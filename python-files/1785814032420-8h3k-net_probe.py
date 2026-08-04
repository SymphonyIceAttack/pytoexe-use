#!/usr/bin/env python3
"""
Network Probe - Advanced Network Diagnostic Tool (Single File Version)
Comprehensive Python-based network analysis tool for Windows.
Performs traceroute, port scanning, firewall detection, and protocol analysis.

Author: Network Architect (20 years experience)
Version: 1.0.1 (Fixed: hop path IP showing * for local servers)
"""

import socket
import struct
import time
import logging
import select
import sys
import os
import re
import csv
import json
import argparse
import subprocess
import threading
import copy
from typing import Optional, Dict, List, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import IntEnum, Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("network_probe.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("net_probe")

try:
    from rich.console import Console
    from rich.table import Table as RichTable
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# ============================================================================
# PROTOCOL TYPES
# ============================================================================

class ProtocolType(IntEnum):
    """Supported protocols"""
    ICMP = 1
    TCP = 6
    UDP = 17
    DNS = 53
    HTTP = 80
    HTTPS = 443


class IcmpType(IntEnum):
    """ICMP Message Types"""
    ECHO_REQUEST = 8
    ECHO_REPLY = 0
    TIME_EXCEEDED = 11
    PARAMETER_PROBLEM = 12
    UNREACHABLE = 3
    SOURCE_QUENCH = 4
    REDIRECT = 5
    TIMESTAMP_REQUEST = 13
    TIMESTAMP_REPLY = 14


class FirewallRuleType(str, Enum):
    """Types of firewall rules/actions"""
    DROP = "drop"
    REJECT = "reject"
    ACCEPT = "accept"
    LOG = "log"


class DnsTraceStatus(Enum):
    """Status indicators for DNS traceroute hops"""
    TIMEOUT = "timeout"
    TIME_EXCEEDED = "time_exceeded"
    UNREACHABLE = "unreachable"
    DNS_RESPONSE = "dns_response"
    BLOCKED = "blocked"
    REACHED_TARGET = "reached_target"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ScanResult:
    """Container for scan result data"""
    host: str
    port: Optional[int] = None
    protocol: ProtocolType = ProtocolType.TCP
    success: bool = False
    timeout: bool = False
    error: Optional[str] = None
    rtt: float = 0.0
    payload: bytes = b""
    timestamps: Dict[str, float] = field(default_factory=lambda: {"send": 0, "receive": 0, "completed": 0})

    def __repr__(self) -> str:
        return f"<ScanResult host={self.host} port={self.port} protocol={self.protocol.name} success={self.success} rtt={self.rtt:.3f}s>"


@dataclass
class HopInfo:
    """Information about each hop in traceroute"""
    hop_number: int
    ip_address: str
    hostname: str = ""
    rtt: float = 0.0
    ttl: int = 0
    icmp_type: int = 0
    icmp_code: int = 0
    country: str = ""
    asn: str = ""
    isp: str = ""
    latency: float = 0.0
    status: str = ""

    def __str__(self) -> str:
        return (f"Hop {self.hop_number}: {self.ip_address} "
                f"({self.hostname}) RTT={self.rtt:.3f}s TTL={self.ttl} "
                f"Type={self.icmp_type} Code={self.icmp_code}")


@dataclass
class DnsHopInfo:
    """Information about each hop in DNS traceroute"""
    hop_number: int
    ip_address: str
    hostname: str
    rtt: float
    ttl: int
    icmp_type: int
    icmp_code: int
    status: DnsTraceStatus
    has_dns_response: bool = False
    dns_response_text: str = ""

    def __str__(self):
        return (f"Hop {self.hop_number}: {self.ip_address} ({self.hostname}) "
                f"RTT={self.rtt:.1f}ms TTL={self.ttl} Status={self.status.value}")


@dataclass
class IcmpMessage:
    """ICMP message structure"""
    type: int
    code: int
    checksum: int
    identifier: int = 0
    sequence_number: int = 0
    data: bytes = b""
    payload_offset: int = 8


@dataclass
class IpInfo:
    """IP address information"""
    ip: str
    country: str = ""
    country_code: str = ""
    city: str = ""
    region: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    asn: str = ""
    as_name: str = ""
    isp: str = ""
    organization: str = ""
    is_private: bool = False
    is_rfc1918: bool = False

    def __str__(self) -> str:
        parts = [f"IP: {self.ip}"]
        if self.country:
            parts.append(f"Country: {self.country}")
        if self.city:
            parts.append(f"City: {self.city}")
        if self.asn:
            parts.append(f"ASN: {self.asn} ({self.as_name})")
        if self.isp:
            parts.append(f"ISP: {self.isp}")
        return ", ".join(parts)


@dataclass
class FirewallFinding:
    """A finding from firewall analysis"""
    hop_number: Optional[int] = None
    protocol: Optional[ProtocolType] = None
    port: Optional[int] = None
    action: Any = None
    confidence: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    rule_type: FirewallRuleType = FirewallRuleType.DROP

    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if not isinstance(self.action, FirewallAction):
            self.action = FirewallAction(self.action, "Unknown", self.confidence)

    def get_summary(self) -> str:
        """Get human-readable summary"""
        parts = []
        if self.hop_number:
            parts.append(f"Hop {self.hop_number}")
        if self.protocol:
            parts.append(f"{self.protocol.name}")
        if self.port:
            parts.append(f"port {self.port}")
        if self.action:
            parts.append(f"{self.action.rule_type.value.upper()}")
        return " ".join(parts) or "Firewall detected"


@dataclass
class ReportContext:
    """Context for report generation"""
    target: str
    protocol: str
    port: Optional[int] = None
    hops: List[HopInfo] = None
    scan_results: List[ScanResult] = None
    findings: List[FirewallFinding] = None
    ip_info: Dict[str, IpInfo] = None
    start_time: float = None
    end_time: float = None

    def __post_init__(self):
        if self.hops is None:
            self.hops = []
        if self.scan_results is None:
            self.scan_results = []
        if self.findings is None:
            self.findings = []
        if self.ip_info is None:
            self.ip_info = {}
        if self.start_time is None:
            self.start_time = datetime.now().timestamp()
        if self.end_time is None:
            self.end_time = datetime.now().timestamp()


# ============================================================================
# FIREWALL ACTION
# ============================================================================

class FirewallAction:
    """Represents a detected firewall action"""
    def __init__(self, rule_type: FirewallRuleType, description: str, confidence: float = 1.0):
        self.rule_type = rule_type
        self.description = description
        self.confidence = confidence

    def __repr__(self) -> str:
        return f"<FirewallAction type={self.rule_type.value} desc={self.description} confidence={self.confidence:.2f}>"


# ============================================================================
# IP INFO PROVIDER
# ============================================================================

class FakeIpInfoProvider:
    """Mock/IP-less provider for testing/demo purposes"""
    def __init__(self):
        self.test_data = {
            "8.8.8.8": IpInfo(
                ip="8.8.8.8", country="United States", country_code="US",
                city="Mountain View", region="California", latitude=37.4056, longitude=-122.0775,
                asn="AS15169", as_name="Google LLC", isp="Google", organization="Google LLC",
                is_private=False, is_rfc1918=False
            ),
            "1.1.1.1": IpInfo(
                ip="1.1.1.1", country="Australia", country_code="AU",
                city="Sydney", region="New South Wales", latitude=-33.8688, longitude=151.2093,
                asn="AS13335", as_name="Cloudflare Inc.", isp="Cloudflare", organization="Cloudflare, Inc.",
                is_private=False, is_rfc1918=False
            ),
            "192.168.1.1": IpInfo(
                ip="192.168.1.1", country="Private", country_code="N/A",
                asn="AS0", as_name="Private Use", isp="Local Network", organization="Private Network",
                is_private=True, is_rfc1918=True
            ),
        }

    def get_info(self, ip: str) -> IpInfo:
        if self._is_private_ip(ip):
            return IpInfo(ip=ip, is_private=True, is_rfc1918=self._is_rfc1918(ip))
        if ip in self.test_data:
            return copy.copy(self.test_data[ip])
        return IpInfo(ip=ip, country="Unknown", country_code="XX", asn="AS0",
                      as_name="Unknown", isp="Unknown", is_private=False, is_rfc1918=self._is_rfc1918(ip))

    def _is_private_ip(self, ip: str) -> bool:
        try:
            import ipaddress
            ip_addr = ipaddress.ip_address(ip)
            return ip_addr.is_private or ip_addr.is_reserved or ip_addr.is_loopback
        except Exception:
            return False

    def _is_rfc1918(self, ip: str) -> bool:
        try:
            import ipaddress
            ip_addr = ipaddress.ip_address(ip)
            return ip_addr in ipaddress.IPv4Address('10.0.0.0/8') or \
                   ip_addr in ipaddress.IPv4Address('172.16.0.0/12') or \
                   ip_addr in ipaddress.IPv4Address('192.168.0.0/16')
        except Exception:
            return False


def get_ip_info(ip: str) -> IpInfo:
    """Get IP information for an address"""
    return FakeIpInfoProvider().get_info(ip)


# ============================================================================
# ICMP ANALYZER
# ============================================================================

class IcmpAnalyzer:
    """ICMP message analyzer and validator"""

    @staticmethod
    def parse_icmp(data: bytes) -> Optional[IcmpMessage]:
        """Parse ICMP message from raw bytes"""
        if len(data) < 8:
            return None
        try:
            type_code = struct.unpack('>BB', data[:2])
            checksum = struct.unpack('>H', data[2:4])[0]
            identifier = struct.unpack_from('>H', data[4:6])[0]
            sequence_number = struct.unpack_from('>H', data[6:8])[0]
            return IcmpMessage(
                type=type_code[0], code=type_code[1], checksum=checksum,
                identifier=identifier, sequence_number=sequence_number, data=data[8:]
            )
        except Exception as e:
            logger.error(f"ICMP parse error: {e}")
            return None


# ============================================================================
# DNS PROTOCOL MODULE
# ============================================================================

class DnsQueryType(IntEnum):
    """DNS query types according to RFC 1035"""
    A = 1
    NS = 2
    CNAME = 5
    SOA = 6
    PTR = 12
    MX = 15
    AAAA = 28
    TXT = 16
    ANY = 255


class DnsClass(IntEnum):
    """DNS classes"""
    IN = 1


class DnsRecord:
    """DNS record structure"""
    def __init__(self, name, type_, cls, ttl, rdata, parsed_data=None):
        self.name = name
        self.type = type_
        self.cls = cls
        self.ttl = ttl
        self.rdata = rdata
        self.parsed_data = parsed_data or {}

    def __repr__(self):
        return f"<DnsRecord name={self.name} type={self.type.value} ttl={self.ttl}>"


class DnsResponse:
    """Parsed DNS response"""
    def __init__(self, transaction_id, flags, questions, answer, authority, additional, rcode=0):
        self.transaction_id = transaction_id
        self.flags = flags
        self.question = questions
        self.answer = answer
        self.authority = authority
        self.additional = additional
        self.rcode = rcode

    def has_answers(self) -> bool:
        return len(self.answer) > 0

    def get_a_records(self) -> List[str]:
        return [rec.parsed_data.get('ip') for rec in self.answer if rec.type == DnsQueryType.A and 'ip' in rec.parsed_data]


class DnsParser:
    """DNS packet parser and analyzer"""

    @staticmethod
    def parse(response_bytes: bytes) -> Optional[DnsResponse]:
        """Parse raw DNS response bytes into structured data"""
        if len(response_bytes) < 12:
            return None
        try:
            tx_id, flags, qdcount, ancount, nscount, arcount = struct.unpack('>HHHHHH', response_bytes[:12])
            flags_dict = {
                "qr": (flags >> 15) & 1, "opcode": (flags >> 11) & 0xF,
                "aa": (flags >> 10) & 1, "tc": (flags >> 9) & 1,
                "rd": (flags >> 8) & 1, "ra": (flags >> 7) & 1,
                "rcode": flags & 0xF
            }
            rcode = flags_dict["rcode"]
            questions = DnsParser._parse_questions(response_bytes[12:])
            answer_start = 12 + DnsParser._count_qdomains(response_bytes[12:])
            answers, next_pos = DnsParser._parse_records(response_bytes, answer_start, ancount)
            authority, next_pos = DnsParser._parse_records(response_bytes, next_pos, nscount)
            additional, _ = DnsParser._parse_records(response_bytes, next_pos, arcount)
            return DnsResponse(tx_id, flags_dict, questions, answers, authority, additional, rcode)
        except Exception as e:
            logger.error(f"DNS parse error: {e}")
            return None

    @staticmethod
    def _parse_questions(data: bytes) -> List[Dict]:
        questions = []
        pos = 0
        while pos < len(data):
            qname, pos = DnsParser._read_name(data, pos)
            if pos + 4 > len(data):
                break
            qtype, cls = struct.unpack_from('>HH', data[pos:pos + 4])
            pos += 4
            questions.append({"name": qname, "type": qtype, "cls": cls})
        return questions

    @staticmethod
    def _read_name(data: bytes, pos: int) -> Tuple[str, int]:
        name_parts = []
        while pos < len(data):
            length = data[pos]
            if length == 0:
                pos += 1
                break
            if length >= 0xC0:
                pos += 2
                break
            name_parts.append(data[pos + 1:pos + 1 + length].decode('ascii', errors='ignore'))
            pos += 1 + length
        return ".".join(name_parts) if name_parts else "", pos

    @staticmethod
    def _count_qdomains(data: bytes) -> int:
        pos = 0
        while pos < len(data):
            length = data[pos]
            if length == 0 or length >= 0xC0:
                return 1
            pos += 1 + length
        return 0

    @staticmethod
    def _parse_records(data: bytes, start_pos: int, count: int) -> Tuple[List[DnsRecord], int]:
        records = []
        pos = start_pos
        for _ in range(count):
            if pos >= len(data):
                break
            qname, pos = DnsParser._read_name(data, pos)
            if pos + 10 > len(data):
                break
            rtype, rclass, rttl, rdlength = struct.unpack_from('>HHHI', data[pos:pos + 10])
            pos += 10
            if pos + rdlength > len(data):
                break
            rdata = data[pos:pos + rdlength]
            pos += rdlength
            parsed_data = DnsParser._parse_rdata(rtype, rdata, rclass)
            record = DnsRecord(qname, DnsQueryType(rtype) if rtype <= 255 else rtype,
                               DnsClass(rclass), rttl, rdata, parsed_data)
            records.append(record)
        return records, pos

    @staticmethod
    def _parse_rdata(rtype: int, rdata: bytes, rclass: int) -> Dict:
        parsed = {}
        if rtype == 1 and len(rdata) == 4:
            parsed['ip'] = socket.in_ntoa(rdata)
        elif rtype == 15 and len(rdata) >= 2:
            preference = struct.unpack_from('>H', rdata[:2])[0]
            exchange, _ = DnsParser._read_name(rdata, 2)
            parsed['preference'] = preference
            parsed['exchange'] = exchange
        elif rtype == 5:
            cname, _ = DnsParser._read_name(rdata, 0)
            parsed['target'] = cname
        elif rtype == 12:
            ptr_name, _ = DnsParser._read_name(rdata, 0)
            parsed['target'] = ptr_name
        elif rtype == 16:
            parsed['text'] = rdata.decode('ascii', errors='ignore')
        return parsed


class DnsScanner:
    """DNS query scanner with analysis"""

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout

    def query(self, domain: str, server: str = "8.8.8.8", qtype: int = 1) -> Optional[DnsResponse]:
        """Send DNS query and parse response"""
        try:
            query = DnsQuery.from_query(domain, qtype=qtype)
            query_bytes = query.to_bytes()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            sock.sendto(query_bytes, (server, 53))
            response_bytes, _ = sock.recvfrom(512)
            sock.close()
            return DnsParser.parse(response_bytes)
        except socket.timeout:
            logger.debug(f"DNS query timed out to {server}")
            return None
        except Exception as e:
            logger.error(f"DNS query error: {e}")
            return None

    def check_dns_resolution(self, domain: str) -> bool:
        """Check if DNS can resolve the domain"""
        try:
            socket.gethostbyname(domain)
            return True
        except socket.gaierror:
            return False


class DnsQuery:
    """DNS query packet"""
    def __init__(self, transaction_id=0, questions=None, qr=False, opcode=0,
                 aa=False, tc=False, rd=True, ra=False, rcode=0, ancount=0, nscount=0, arcount=0):
        self.transaction_id = transaction_id
        self.questions = questions or []
        self.rd = rd

    def to_bytes(self) -> bytes:
        flags = (1 << 8) if self.rd else 0
        header = struct.pack('>HHHHHH', self.transaction_id, flags,
                             len(self.questions), 0, 0, 0)
        questions_bytes = b""
        for q in self.questions:
            questions_bytes += self._name_to_bytes(q['name'])
            questions_bytes += struct.pack('>HH', q['type'], q.get('cls', 1))
        return header + questions_bytes

    def _name_to_bytes(self, name: str) -> bytes:
        parts = name.split('.')
        result = b""
        for part in parts:
            result += struct.pack('B', len(part)) + part.encode('ascii')
        result += b'\x00'
        return result

    @classmethod
    def from_query(cls, domain: str, qtype: int = 1, qclass: int = 1) -> 'DnsQuery':
        return cls(transaction_id=0x1234, questions=[{"name": domain, "type": qtype, "cls": qclass}])


def dns_query(domain: str, server: str = "8.8.8.8", qtype: int = 1) -> Optional[DnsResponse]:
    """Quick DNS query"""
    scanner = DnsScanner()
    return scanner.query(domain, server, qtype=qtype)


# ============================================================================
# DNS TRACEROUTE MODULE
# ============================================================================

def _build_dns_query(domain: str = "example.com", transaction_id: int = 0x1234) -> bytes:
    """Build a standard DNS A-query packet (RFC 1035)."""
    header = struct.pack('>HHHHHH', transaction_id, 0x0100, 1, 0, 0, 0)
    domain_bytes = b""
    for label in domain.split("."):
        domain_bytes += struct.pack('B', len(label)) + label.encode('ascii')
    domain_bytes += b'\x00'
    question = domain_bytes + struct.pack('>HH', 1, 1)
    return header + question


def _parse_icmp_error(packet: bytes, sent_at: float) -> Tuple[Optional[str], int, int, float]:
    """Parse an ICMP error packet (Time Exceeded / Destination Unreachable)."""
    if len(packet) < 28:
        return None, 0, 0, 0
    ip_version = (packet[0] >> 4) & 0xF
    if ip_version != 4:
        return None, 0, 0, 0
    ip_header_len = (packet[0] & 0xF) * 4
    if len(packet) < ip_header_len + 8:
        return None, 0, 0, 0
    icmp_offset = ip_header_len
    icmp_type = packet[icmp_offset]
    icmp_code = packet[icmp_offset + 1]
    rtt = (time.time() - sent_at) * 1000
    if icmp_offset + 8 + 20 <= len(packet):
        inner_ip = socket.inet_ntoa(packet[icmp_offset + 8 + 16: icmp_offset + 8 + 20])
        return inner_ip, icmp_type, icmp_code, rtt
    return None, icmp_type, icmp_code, rtt


def _reverse_dns(ip: str) -> str:
    """Reverse DNS lookup with timeout."""
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except (socket.herror, socket.gaierror, OSError):
        return ""


def _icmp_proto() -> int:
    """Get ICMP protocol number cross-platform."""
    return getattr(socket, "ICMP", socket.getprotobyname("icmp"))


class DnsTraceroute:
    """
    Trace the path of a DNS query by sending UDP packets with DNS payloads
    to the target DNS server, incrementing TTL each hop.
    """

    def __init__(self, max_ttl: int = 30, timeout: float = 2.0, retries: int = 2):
        self.max_ttl = max_ttl
        self.timeout = timeout
        self.retries = retries
        self.hops: List[DnsHopInfo] = []

    def trace(self, dns_server: str, domain: str = "example.com") -> List[DnsHopInfo]:
        """Perform DNS traceroute to the specified DNS server."""
        logger.info(f"Starting DNS traceroute to {dns_server} (domain={domain})")
        self.hops = []
        dns_query = _build_dns_query(domain)
        logger.info(f"DNS query payload size: {len(dns_query)} bytes")

        for ttl in range(1, self.max_ttl + 1):
            hop_found = False
            hop_info = None
            for attempt in range(self.retries):
                hop_info = self._probe_ttl(ttl, dns_server, dns_query)
                if hop_info:
                    self.hops.append(hop_info)
                    hop_found = True
                    logger.debug(f"TTL {ttl}: {hop_info}")
                    break
                logger.warning(f"TTL {ttl}, attempt {attempt + 1}/{self.retries} timed out")

            if not hop_found:
                timeout_hop = DnsHopInfo(
                    hop_number=ttl, ip_address=target_ip, hostname=_reverse_dns(target_ip),
                    rtt=self.timeout * 1000, ttl=ttl,
                    icmp_type=0, icmp_code=0, status=DnsTraceStatus.TIMEOUT
                )
                self.hops.append(timeout_hop)
                logger.info(f"Stopping at TTL {ttl} - no response after {self.retries} attempts")
                break

            if hop_info and hop_info.status == DnsTraceStatus.REACHED_TARGET:
                logger.info(f"DNS response received at hop {ttl} from {dns_server}")
                break

        logger.info(f"DNS traceroute complete: {len(self.hops)} hops found")
        return self.hops

    def _probe_ttl(self, ttl: int, target_ip: str, dns_query: bytes) -> Optional[DnsHopInfo]:
        """Send a DNS query packet with specific TTL and collect response."""
        recv_sock = None
        send_sock = None
        try:
            recv_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, _icmp_proto())
            recv_sock.settimeout(self.timeout)
            send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
            send_sock.settimeout(self.timeout)
            send_sock.bind(("0.0.0.0", 0))

            sent_at = time.time()
            send_sock.sendto(dns_query, (target_ip, 53))
            deadline = sent_at + self.timeout

            while True:
                remaining = deadline - time.time()
                if remaining <= 0:
                    raise socket.timeout()
                readable, _, _ = select.select([recv_sock, send_sock], [], [], remaining)
                if not readable:
                    raise socket.timeout()

                if send_sock in readable:
                    data, addr = send_sock.recvfrom(512)
                    if addr[0] == target_ip:
                        rtt = (time.time() - sent_at) * 1000
                        dns_text = self._parse_dns_response_summary(data)
                        hostname = _reverse_dns(addr[0])
                        return DnsHopInfo(
                            hop_number=ttl, ip_address=addr[0], hostname=hostname,
                            rtt=rtt, ttl=ttl, icmp_type=0, icmp_code=0,
                            status=DnsTraceStatus.DNS_RESPONSE,
                            has_dns_response=True, dns_response_text=dns_text
                        )

                if recv_sock in readable:
                    resp_packet, _ = recv_sock.recvfrom(65535)
                    inner_ip, icmp_type, icmp_code, rtt = _parse_icmp_error(resp_packet, sent_at)
                    if inner_ip == target_ip:
                        hostname = _reverse_dns(inner_ip) if inner_ip else ""
                        if icmp_type == 11 and icmp_code == 0:
                            status = DnsTraceStatus.TIME_EXCEEDED
                        elif icmp_type == 3 and icmp_code == 0:
                            status = DnsTraceStatus.UNREACHABLE
                        elif icmp_type == 3 and icmp_code == 13:
                            status = DnsTraceStatus.BLOCKED
                        else:
                            status = DnsTraceStatus.TIME_EXCEEDED
                        return DnsHopInfo(
                            hop_number=ttl, ip_address=inner_ip or "*",
                            hostname=hostname, rtt=rtt, ttl=ttl,
                            icmp_type=icmp_type, icmp_code=icmp_code, status=status
                        )

        except socket.timeout:
            logger.debug(f"TTL {ttl} timed out")
            return None
        except PermissionError as e:
            logger.error(f"Permission denied - raw socket requires admin: {e}")
            return None
        except Exception as e:
            logger.error(f"Error probing TTL {ttl}: {e}")
            return None
        finally:
            if recv_sock:
                recv_sock.close()
            if send_sock:
                send_sock.close()
        return None

    def _parse_dns_response_summary(self, data: bytes) -> str:
        """Parse DNS response and return a human-readable summary."""
        try:
            if len(data) < 12:
                return f"Short DNS response ({len(data)} bytes)"
            tx_id, flags, qdcount, ancount, nscount, arcount = struct.unpack('>HHHHHH', data[:12])
            rcode = flags & 0xF
            qr = (flags >> 15) & 1
            if qr == 0:
                return "Query (no response)"
            rcodes = {0: "NOERROR", 1: "FORMERR", 2: "SERVFAIL", 3: "NXDOMAIN",
                      4: "NOTIMP", 5: "REFUSED"}
            rcode_str = rcodes.get(rcode, f"RCODE_{rcode}")
            answers = []
            pos = 12
            for _ in range(qdcount):
                while pos < len(data):
                    length = data[pos]
                    if length == 0:
                        pos += 1
                        break
                    if length >= 0xC0:
                        pos += 2
                        break
                    pos += 1 + length
                pos += 4
            for _ in range(ancount):
                if pos >= len(data):
                    break
                while pos < len(data):
                    length = data[pos]
                    if length == 0:
                        pos += 1
                        break
                    if length >= 0xC0:
                        pos += 2
                        break
                    pos += 1 + length
                if pos + 10 > len(data):
                    break
                rtype, rclass, rttl, rdlength = struct.unpack_from('>HHHI', data, pos)
                pos += 10
                if rtype == 1 and rdlength == 4 and pos + rdlength <= len(data):
                    ip = socket.inet_ntoa(data[pos:pos + 4])
                    answers.append(ip)
                pos += rdlength
            summary = f"{rcode_str}"
            if answers:
                summary += f" A={','.join(answers[:3])}"
            return summary
        except Exception as e:
            return f"Parse error: {e}"


def quick_dns_trace(dns_server: str, domain: str = "example.com",
                    max_ttl: int = 30, timeout: float = 2.0) -> List[DnsHopInfo]:
    """Quick DNS traceroute convenience function."""
    tracer = DnsTraceroute(max_ttl=max_ttl, timeout=timeout)
    return tracer.trace(dns_server, domain)


# ============================================================================
# NETWORK SCANNER MODULE
# ============================================================================

class TraceRouteScanner:
    """Traceroute implementation using TTL scanning"""

    def __init__(self, max_ttl: int = 30, timeout: float = 2.0, retries: int = 3):
        self.max_ttl = max_ttl
        self.timeout = timeout
        self.retries = retries
        self.hops: List[HopInfo] = []
        self.lock = threading.Lock()
        self._raw_socket_warning_shown = False

    def _should_show_raw_socket_warning(self) -> bool:
        if not self._raw_socket_warning_shown:
            self._raw_socket_warning_shown = True
            return True
        return False

    @staticmethod
    def _icmp_proto() -> int:
        return getattr(socket, "ICMP", socket.getprotobyname("icmp"))

    def trace(self, target: str, use_icmp: bool = True,
              protocol: ProtocolType = ProtocolType.ICMP,
              port: Optional[int] = None,
              payload: bytes = b"") -> List[HopInfo]:
        """Perform traceroute to target."""
        logger.info(f"Starting traceroute to {target} (protocol={protocol.name}, max TTL: {self.max_ttl})")
        try:
            target_ip = socket.gethostbyname(target)
        except socket.gaierror as e:
            logger.error(f"Unable to resolve target: {e}")
            return []

        self.hops = []
        if use_icmp or protocol in (ProtocolType.UDP, ProtocolType.DNS):
            try:
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, self._icmp_proto())
                test_sock.close()
                logger.info("Using raw socket traceroute")
            except (OSError, AttributeError):
                logger.warning("Raw socket ICMP not available, falling back to system tracert")
                return self._trace_via_system_command(target)

        for ttl in range(1, self.max_ttl + 1):
            hop_found = False
            hop_info = None
            for attempt in range(self.retries):
                hop_info = self._probe_ttl(ttl, target_ip, use_icmp, protocol=protocol, port=port, payload=payload)
                if hop_info:
                    with self.lock:
                        self.hops.append(hop_info)
                        hop_found = True
                    logger.debug(f"TTL {ttl}: {hop_info}")
                    break
                logger.warning(f"TTL {ttl}, attempt {attempt + 1}/{self.retries} timed out")

            if not hop_found:
                remaining_hops = self.max_ttl - ttl + 1
                logger.info(f"Stopping at TTL {ttl} - {remaining_hops} hops remaining")
                break

            if hop_info is not None and self._is_terminal_hop(hop_info, target_ip):
                logger.info("Stopping traceroute at hop %s (%s)", hop_info.hop_number, hop_info.status)
                break

        logger.info(f"Traceroute complete: {len(self.hops)} hops found")
        return self.hops

    def _trace_via_system_command(self, target: str) -> List[HopInfo]:
        """Use system tracert command for accurate results (Windows fallback)"""
        logger.info("Using system command to trace route")
        hops = []
        try:
            result = subprocess.run(
                ['tracert', '-d', '-h', str(self.max_ttl), '-w', str(max(int(self.timeout * 1000), 250)), target],
                capture_output=True, text=True,
                timeout=max(self.max_ttl * self.timeout * 4 + 10, 20)
            )
            if result.returncode != 0:
                logger.warning(f"Tracert command failed: {result.stderr}")
                return []
            lines = result.stdout.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('Trac') or line.startswith('Route') or line.startswith('tracking'):
                    continue
                if 'Average' in line or 'Trung bình' in line or 'stat' in line.lower():
                    continue
                # Skip lines that are pure timeout indicators (e.g. "* * *")
                if re.match(r'^\s*\*+\s*$', line):
                    continue
                # Match Windows tracert format: "N   x.xxx ms  x.xxx ms  x.xxx ms  IP"
                # or timeout format: "N   * * *" (already filtered above)
                match = re.search(r'^\s*(\d+)\s+(.*?)(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*$', line)
                if match:
                    hop_number = int(match.group(1))
                    rtt_str = match.group(2).strip()
                    ip = match.group(3)
                    # Skip if IP is actually a wildcard/timeout marker
                    if ip == '*':
                        continue
                    rtt_values = []
                    for rtt in rtt_str.split():
                        rtt_clean = rtt.replace('ms', '').strip().lstrip('<').lstrip('-')
                        if rtt_clean and rtt_clean.replace('.', '', 1).isdigit():
                            rtt_values.append(float(rtt_clean))
                        elif rtt.startswith('<') and rtt.lstrip('<').replace('.', '', 1).isdigit():
                            rtt_values.append(0.1)
                    avg_rtt = sum(rtt_values) / len(rtt_values) if rtt_values else 0.0
                    hostname = ""
                    if ip and ip != '*' and not ip.startswith('<') and ip != '<>':
                        try:
                            hostname, _, _ = socket.gethostbyaddr(ip)
                        except Exception:
                            hostname = ""
                    status = "timeout" if ip == '*' else "traceroute"
                    hop_info = HopInfo(
                        hop_number=hop_number, ip_address=ip, hostname=hostname,
                        rtt=avg_rtt, ttl=hop_number, icmp_type=0, icmp_code=0, status=status
                    )
                    hops.append(hop_info)
        except subprocess.TimeoutExpired:
            logger.error("Tracert command timed out")
        except Exception as e:
            logger.error(f"Error parsing tracert output: {e}")
        return hops

    def _probe_ttl(self, ttl: int, target_ip: str, use_icmp: bool,
                   protocol: ProtocolType = ProtocolType.ICMP,
                   port: Optional[int] = None,
                   payload: bytes = b"") -> Optional[HopInfo]:
        """Send packet with specific TTL and receive response"""
        sock = None
        try:
            if protocol in (ProtocolType.UDP, ProtocolType.DNS):
                return self._udp_trace_probe(ttl, target_ip, port, payload)
            if use_icmp:
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, self._icmp_proto())
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
                sock.bind(("0.0.0.0", 0))
                sock.settimeout(self.timeout)
                sent_at = time.time()
                req_packet = self._create_icmpecho_request()
                sock.sendto(req_packet, (target_ip, 0))
                resp_packet, addr = sock.recvfrom(65535)
                recv_ip, recv_port = addr
                parse_result = self._parse_icmpecho_response(resp_packet, recv_ip, recv_port, sent_at)
                if parse_result:
                    ip, rtt, hop_type, hop_code, _ = parse_result
                    hostname = self._reverse_dns(ip)
                    return HopInfo(
                        hop_number=ttl, ip_address=ip, hostname=hostname,
                        rtt=rtt, ttl=ttl, icmp_type=hop_type, icmp_code=hop_code,
                        status=self._status_from_icmp(ip, target_ip, hop_type, hop_code)
                    )
                else:
                    return HopInfo(
                        hop_number=ttl, ip_address=recv_ip,
                        hostname=self._reverse_dns(recv_ip),
                        rtt=(time.time() - sent_at) * 1000, ttl=ttl,
                        icmp_type=0, icmp_code=0,
                        status="destination" if recv_ip == target_ip else "traceroute"
                    )
            else:
                return self._tcp_trace_probe(ttl, target_ip)
        except socket.timeout:
            return HopInfo(hop_number=ttl, ip_address=target_ip, hostname=_reverse_dns(target_ip),
                          rtt=self.timeout * 1000, ttl=ttl, icmp_type=0, icmp_code=0, status="timeout")
        except (PermissionError, OSError, AttributeError) as e:
            if self._should_show_raw_socket_warning():
                logger.warning(f"Raw socket not available (ICMP mode requires admin): {e}")
            return None
        except Exception as e:
            logger.error(f"Error probing TTL {ttl}: {e}")
            return None
        finally:
            if sock is not None:
                sock.close()

    def _udp_trace_probe(self, ttl: int, target_ip: str,
                          port: Optional[int],
                          payload: bytes = b"") -> Optional[HopInfo]:
        """Traceroute using UDP or DNS payloads and ICMP feedback."""
        recv_sock = None
        send_sock = None
        target_port = port or 33434
        try:
            recv_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, self._icmp_proto())
            recv_sock.settimeout(self.timeout)
            send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
            send_sock.settimeout(self.timeout)
            send_sock.bind(("0.0.0.0", 0))
            sent_at = time.time()
            send_sock.sendto(payload or b"", (target_ip, target_port))
            deadline = sent_at + self.timeout
            while True:
                remaining = deadline - time.time()
                if remaining <= 0:
                    raise socket.timeout()
                readable, _, _ = select.select([recv_sock, send_sock], [], [], remaining)
                if not readable:
                    raise socket.timeout()
                if send_sock in readable:
                    data, addr = send_sock.recvfrom(4096)
                    if addr[0] != target_ip:
                        continue
                    return HopInfo(
                        hop_number=ttl, ip_address=addr[0],
                        hostname=self._reverse_dns(addr[0]),
                        rtt=(time.time() - sent_at) * 1000, ttl=ttl,
                        icmp_type=0, icmp_code=0, status="destination"
                    )
                if recv_sock in readable:
                    resp_packet, addr = recv_sock.recvfrom(65535)
                    recv_ip = addr[0]
                    if not self._icmp_matches_udp_probe(resp_packet, target_ip, target_port):
                        continue
                    parse_result = self._parse_icmpecho_response(resp_packet, recv_ip, 0, sent_at)
                    if not parse_result:
                        return HopInfo(
                            hop_number=ttl, ip_address=recv_ip,
                            hostname=self._reverse_dns(recv_ip),
                            rtt=(time.time() - sent_at) * 1000, ttl=ttl,
                            icmp_type=0, icmp_code=0,
                            status="destination" if recv_ip == target_ip else "traceroute"
                        )
                    ip, rtt, hop_type, hop_code, _ = parse_result
                    return HopInfo(
                        hop_number=ttl, ip_address=ip,
                        hostname=self._reverse_dns(ip), rtt=rtt, ttl=ttl,
                        icmp_type=hop_type, icmp_code=hop_code,
                        status=self._status_from_icmp(ip, target_ip, hop_type, hop_code)
                    )
        finally:
            if recv_sock is not None:
                recv_sock.close()
            if send_sock is not None:
                send_sock.close()
        return None

    def _create_icmpecho_request(self) -> bytes:
        """Create ICMP Echo Request packet"""
        header = bytes([8, 0, 0, 0, 0, 0]) + struct.pack('>HH', 12345, 1)
        padding = b"A" * (64 - len(header))
        checksum = self._icmp_checksum(header + padding)
        header = bytearray(header)
        header[2] = checksum >> 8
        header[3] = checksum & 0xFF
        return bytes(header) + padding

    def _icmp_checksum(self, data: bytes) -> int:
        """Calculate ICMP checksum"""
        checksum = 0
        for i in range(0, len(data), 2):
            word = struct.unpack_from('>H', data[i:i + 2] + (b'\x00' if i + 1 >= len(data) else b''))[0]
            checksum += word
            checksum = (checksum & 0xFFFF) + (checksum >> 16)
        return ~checksum & 0xFFFF

    def _parse_icmpecho_response(self, packet: bytes, recv_ip: str,
                                  recv_port: int = 0,
                                  sent_at: Optional[float] = None) -> Optional[Tuple[str, float, int, int, float]]:
        """Parse received ICMP response."""
        if len(packet) < 28:
            return None
        ip_version = (packet[0] >> 4) & 0xF
        if ip_version != 4:
            return None
        ip_header_len = (packet[0] & 0xF) * 4
        if len(packet) < ip_header_len + 8:
            return None
        icmp_offset = ip_header_len
        icmp_type = packet[icmp_offset]
        icmp_code = packet[icmp_offset + 1]
        rtt = ((time.time() - sent_at) * 1000) if sent_at else 0.0
        if icmp_type == 11 and icmp_code == 0:
            return recv_ip, rtt, icmp_type, icmp_code, rtt
        elif icmp_type == 0 and icmp_code == 0:
            return recv_ip, rtt, icmp_type, icmp_code, rtt
        elif icmp_type == 3 and icmp_code in {0, 1, 3, 13}:
            return recv_ip, rtt, icmp_type, icmp_code, rtt
        return None

    def _is_destination(self, hop_info: HopInfo, target_ip: str) -> bool:
        return hop_info.ip_address == target_ip or hop_info.status == "destination"

    def _is_terminal_hop(self, hop_info: HopInfo, target_ip: str) -> bool:
        if self._is_destination(hop_info, target_ip):
            return True
        return hop_info.icmp_type == 3 and hop_info.icmp_code in {0, 1, 3, 13}

    def _status_from_icmp(self, hop_ip: str, target_ip: str, icmp_type: int, icmp_code: int) -> str:
        if icmp_type == 11 and icmp_code == 0:
            return "traceroute"
        if icmp_type == 0 and icmp_code == 0:
            return "destination"
        if icmp_type == 3 and icmp_code == 13:
            return "blocked"
        if icmp_type == 3 and icmp_code in {0, 1, 3}:
            return "destination" if hop_ip == target_ip and icmp_code == 3 else "unreachable"
        return "alive"

    def _icmp_matches_udp_probe(self, packet: bytes, target_ip: str, target_port: int) -> bool:
        """Verify that an ICMP error quotes the UDP probe we just sent."""
        try:
            if len(packet) < 56:
                return False
            outer_ip_header_len = (packet[0] & 0x0F) * 4
            inner_ip_offset = outer_ip_header_len + 8
            if len(packet) < inner_ip_offset + 20:
                return False
            inner_protocol = packet[inner_ip_offset + 9]
            inner_dest_ip = socket.inet_ntoa(packet[inner_ip_offset + 16:inner_ip_offset + 20])
            inner_ip_header_len = (packet[inner_ip_offset] & 0x0F) * 4
            udp_offset = inner_ip_offset + inner_ip_header_len
            if len(packet) < udp_offset + 4:
                return False
            _, dest_port = struct.unpack('>HH', packet[udp_offset:udp_offset + 4])
            return (
                inner_protocol == socket.IPPROTO_UDP and
                inner_dest_ip == target_ip and
                dest_port == target_port
            )
        except (OSError, struct.error, ValueError):
            return False

    def _tcp_trace_probe(self, ttl: int, target_ip: str) -> Optional[HopInfo]:
        return None

    def _reverse_dns(self, ip: str) -> str:
        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname
        except (socket.herror, socket.gaierror, OSError):
            return ""


class TcpPortScanner:
    """TCP port scanner with SYN scan capability"""
    def __init__(self, timeout: float = 2.0, max_retries: int = 2):
        self.timeout = timeout
        self.max_retries = max_retries

    def scan_syn(self, host: str, port: int) -> ScanResult:
        result = ScanResult(host=host, port=port, protocol=ProtocolType.TCP)
        for attempt in range(self.max_retries + 1):
            result.timestamps["send"] = time.time()
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.connect((host, port))
                sock.setblocking(True)
                sock.settimeout(0.1)
                try:
                    data = sock.recv(1024)
                    if data:
                        result.error = "Port open but received unexpected data"
                except socket.timeout:
                    pass
                result.success = True
                result.rtt = (time.time() - result.timestamps["send"]) * 1000
                result.timestamps["receive"] = time.time()
                sock.close()
                return result
            except ConnectionRefusedError:
                result.error = "Connection refused (port closed)"
                result.rtt = (time.time() - result.timestamps["send"]) * 1000
                result.timestamps["receive"] = time.time()
                break
            except TimeoutError:
                result.timeout = True
                result.error = "Timeout - possibly firewall dropped packet"
                result.rtt = self.timeout * 1000
                result.timestamps["receive"] = time.time()
            except OSError as e:
                result.error = f"OS Error: {e}"
                result.rtt = (time.time() - result.timestamps["send"]) * 1000
                result.timestamps["receive"] = time.time()
            finally:
                if 'sock' in locals():
                    sock.close()
            if attempt < self.max_retries:
                time.sleep(0.1 * (attempt + 1))
        return result


class UdpPortScanner:
    """UDP port scanner"""
    def __init__(self, timeout: float = 2.0, max_retries: int = 2):
        self.timeout = timeout
        self.max_retries = max_retries

    def scan(self, host: str, port: int, payload: bytes = b"") -> ScanResult:
        result = ScanResult(host=host, port=port, protocol=ProtocolType.UDP)
        result.payload = payload
        for attempt in range(self.max_retries + 1):
            result.timestamps["send"] = time.time()
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(self.timeout)
                if payload:
                    sock.sendto(payload, (host, port))
                else:
                    sock.sendto(b"", (host, port))
                try:
                    data, _ = sock.recvfrom(1024)
                    result.success = True
                    result.rtt = (time.time() - result.timestamps["send"]) * 1000
                    result.timestamps["receive"] = time.time()
                    result.payload = data
                except socket.timeout:
                    result.timeout = True
                    if port == 53:
                        result.error = "No response - Port 53 requires valid DNS query. Use quick_dns_query() instead."
                    else:
                        result.error = "No response - possible firewall drop or closed port"
                    result.rtt = self.timeout * 1000
                    result.timestamps["receive"] = time.time()
                sock.close()
                return result
            except Exception as e:
                result.error = str(e)
                result.rtt = (time.time() - result.timestamps["send"]) * 1000
                result.timestamps["receive"] = time.time()
                sock.close()
            if attempt < self.max_retries:
                time.sleep(0.1 * (attempt + 1))
        return result


class DnsPortScanner:
    """DNS query scanner"""
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout

    @staticmethod
    def _build_query(domain: str, qtype: int = 1) -> bytes:
        """Build DNS query packet according to RFC 1035"""
        header = struct.pack('>HHHHHH', 0x0100, 0x0100, 1, 0, 0, 0)
        domain_bytes = b""
        for label in domain.split("."):
            domain_bytes += struct.pack('B', len(label)) + label.encode('ascii')
        domain_bytes += b'\x00'
        question = domain_bytes + struct.pack('>HH', qtype, 1)
        return header + question

    def query(self, domain: str, server: str = "8.8.8.8", qtype: int = 1) -> ScanResult:
        """Send DNS query to specified server"""
        result = ScanResult(host=server, port=53, protocol=ProtocolType.DNS)
        query_payload = self._build_query(domain, qtype)
        result.timestamps["send"] = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            sock.sendto(query_payload, (server, 53))
            try:
                data, _ = sock.recvfrom(512)
                result.success = True
                result.rtt = (time.time() - result.timestamps["send"]) * 1000
                result.timestamps["receive"] = time.time()
                result.payload = data
            except socket.timeout:
                result.timeout = True
                result.error = "DNS query timeout - possible firewall blocking"
                result.rtt = self.timeout * 1000
                result.timestamps["receive"] = time.time()
            sock.close()
        except Exception as e:
            result.error = str(e)
            result.rtt = (time.time() - result.timestamps["send"]) * 1000
            result.timestamps["receive"] = time.time()
        return result

    def check_dns_resolution(self, domain: str) -> bool:
        try:
            socket.gethostbyname(domain)
            return True
        except socket.gaierror:
            return False


class ParallelScanner:
    """Parallel scanner using thread pool"""
    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.lock = threading.Lock()


# ============================================================================
# FIREWALL ANALYSIS MODULE
# ============================================================================

class FirewallRuleEngine:
    """AI-powered rule engine for firewall detection"""

    def __init__(self):
        self.rules = self._load_default_rules()

    def _load_default_rules(self) -> List[Dict]:
        return [
            {"condition": "icmp_type == 3 and icmp_code == 0", "action": FirewallRuleType.DROP,
             "description": "Network Unreachable - Firewall or router blocking network", "confidence": 0.95},
            {"condition": "icmp_type == 3 and icmp_code == 1", "action": FirewallRuleType.DROP,
             "description": "Host Unreachable - Host not found or blocked", "confidence": 0.90},
            {"condition": "icmp_type == 3 and icmp_code == 3", "action": FirewallRuleType.REJECT,
             "description": "Port Closed - Port closed on target host", "confidence": 0.85},
            {"condition": "icmp_type == 3 and icmp_code == 13", "action": FirewallRuleType.DROP,
             "description": "Administratively Prohibited - Firewall ACL blocking", "confidence": 0.98},
            {"condition": "icmp_type == 11 and icmp_code == 0", "action": FirewallRuleType.ACCEPT,
             "description": "TTL Expired - Normal traceroute response", "confidence": 0.99},
            {"condition": "tcp_syn_timeout and no_icmp", "action": FirewallRuleType.DROP,
             "description": "Silent TCP drop - Likely firewall ACL", "confidence": 0.90},
            {"condition": "udp_timeout and icmp_response", "action": FirewallRuleType.DROP,
             "description": "UDP blocked but ICMP allowed - Selective firewall", "confidence": 0.87},
        ]

    def analyze_hop(self, hop: HopInfo, previous_hop: Optional[HopInfo] = None) -> List[FirewallFinding]:
        findings: List[FirewallFinding] = []
        if hop.icmp_type == 11 and hop.icmp_code == 0:
            findings.append(FirewallFinding(
                hop_number=hop.hop_number, protocol=ProtocolType.UDP,
                action=FirewallAction(FirewallRuleType.ACCEPT, "Normal traceroute response"),
                confidence=0.99
            ))
            return findings
        if hop.icmp_type == 3:
            codes = {
                0: (FirewallRuleType.DROP, "Network Unreachable", 0.95),
                1: (FirewallRuleType.DROP, "Host Unreachable", 0.90),
                3: (FirewallRuleType.REJECT, "Port Closed", 0.85),
                13: (FirewallRuleType.DROP, "Administratively Prohibited (Firewall ACL)", 0.98),
            }
            if hop.icmp_code in codes:
                rule_type, desc, conf = codes[hop.icmp_code]
                findings.append(FirewallFinding(
                    hop_number=hop.hop_number, protocol=ProtocolType.UDP,
                    action=FirewallAction(rule_type, desc), confidence=conf,
                    details={"code": hop.icmp_code}
                ))
        return findings

    def analyze_scan_results(self, results: List[ScanResult]) -> List[FirewallFinding]:
        findings: List[FirewallFinding] = []
        icmp_ok = any(r.protocol == ProtocolType.UDP and r.success for r in results)
        tcp_ok = any(r.protocol == ProtocolType.TCP and r.success for r in results)
        udp_fail = any(r.protocol == ProtocolType.UDP and not r.success for r in results)
        tcp_fail = any(r.protocol == ProtocolType.TCP and not r.success for r in results)
        if icmp_ok and tcp_ok and udp_fail:
            findings.append(FirewallFinding(
                protocol=ProtocolType.UDP,
                action=FirewallAction(FirewallRuleType.DROP, "Firewall blocking specific UDP port"),
                confidence=0.96
            ))
        if tcp_fail and udp_fail and icmp_ok:
            findings.append(FirewallFinding(
                protocol=ProtocolType.TCP,
                action=FirewallAction(FirewallRuleType.DROP, "Firewall blocking TCP/UDP traffic"),
                confidence=0.92
            ))
        if not icmp_ok and tcp_fail and udp_fail:
            findings.append(FirewallFinding(
                protocol=ProtocolType.UDP,
                action=FirewallAction(FirewallRuleType.DROP, "Route failure or complete network block"),
                confidence=0.85
            ))
        return findings

    def correlate_with_traceroute(self, hops: List[HopInfo], scan_results: List[ScanResult]) -> Dict[str, Any]:
        analysis = {"drop_point": None, "firewall_location": None, "confidence": 0.0,
                    "recommendations": [], "detailed_analysis": []}
        last_working_hop = None
        first_failing_hop = None
        for i, hop in enumerate(hops):
            if hop.status in ["alive", "traceroute"]:
                last_working_hop = hop.hop_number
                analysis["detailed_analysis"].append(f"Working hop: {hop}")
            else:
                if first_failing_hop is None:
                    first_failing_hop = hop.hop_number
                analysis["detailed_analysis"].append(f"Failing hop: {hop}")
        if first_failing_hop is not None and last_working_hop is not None:
            analysis["drop_point"] = first_failing_hop
            analysis["firewall_location"] = f"Between hop {last_working_hop} and hop {first_failing_hop}"
            analysis["confidence"] = 0.85 + (first_failing_hop - last_working_hop) * 0.05
        for finding in self.analyze_scan_results(scan_results):
            analysis["detailed_analysis"].append(f"Scan finding: {finding.get_summary()}")
        if analysis["confidence"] > 0.9:
            analysis["recommendations"].append("Contact ISP or network administrator immediately")
        elif analysis["drop_point"]:
            analysis["recommendations"].append(f"Check firewall at or after hop {analysis['drop_point']}")
        else:
            analysis["recommendations"].append("Continue investigation with additional scan methods")
        return analysis


class FirewallAnalyzer:
    """High-level firewall analysis interface"""

    def __init__(self):
        self.rule_engine = FirewallRuleEngine()

    def analyze_trace_route(self, hops: List[HopInfo]) -> List[FirewallFinding]:
        findings: List[FirewallFinding] = []
        for i, hop in enumerate(hops):
            previous = hops[i - 1] if i > 0 else None
            hop_findings = self.rule_engine.analyze_hop(hop, previous)
            findings.extend(hop_findings)
        return findings

    def analyze_comprehensive(self, hops: List[HopInfo], scan_results: List[ScanResult]) -> Dict[str, Any]:
        findings = self.rule_engine.analyze_scan_results(scan_results)
        correlation = self.rule_engine.correlate_with_traceroute(hops, scan_results)
        return {
            "findings": findings, "correlation": correlation,
            "overall_assessment": self._generate_overall_assessment(findings, correlation)
        }

    def _generate_overall_assessment(self, findings, correlation):
        drop_count = sum(1 for f in findings if f.action.rule_type == FirewallRuleType.DROP)
        assessment = {"threat_level": "LOW",
                      "summary": "No significant firewall issues detected",
                      "actionable_findings": []}
        if drop_count > 0:
            assessment["threat_level"] = "HIGH" if drop_count > 2 else "MEDIUM"
            assessment["summary"] = f"Detected {drop_count} firewall DROP rules"
        if correlation["confidence"] > 0.9:
            assessment["summary"] += " - High confidence"
        assessment["actionable_findings"] = [f.get_summary() for f in findings if f.confidence > 0.8]
        return assessment


def analyze_firewall(hops: List[HopInfo], scan_results: List[ScanResult]) -> Dict[str, Any]:
    analyzer = FirewallAnalyzer()
    return analyzer.analyze_comprehensive(hops, scan_results)


# ============================================================================
# REPORT MODULE
# ============================================================================

class ReportGenerator:
    """Base report generator"""
    def __init__(self, context: ReportContext):
        self.context = context
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def generate(self, output_path: str = None) -> str:
        raise NotImplementedError

    def _get_report_filename(self, extension: str) -> str:
        if not self.context.target:
            target = "localhost"
        else:
            target = self.context.target.replace(".", "_")
        filename = f"netprobe_{target}_{self.timestamp}{extension}"
        return filename


class ConsoleReporter(ReportGenerator):
    def __init__(self, context: ReportContext, use_rich: bool = True):
        super().__init__(context)
        self.use_rich = use_rich
        self.console = Console() if use_rich and HAS_RICH else None

    def generate(self, output_path: str = None) -> str:
        if self.use_rich and self.console:
            return self._generate_rich_report()
        else:
            return self._generate_plain_report()

    def _generate_rich_report(self) -> str:
        output = []
        output.append(f"\n{'='*60}")
        output.append(f"  Network Probe Report")
        output.append(f"{'='*60}\n")
        output.append(f"Target: {self.context.target}")
        output.append(f"Protocol: {self.context.port}")
        output.append(f"Hops: {len(self.context.hops)}")
        output.append(f"Scan Results: {len(self.context.scan_results)}")
        output.append(f"Findings: {len(self.context.findings)}")
        output.append(f"Duration: {self.context.end_time - self.context.start_time:.2f}s")
        output.append("")
        if self.context.hops:
            output.append("Traceroute Path:")
            table = RichTable(title="Hop Path", show_header=True)
            table.add_column("Hop", style="blue")
            table.add_column("IP", style="green")
            table.add_column("Hostname", style="yellow")
            table.add_column("RTT", style="cyan")
            table.add_column("Status", style="magenta")
            for hop in self.context.hops:
                table.add_row(str(hop.hop_number), hop.ip_address,
                              hop.hostname or "<unknown>", f"{hop.rtt:.1f}ms", hop.status)
            output.append(str(table))
            output.append("")
        if self.context.scan_results:
            output.append("Protocol Scan Results:")
            table = RichTable(title="Port Scan", show_header=True)
            table.add_column("Protocol", style="blue")
            table.add_column("Port", style="green")
            table.add_column("Result", style="yellow")
            table.add_column("RTT", style="cyan")
            for result in self.context.scan_results:
                status = "Open" if result.success else "Closed/Filtered" if result.timeout or result.error else "Error"
                table.add_row(result.protocol.name, str(result.port) if result.port else "N/A",
                              status, f"{result.rtt:.1f}ms")
            output.append(str(table))
            output.append("")
        if self.context.findings:
            output.append("Firewall Analysis:")
            for finding in self.context.findings:
                output.append(f"  - {finding.get_summary()} (Confidence: {finding.confidence:.0%})")
            output.append("")
        output.append("\n" + "="*60)
        output.append("End of Report")
        output.append("="*60)
        return "\n".join(output)

    def _generate_plain_report(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("Network Probe Report")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Target: {self.context.target}")
        lines.append(f"Protocol: {self.context.port}")
        lines.append(f"Hops: {len(self.context.hops)}")
        lines.append(f"Scan Results: {len(self.context.scan_results)}")
        lines.append(f"Findings: {len(self.context.findings)}")
        lines.append(f"Duration: {self.context.end_time - self.context.start_time:.2f}s")
        lines.append("")
        if self.context.hops:
            lines.append("Traceroute Path:")
            lines.append(f"{'#':<4} {'IP':<15} {'Hostname':<30} {'RTT':<8} {'Status':<12}")
            lines.append("-" * 70)
            for hop in self.context.hops:
                lines.append(f"{hop.hop_number:<4} {hop.ip_address:<15} {hop.hostname or '<unknown>':<30} {hop.rtt:<8.1f} {hop.status:<12}")
            lines.append("")
        if self.context.scan_results:
            lines.append("Protocol Scan Results:")
            lines.append(f"{'Protocol':<10} {'Port':<8} {'Result':<15} {'RTT':<8}")
            lines.append("-" * 45)
            for result in self.context.scan_results:
                status = "Open" if result.success else "Filtered" if result.timeout else "Error"
                lines.append(f"{result.protocol.name:<10} {result.port or 'N/A':<8} {status:<15} {result.rtt:<8.1f}")
            lines.append("")
        if self.context.findings:
            lines.append("Firewall Analysis:")
            for finding in self.context.findings:
                lines.append(f"  - {finding.get_summary()}")
            lines.append("")
        lines.append("=" * 60)
        lines.append("End of Report")
        lines.append("=" * 60)
        return "\n".join(lines)


class JsonReporter(ReportGenerator):
    def generate(self, output_path: str = None) -> str:
        report = {
            "metadata": {
                "target": self.context.target, "protocol": self.context.port,
                "start_time": datetime.fromtimestamp(self.context.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(self.context.end_time).isoformat(),
                "duration_seconds": self.context.end_time - self.context.start_time,
                "version": "1.0.1"
            },
            "traceroute": {"hops": [
                {"hop_number": h.hop_number, "ip_address": h.ip_address, "hostname": h.hostname,
                 "rtt": h.rtt, "ttl": h.ttl, "icmp_type": h.icmp_type, "icmp_code": h.icmp_code,
                 "status": h.status} for h in self.context.hops
            ]},
            "scan_results": [
                {"host": r.host, "port": r.port, "protocol": r.protocol.name,
                 "success": r.success, "timeout": r.timeout, "error": r.error,
                 "rtt": r.rtt, "timestamps": r.timestamps}
                for r in self.context.scan_results
            ],
            "firewall_findings": [
                {"hop_number": f.hop_number, "protocol": f.protocol.name if f.protocol else None,
                 "port": f.port, "action": f.action.rule_type.value,
                 "description": f.action.description, "confidence": f.confidence,
                 "details": f.details}
                for f in self.context.findings
            ],
            "ip_info": {
                ip: {"country": info.country, "city": info.city, "asn": info.asn, "isp": info.isp}
                for ip, info in self.context.ip_info.items()
            }
        }
        report_str = json.dumps(report, indent=2, default=str)
        filename = output_path or self._get_report_filename(".json")
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_str)
        logger.info(f"JSON report generated: {filename}")
        return report_str


class CsvReporter(ReportGenerator):
    def generate(self, output_path: str = None) -> str:
        filename = output_path or self._get_report_filename(".csv")
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Network Probe Report"])
            writer.writerow(["Target", self.context.target])
            writer.writerow(["Protocol", self.context.port])
            writer.writerow(["Start Time", datetime.fromtimestamp(self.context.start_time).isoformat()])
            writer.writerow(["End Time", datetime.fromtimestamp(self.context.end_time).isoformat()])
            writer.writerow([])
            writer.writerow(["--- Traceroute Hops ---"])
            writer.writerow(["Hop", "IP Address", "Hostname", "RTT (ms)", "TTL", "ICMP Type", "ICMP Code", "Status"])
            for hop in self.context.hops:
                writer.writerow([hop.hop_number, hop.ip_address, hop.hostname or "",
                                 f"{hop.rtt:.1f}", hop.ttl, hop.icmp_type, hop.icmp_code, hop.status])
            writer.writerow([])
            writer.writerow(["--- Scan Results ---"])
            writer.writerow(["Protocol", "Port", "Success", "Timeout", "Error", "RTT (ms)"])
            for result in self.context.scan_results:
                writer.writerow([result.protocol.name, result.port or "",
                                 str(result.success), str(result.timeout), result.error or "", f"{result.rtt:.1f}"])
            writer.writerow([])
            writer.writerow(["--- Firewall Findings ---"])
            writer.writerow(["Hop", "Protocol", "Port", "Action", "Description", "Confidence"])
            for finding in self.context.findings:
                writer.writerow([finding.hop_number,
                                 finding.protocol.name if finding.protocol else "N/A",
                                 finding.port or "", finding.action.rule_type.value,
                                 finding.action.description, finding.confidence])
        logger.info(f"CSV report generated: {filename}")
        return filename


class HtmlReporter(ReportGenerator):
    def generate(self, output_path: str = None) -> str:
        filename = output_path or self._get_report_filename(".html")
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Probe Report - {self.context.target}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #2c3e50; }}
        .report-header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ background-color: #fff; padding: 20px; margin-bottom: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        table th, table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        table th {{ background-color: #f2f2f2; }}
        table tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .finding {{ padding: 10px; margin: 5px 0; border-radius: 3px; }}
        .finding.high {{ background-color: #ffebee; border-left: 4px solid #f44336; }}
        .finding.medium {{ background-color: #fff8e1; border-left: 4px solid #ff9800; }}
        .finding.low {{ background-color: #e8f5e9; border-left: 4px solid #4caf50; }}
    </style>
</head>
<body>
    <div class="report-header">
        <h1>Network Probe Report</h1>
        <p><strong>Target:</strong> {self.context.target}</p>
        <p><strong>Protocol:</strong> {self.context.port}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Duration:</strong> {self.context.end_time - self.context.start_time:.2f} seconds</p>
    </div>
    <div class="section">
        <h2>Traceroute Path</h2>
        <table>
            <thead><tr><th>Hop</th><th>IP Address</th><th>Hostname</th><th>RTT (ms)</th><th>TTL</th><th>Status</th></tr></thead>
            <tbody>
"""
        for hop in self.context.hops:
            html += f"                <tr><td>{hop.hop_number}</td><td>{hop.ip_address}</td><td>{hop.hostname or '<unknown>'}</td><td>{hop.rtt:.1f}</td><td>{hop.ttl}</td><td>{hop.status}</td></tr>\n"
        html += """            </tbody>
        </table>
    </div>
    <div class="section">
        <h2>Scan Results</h2>
        <table>
            <thead><tr><th>Protocol</th><th>Port</th><th>Result</th><th>RTT (ms)</th><th>Error</th></tr></thead>
            <tbody>
"""
        for result in self.context.scan_results:
            status = "Open" if result.success else "Filtered" if result.timeout else "Error"
            html += f"                <tr><td>{result.protocol.name}</td><td>{result.port or 'N/A'}</td><td>{status}</td><td>{result.rtt:.1f}</td><td>{result.error or '-'}</td></tr>\n"
        html += """            </tbody>
        </table>
    </div>
    <div class="section">
        <h2>Firewall Analysis</h2>
"""
        for finding in self.context.findings:
            severity = "high" if finding.confidence > 0.9 else "medium" if finding.confidence > 0.7 else "low"
            html += f'                <div class="finding {severity}"><strong>{finding.get_summary()}</strong><br>Confidence: {finding.confidence:.0%}</div>\n'
        html += """    </div>
</body>
</html>"""
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        logger.info(f"HTML report generated: {filename}")
        return filename


class MarkdownReporter(ReportGenerator):
    def generate(self, output_path: str = None) -> str:
        filename = output_path or self._get_report_filename(".md")
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        md = f"""# Network Probe Report

**Target:** {self.context.target}
**Protocol:** {self.context.port}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Duration:** {self.context.end_time - self.context.start_time:.2f} seconds

## Traceroute Path

| Hop | IP Address | Hostname | RTT (ms) | TTL | Status |
|-----|------------|----------|----------|-----|--------|
"""
        for hop in self.context.hops:
            md += f"| {hop.hop_number} | {hop.ip_address} | {hop.hostname or '<unknown>'} | {hop.rtt:.1f} | {hop.ttl} | {hop.status} |\n"
        md += "\n## Scan Results\n\n"
        md += "| Protocol | Port | Result | RTT (ms) | Error |\n"
        md += "|----------|------|--------|----------|-------|\n"
        for result in self.context.scan_results:
            status = "Open" if result.success else "Filtered" if result.timeout else "Error"
            md += f"| {result.protocol.name} | {result.port or 'N/A'} | {status} | {result.rtt:.1f} | {result.error or '-'} |\n"
        md += "\n## Firewall Analysis\n\n"
        for finding in self.context.findings:
            md += f"- **{finding.get_summary()}** (Confidence: {finding.confidence:.0%})\n"
        md += "\n---\n*Generated by Network Probe v1.0.1*\n"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md)
        logger.info(f"Markdown report generated: {filename}")
        return filename


class ReportFactory:
    @staticmethod
    def get_reporter(context: ReportContext, format: str) -> ReportGenerator:
        format = format.lower()
        reporters = {
            "console": lambda: ConsoleReporter(context, use_rich=True),
            "json": lambda: JsonReporter(context),
            "csv": lambda: CsvReporter(context),
            "html": lambda: HtmlReporter(context),
            "markdown": lambda: MarkdownReporter(context),
        }
        if format in reporters:
            return reporters[format]()
        raise ValueError(f"Unknown report format: {format}")

    @staticmethod
    def generate_all(context: ReportContext, formats: List[str] = None, output_path: str = None) -> Dict[str, str]:
        if formats is None:
            formats = ["console", "json", "html"]
        # Derive per-format output paths from the user-supplied output_path
        derived_outputs: Dict[str, Optional[str]] = {}
        if output_path:
            import os.path
            base = output_path
            # Find the extension of the user-provided path (e.g., ".html")
            ext = os.path.splitext(base)[1].lower()
            for fmt in formats:
                if fmt == "console":
                    derived_outputs[fmt] = None
                else:
                    expected_ext = f".{fmt}"
                    if ext == expected_ext:
                        # User explicitly requested this format - use the given path
                        derived_outputs[fmt] = base
                    else:
                        # Derive a new path: replace extension
                        # e.g., "results/report.html" -> "results/report.json"
                        derived_outputs[fmt] = os.path.splitext(base)[0] + expected_ext
        else:
            for fmt in formats:
                derived_outputs[fmt] = None
        results: Dict[str, str] = {}
        for fmt in formats:
            try:
                reporter = ReportFactory.get_reporter(context, fmt)
                if fmt == "console":
                    result = reporter.generate()
                else:
                    result = reporter.generate(output_path=derived_outputs[fmt])
                results[fmt] = result
                logger.info(f"Generated report ({fmt})")
            except Exception as e:
                logger.error(f"Failed to generate {fmt} report: {e}")
        return results


# ============================================================================
# MAIN CLI APPLICATION
# ============================================================================

class ProbeResult:
    """Comprehensive probe result"""
    def __init__(self, target, protocol, port, hops, scan_results, findings, ip_info, duration, correlation, trace_note=None):
        self.target = target
        self.protocol = protocol
        self.port = port
        self.hops = hops
        self.scan_results = scan_results
        self.findings = findings
        self.ip_info = ip_info
        self.duration = duration
        self.correlation = correlation
        self.trace_note = trace_note


class NetworkProbe:
    """Main Network Probe application"""

    def __init__(self, config: Optional[Any] = None):
        self.config = config
        self.scanner = TraceRouteScanner(max_ttl=30, timeout=2.0, retries=3)
        self.tcp_scanner = TcpPortScanner(timeout=2.0)
        self.udp_scanner = UdpPortScanner(timeout=2.0)
        self.dns_scanner = DnsPortScanner(timeout=5.0)
        self.parallel_scanner = ParallelScanner(max_workers=10)
        self.firewall_analyzer = FirewallAnalyzer()

    def run(self, target: str, protocol: ProtocolType = ProtocolType.TCP,
            port: Optional[int] = None, dns_query: bool = False) -> ProbeResult:
        """Execute network probe"""
        start_time = time.time()
        logger.info(f"Starting network probe to {target} ({protocol.name}{f':{port}' if port else ''})")

        trace_target = target
        trace_protocol = ProtocolType.ICMP
        trace_port = port
        trace_payload = b""

        if protocol == ProtocolType.DNS:
            ip_pattern = re.match(r'^\d+\.\d+\.\d+\.\d+$', target)
            query_name = "example.com" if ip_pattern else target
            dns_server = target if ip_pattern else "8.8.8.8"
            trace_target = dns_server
            trace_protocol = ProtocolType.DNS
            trace_port = 53
            trace_payload = self.dns_scanner._build_query(query_name)
            logger.info(f"Executing DNS-aware traceroute to server {dns_server} with query name {query_name}...")
        elif protocol == ProtocolType.UDP and port:
            trace_protocol = ProtocolType.UDP
            logger.info(f"Executing UDP-aware traceroute to port {port}...")
        else:
            logger.info("Executing ICMP traceroute...")

        hops = self.scanner.trace(trace_target, protocol=trace_protocol, port=trace_port, payload=trace_payload)
        trace_note = None
        # Resolve target IP for fallback detection
        try:
            target_ip = socket.gethostbyname(trace_target)
        except socket.gaierror:
            target_ip = trace_target
        # Fallback to system tracert when raw socket fails to get intermediate hop responses
        # This covers DNS, UDP, and ICMP protocols on Windows
        if trace_protocol in (ProtocolType.DNS, ProtocolType.UDP, ProtocolType.ICMP):
            if hops:
                # Check for all timeouts (*) or all hops pointing to target (raw socket didn't get intermediate replies)
                has_timeouts = all(hop.ip_address == "*" for hop in hops)
                has_target_only = all(hop.ip_address == target_ip for hop in hops)
                if has_timeouts or has_target_only:
                    logger.warning("Raw socket traceroute produced no intermediate hops; falling back to system tracert")
                    hops = self.scanner._trace_via_system_command(trace_target)
                    if has_timeouts:
                        trace_note = "Hop Path uses system tracert fallback because Windows did not expose per-hop ICMP replies for the UDP/DNS probes."
                    else:
                        trace_note = "Hop Path uses system tracert fallback because raw socket did not receive ICMP Time Exceeded replies from intermediate hops."

        ip_info = {}
        for hop in hops:
            if hop.ip_address != "*":
                ip_info[hop.ip_address] = get_ip_info(hop.ip_address)

        scan_results: Dict[int, ScanResult] = {}
        if protocol == ProtocolType.TCP and port:
            logger.info(f"Scanning TCP port {port}...")
            result = self.tcp_scanner.scan_syn(target, port)
            scan_results[port] = result
        elif protocol == ProtocolType.UDP and port:
            logger.info(f"Scanning UDP port {port}...")
            result = self.udp_scanner.scan(target, port)
            scan_results[port] = result
        elif protocol == ProtocolType.DNS:
            logger.info("Performing DNS query...")
            ip_pattern = re.match(r'^\d+\.\d+\.\d+\.\d+$', target)
            domain = "example.com" if ip_pattern else target
            server = target if ip_pattern else "8.8.8.8"
            result = self.dns_scanner.query(domain, server=server)
            scan_results[53] = result
        elif dns_query:
            logger.info("Performing DNS lookup...")
            result = self.dns_scanner.query(target)
            scan_results[53] = result
        else:
            logger.info("Scanning common ports...")
            for common_port in [80, 443, 53, 22, 21, 23, 3389, 3306, 5432]:
                result = self.tcp_scanner.scan_syn(target, common_port)
                scan_results[common_port] = result

        logger.info("Analyzing firewall patterns...")
        analysis = self.firewall_analyzer.analyze_comprehensive(hops, list(scan_results.values()))
        duration = time.time() - start_time
        logger.info(f"Probe completed in {duration:.2f}s")

        return ProbeResult(
            target=target, protocol=protocol, port=port, hops=hops,
            scan_results=scan_results, findings=analysis["findings"],
            ip_info=ip_info, duration=duration, correlation=analysis["correlation"],
            trace_note=trace_note,
        )

    def print_result(self, result: ProbeResult, use_rich: bool = True) -> None:
        """Print probe result to console"""
        def render_scan_status(scan_result: ScanResult) -> str:
            if scan_result.success:
                return "Open"
            if scan_result.timeout:
                return "Filtered"
            if scan_result.error and "closed" in scan_result.error.lower():
                return "Closed"
            return "Error"

        if use_rich and HAS_RICH:
            console = Console()
        else:
            console = None

        if console:
            console.print(f"\n[bold green]=== Network Probe Report ===[/bold green]")
            console.print(f"[blue]Target:[/blue] {result.target}")
            console.print(f"[green]Protocol:[/green] {result.protocol.name}")
            if result.port:
                console.print(f"[yellow]Port:[/yellow] {result.port}")
            console.print(f"[magenta]Duration:[/magenta] {result.duration:.2f}s")
            console.print(f"[cyan]Hops:[/cyan] {len(result.hops)}")
            console.print(f"[cyan]Findings:[/cyan] {len(result.findings)}")
            if result.correlation.get("firewall_location"):
                console.print(f"[red]Likely drop:[/red] {result.correlation['firewall_location']}")
            if result.trace_note:
                console.print(f"[yellow]Note:[/yellow] {result.trace_note}")
            console.print()
            console.print("[bold]Traceroute Path:[/bold]")
            table = RichTable(title="Hop Path", show_header=True)
            table.add_column("Hop", style="blue")
            table.add_column("IP", style="green")
            table.add_column("Hostname", style="yellow")
            table.add_column("RTT", style="cyan")
            table.add_column("Status", style="magenta")
            max_display_hops = 50
            if len(result.hops) > max_display_hops:
                for hop in result.hops[:10]:
                    table.add_row(str(hop.hop_number), hop.ip_address,
                                  hop.hostname or "<unknown>", f"{hop.rtt:.1f}ms", hop.status)
                table.add_row("...", "...", f"... ({len(result.hops)} total) ...", "...", "...")
                for hop in result.hops[-5:]:
                    table.add_row(str(hop.hop_number), hop.ip_address,
                                  hop.hostname or "<unknown>", f"{hop.rtt:.1f}ms", hop.status)
                console.print(f"[yellow]{len(result.hops)} hops total (first 10 + last 5 shown)")
            else:
                for hop in result.hops:
                    table.add_row(str(hop.hop_number), hop.ip_address,
                                  hop.hostname or "<unknown>", f"{hop.rtt:.1f}ms", hop.status)
            console.print(table)
            console.print()
            console.print("[bold]Protocol Scan Results:[/bold]")
            table = RichTable(title="Port Scan", show_header=True)
            table.add_column("Protocol", style="blue")
            table.add_column("Port", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("RTT", style="cyan")
            for port, scan_result in result.scan_results.items():
                status = render_scan_status(scan_result)
                table.add_row(scan_result.protocol.name, str(port), status, f"{scan_result.rtt:.1f}ms")
            console.print(table)
            if result.findings:
                console.print()
                console.print("[bold red]Firewall Analysis:[/bold red]")
                for finding in result.findings:
                    console.print(f"  • {finding.get_summary()} (Confidence: {finding.confidence:.0%})")
            console.print()
            console.print("[bold]=== End of Report ===[/bold]")
        else:
            print(f"\n{'='*60}")
            print("Network Probe Report")
            print(f"{'='*60}")
            print(f"Target: {result.target}")
            print(f"Protocol: {result.protocol.name}")
            if result.port:
                print(f"Port: {result.port}")
            print(f"Duration: {result.duration:.2f}s")
            print(f"Hops: {len(result.hops)}")
            print(f"Findings: {len(result.findings)}")
            if result.correlation.get("firewall_location"):
                print(f"Likely drop: {result.correlation['firewall_location']}")
            if result.trace_note:
                print(f"Note: {result.trace_note}")
            print()
            if result.hops:
                print("Traceroute Path:")
                print(f"{'#':<4} {'IP':<15} {'Hostname':<30} {'RTT':<8} {'Status':<12}")
                print("-" * 70)
                max_display = 50
                if len(result.hops) > max_display:
                    for hop in result.hops[:10]:
                        print(f"{hop.hop_number:<4} {hop.ip_address:<15} {hop.hostname or '<unknown>':<30} {hop.rtt:<8.1f} {hop.status:<12}")
                    print(f"{'...':<4} {'...':<15} {'... ({len(result.hops)} total) ...':<30} {'...':<8} {'...':<12}")
                    for hop in result.hops[-5:]:
                        print(f"{hop.hop_number:<4} {hop.ip_address:<15} {hop.hostname or '<unknown>':<30} {hop.rtt:<8.1f} {hop.status:<12}")
                    print(f"[yellow]{len(result.hops)} hops total (first 10 + last 5 shown)")
                else:
                    for hop in result.hops:
                        print(f"{hop.hop_number:<4} {hop.ip_address:<15} {hop.hostname or '<unknown>':<30} {hop.rtt:<8.1f} {hop.status:<12}")
                print()
            if result.scan_results:
                print("Protocol Scan Results:")
                print(f"{'Protocol':<10} {'Port':<8} {'Result':<15} {'RTT':<8}")
                print("-" * 45)
                for port, scan_result in result.scan_results.items():
                    status = render_scan_status(scan_result)
                    print(f"{scan_result.protocol.name:<10} {port:<8} {status:<15} {scan_result.rtt:.1f}")
                print()
            if result.findings:
                print("Firewall Analysis:")
                for finding in result.findings:
                    print(f"  - {finding.get_summary()}")
                print()
            print(f"{'='*60}")
            print("End of Report")
            print(f"{'='*60}")

    def generate_reports(self, result: ProbeResult, formats: List[str] = None, output_path: str = None) -> Dict[str, str]:
        """Generate reports in specified formats"""
        if formats is None:
            formats = ["console", "json", "html"]
        context = ReportContext(
            target=result.target,
            protocol=str(result.protocol),
            port=result.port if result.port else 0,
            hops=result.hops,
            scan_results=list(result.scan_results.values()),
            findings=result.findings,
            ip_info=result.ip_info
        )
        context.start_time = time.time() - result.duration
        context.end_time = time.time()
        return ReportFactory.generate_all(context, formats, output_path=output_path)


def parse_protocol(proto: str) -> ProtocolType:
    """Parse protocol string to ProtocolType enum."""
    proto_map = {
        "tcp": ProtocolType.TCP, "udp": ProtocolType.UDP,
        "icmp": ProtocolType.UDP, "dns": ProtocolType.DNS,
        "http": ProtocolType.HTTP, "https": ProtocolType.HTTPS,
        "auto": ProtocolType.TCP,
    }
    return proto_map.get(proto.lower(), ProtocolType.TCP)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Network Probe - Advanced network diagnostic tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  probe.py 8.8.8.8                    # TCP traceroute to Google DNS
  probe.py 8.8.8.8 -udp 53           # UDP traceroute to port 53
  probe.py google.com -dns           # DNS query
  probe.py github.com -tcp 443       # TCP SYN scan to port 443
  probe.py 8.8.8.8 --dns-trace       # DNS traceroute to find blocking point
        """
    )

    parser.add_argument("target", help="Target host or IP address")
    parser.add_argument("--port", type=int, help="Target port (for TCP/UDP/DNS scans)")
    parser.add_argument("-P", "--protocol", choices=["auto", "tcp", "udp", "dns", "icmp", "http", "https"],
                        default="auto",
                        help="Protocol to use: auto (default), tcp, udp, dns, icmp, http, https.")
    parser.add_argument("--max-ttl", type=int, default=30, help="Maximum TTL for traceroute (default: 30)")
    parser.add_argument("--timeout", type=float, default=2.0, help="Packet timeout in seconds (default: 2.0)")
    parser.add_argument("--retries", type=int, default=3, help="Number of retries per hop (default: 3)")
    parser.add_argument("--format", choices=["console", "json", "html", "csv", "markdown", "pdf"],
                        default="console", help="Report format (default: console)")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--dns-trace", action="store_true",
                        help="Run DNS-specific traceroute to find where external DNS is blocked")

    args = parser.parse_args()

    probe = NetworkProbe()
    raw_protocol = args.protocol
    protocol = parse_protocol(raw_protocol)

    # Auto-detection: port 53 -> DNS protocol
    if raw_protocol == "auto" and args.port == 53:
        logger.info("Auto-detected DNS port 53, switching to DNS protocol")
        protocol = ProtocolType.DNS
        raw_protocol = "dns"

    # Execute probe or DNS traceroute
    try:
        if args.dns_trace:
            # Run DNS-specific traceroute to find where external DNS is blocked
            logger.info(f"Running DNS traceroute to {args.target}")
            domain = "example.com"
            hops = quick_dns_trace(args.target, domain=domain, max_ttl=args.max_ttl, timeout=args.timeout)

            print(f"\n{'='*70}")
            print(f"DNS Traceroute to {args.target} (domain={domain})")
            print(f"{'='*70}")
            print(f"{'#':<4} {'IP':<18} {'Hostname':<30} {'RTT':<10} {'Status':<15} {'Details'}")
            print("-" * 90)

            for hop in hops:
                details = ""
                if hop.has_dns_response:
                    details = f"[DNS] {hop.dns_response_text}"
                elif hop.icmp_type:
                    details = f"(ICMP {hop.icmp_type}/{hop.icmp_code})"

                print(f"{hop.hop_number:<4} {hop.ip_address:<18} {hop.hostname or '<unknown>':<30} "
                      f"{hop.rtt:<10.1f} {hop.status.value:<15} {details}")

            print(f"\n{'='*70}")

            # Find blocking node
            blocking_node = None
            last_hop = hops[-1] if hops else None

            for hop in hops:
                if hop.status in (DnsTraceStatus.BLOCKED, DnsTraceStatus.TIME_EXCEEDED) and hop.ip_address != "*":
                    blocking_node = hop
                    break

            if last_hop and last_hop.status in (DnsTraceStatus.DNS_RESPONSE, DnsTraceStatus.REACHED_TARGET):
                print(f"Result: DNS query reached {args.target} successfully - external DNS is accessible!")
            elif blocking_node:
                print(f"Result: DNS query BLOCKED at hop {blocking_node.hop_number} ({blocking_node.ip_address})")
            elif last_hop and last_hop.ip_address == "*":
                print(f"Result: DNS query stopped at hop {last_hop.hop_number} - query did not reach external DNS")
            elif hops:
                print(f"Result: DNS query reached final hop {hops[-1].hop_number} but did not receive DNS response")
            print(f"{'='*70}\n")

            sys.exit(0)

        # Normal network probe
        result = probe.run(
            target=args.target,
            protocol=protocol,
            port=args.port,
            dns_query=(raw_protocol == "dns")
        )

        # Print result
        probe.print_result(result, use_rich=not args.no_color)

        # Generate report if file output specified
        if args.output:
            formats = [args.format] if args.format else ["json"]
            reports = probe.generate_reports(result, formats, output_path=args.output)
            for fmt, path in reports.items():
                if args.output:
                    import shutil
                    base = os.path.basename(args.output)
                    # If output already has the correct extension, use it directly
                    if base.endswith(f".{fmt}"):
                        out_path = args.output
                    else:
                        out_path = os.path.join(os.path.dirname(args.output), f"{base}.{fmt}") if "." in base else f"{args.output}.{fmt}"
                    # Skip copy if source and destination are the same
                    if path == out_path:
                        logger.info(f"Report saved to {out_path}")
                    else:
                        shutil.copy(path, out_path)
                        logger.info(f"Report saved to {out_path}")
                else:
                    logger.info(f"Report generated: {path}")

        # Exit with code based on findings
        if result.findings:
            print("\n[WARNING] Firewall issues detected. See report for details.")
            sys.exit(1)
        else:
            print("\n[OK] No firewall issues detected.")
            sys.exit(0)

    except PermissionError:
        logger.error("Permission denied - run as administrator for raw socket access")
        print("Error: Permission denied. Run this tool as administrator/root for full functionality.")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Probe failed: {e}")
        print(f"Error: {e}")
        sys.exit(3)


# ============================================================================
# CONVENIENCE FUNCTIONS (module-level API)
# ============================================================================

def quick_check_port(host: str, port: int, protocol: str = "auto") -> ScanResult:
    """Quick port check with auto-detection for DNS port 53"""
    if protocol == "auto" and port == 53:
        return quick_dns_query("example.com", server=host)
    proto = parse_protocol(protocol)
    if proto == ProtocolType.TCP:
        return TcpPortScanner().scan_syn(host, port)
    elif proto == ProtocolType.UDP:
        return UdpPortScanner().scan(host, port)
    else:
        return TcpPortScanner().scan_syn(host, port)


def quick_tcp_scan(host: str, port: int) -> ScanResult:
    """Quick TCP scan"""
    return TcpPortScanner().scan_syn(host, port)


def quick_udp_scan(host: str, port: int, payload: bytes = b"") -> ScanResult:
    """Quick UDP scan"""
    return UdpPortScanner().scan(host, port, payload)


def quick_dns_query(domain: str, server: str = "8.8.8.8") -> ScanResult:
    """Quick DNS query"""
    return DnsPortScanner().query(domain, server)


if __name__ == "__main__":
    main()