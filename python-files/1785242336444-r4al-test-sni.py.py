import socket
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CONFIGURATION ---
TARGET_IP = "eritel.com.er"  # Your stunnel / gateway server IP
TARGET_PORT = 443             # Public TLS port
TIMEOUT = 4.0                 # Timeout in seconds
MAX_THREADS = 10              # Concurrent scan threads
OUTPUT_FILE = "sni_scan_results.txt" # File to save results

# List of candidate SNI domains to test
CANDIDATE_SNIS = [
    # --- 1. Video, Audio & Streaming ---
    "zte.com",
    "google.com",
    "microsoft.com",
    "xmdo.com",
    "www.netflix.com",
    "netflix.com",
    "www.youtube.com",
    "youtube.com",
    "m.youtube.com",
    "www.hulu.com",
    "amazon.com",
    "hulu.com",
    "www.disneyplus.com",
    "disneyplus.com",
    "www.primevideo.com",
    "primevideo.com",
    "www.max.com",
    "max.com",
    "www.hbo.com",
    "hbo.com",
    "www.paramountplus.com",
    "paramountplus.com",
    "www.peacocktv.com",
    "peacocktv.com",
    "www.vimeo.com",
    "vimeo.com",
    "www.dailymotion.com",
    "dailymotion.com",
    "www.spotify.com",
    "spotify.com",
    "www.soundcloud.com",
    "soundcloud.com",
    "www.deezer.com",
    "deezer.com",
    "www.pandora.com",
    "pandora.com",
    "www.twitch.com",
    "twitch.com",
    "www.crunchyroll.com",
    "crunchyroll.com",
    "www.audible.com",
    "audible.com",
    "www.roku.com",
    "roku.com",

    # --- 2. Antivirus, Cybersecurity & Privacy ---
    "www.avast.com",
    "avast.com",
    "www.avg.com",
    "avg.com",
    "www.mcafee.com",
    "mcafee.com",
    "www.norton.com",
    "norton.com",
    "www.kaspersky.com",
    "kaspersky.com",
    "www.bitdefender.com",
    "bitdefender.com",
    "www.malwarebytes.com",
    "malwarebytes.com",
    "www.eset.com",
    "eset.com",
    "www.sophos.com",
    "sophos.com",
    "www.trendmicro.com",
    "trendmicro.com",
    "www.paloaltonetworks.com",
    "paloaltonetworks.com",
    "www.crowdstrike.com",
    "crowdstrike.com",
    "www.fortinet.com",
    "fortinet.com",
    "www.sentinelone.com",
    "sentinelone.com",
    "www.zscaler.com",
    "zscaler.com",
    "www.rapid7.com",
    "rapid7.com",
    "www.qualys.com",
    "qualys.com",
    "www.digicert.com",
    "digicert.com",
    "www.nordvpn.com",
    "nordvpn.com",
    "www.expressvpn.com",
    "expressvpn.com",

    # --- 3. Cloud Infrastructure, CDNs & Hosting ---
    "www.cloudflare.com",
    "cloudflare.com",
    "www.akamai.com",
    "akamai.com",
    "www.fastly.com",
    "fastly.com",
    "www.imperva.com",
    "imperva.com",
    "www.datadoghq.com",
    "datadoghq.com",
    "www.amazonaws.com",
    "amazonaws.com",
    "www.azure.com",
    "azure.com",
    "cloud.google.com",
    "www.digitalocean.com",
    "digitalocean.com",
    "www.linode.com",
    "linode.com",
    "www.vercel.com",
    "vercel.com",
    "www.netlify.com",
    "netlify.com",

    # --- 4. News, Media & Publishing ---
    "www.cnn.com",
    "cnn.com",
    "edition.cnn.com",
    "www.bbc.com",
    "bbc.com",
    "www.foxnews.com",
    "foxnews.com",
    "www.nytimes.com",
    "nytimes.com",
    "www.washingtonpost.com",
    "washingtonpost.com",
    "www.reuters.com",
    "reuters.com",
    "www.bloomberg.com",
    "bloomberg.com",
    "www.forbes.com",
    "forbes.com",
    "www.nbcnews.com",
    "nbcnews.com",
    "www.cbsnews.com",
    "cbsnews.com",
    "www.aljazeera.com",
    "aljazeera.com",
    "www.huffpost.com",
    "huffpost.com",
    "www.theguardian.com",
    "theguardian.com",
    "www.wsj.com",
    "wsj.com",
    "www.usatoday.com",
    "usatoday.com",
    "www.businessinsider.com",
    "businessinsider.com",
    "www.cnet.com",
    "cnet.com",
    "www.techcrunch.com",
    "techcrunch.com",
    "www.cnbc.com",
    "cnbc.com",
    "www.msnbc.com",
    "msnbc.com",
    "www.abcnews.com",
    "abcnews.com",
    "www.apnews.com",
    "apnews.com",
    "www.dailymail.com",
    "dailymail.com",
    "www.time.com",
    "time.com",
    "www.newsweek.com",
    "newsweek.com",

    # --- 5. Search Engines & Web Portals ---
    "www.google.com",
    "google.com",
    "www.yahoo.com",
    "yahoo.com",
    "www.bing.com",
    "bing.com",
    "www.duckduckgo.com",
    "duckduckgo.com",
    "www.baidu.com",
    "baidu.com",
    "www.yandex.com",
    "yandex.com",

    # --- 6. E-Commerce, Retail & Fashion ---
    "www.amazon.com",
    "amazon.com",
    "www.ebay.com",
    "ebay.com",
    "www.walmart.com",
    "walmart.com",
    "www.target.com",
    "target.com",
    "www.bestbuy.com",
    "bestbuy.com",
    "www.aliexpress.com",
    "aliexpress.com",
    "www.alibaba.com",
    "alibaba.com",
    "www.shopify.com",
    "shopify.com",
    "www.etsy.com",
    "etsy.com",
    "www.homedepot.com",
    "homedepot.com",
    "www.ikea.com",
    "ikea.com",
    "www.wayfair.com",
    "wayfair.com",
    "www.macys.com",
    "macys.com",
    "www.nordstrom.com",
    "nordstrom.com",
    "www.nike.com",
    "nike.com",
    "www.adidas.com",
    "adidas.com",
    "www.shein.com",
    "shein.com",
    "www.temu.com",
    "temu.com",

    # --- 7. Social Media, Messaging & Communities ---
    "www.facebook.com",
    "facebook.com",
    "m.facebook.com",
    "www.instagram.com",
    "instagram.com",
    "www.twitter.com",
    "twitter.com",
    "www.x.com",
    "x.com",
    "www.linkedin.com",
    "linkedin.com",
    "www.pinterest.com",
    "pinterest.com",
    "www.tiktok.com",
    "tiktok.com",
    "www.reddit.com",
    "reddit.com",
    "www.snapchat.com",
    "snapchat.com",
    "www.tumblr.com",
    "tumblr.com",
    "www.discord.com",
    "discord.com",
    "www.whatsapp.com",
    "whatsapp.com",
    "web.whatsapp.com",
    "www.quora.com",
    "quora.com",
    "www.medium.com",
    "medium.com",

    # --- 8. Banking, Payments & Crypto ---
    "www.paypal.com",
    "paypal.com",
    "www.stripe.com",
    "stripe.com",
    "www.visa.com",
    "visa.com",
    "www.mastercard.com",
    "mastercard.com",
    "www.chase.com",
    "chase.com",
    "www.bankofamerica.com",
    "bankofamerica.com",
    "www.wellsfargo.com",
    "wellsfargo.com",
    "www.americanexpress.com",
    "americanexpress.com",
    "www.capitalone.com",
    "capitalone.com",
    "www.citi.com",
    "citi.com",
    "www.fidelity.com",
    "fidelity.com",
    "www.robinhood.com",
    "robinhood.com",
    "www.square.com",
    "square.com",
    "www.coinbase.com",
    "coinbase.com",
    "www.binance.com",
    "binance.com",
    "www.crypto.com",
    "crypto.com",

    # --- 9. SaaS, Developer Tools & Enterprise ---
    "www.microsoft.com",
    "microsoft.com",
    "www.office.com",
    "office.com",
    "www.apple.com",
    "apple.com",
    "www.dropbox.com",
    "dropbox.com",
    "www.zoom.com",
    "zoom.com",
    "www.slack.com",
    "slack.com",
    "www.salesforce.com",
    "salesforce.com",
    "www.adobe.com",
    "adobe.com",
    "www.github.com",
    "github.com",
    "www.gitlab.com",
    "gitlab.com",
    "www.atlassian.com",
    "atlassian.com",
    "www.notion.com",
    "notion.com",
    "www.canva.com",
    "canva.com",
    "www.oracle.com",
    "oracle.com",
    "www.ibm.com",
    "ibm.com",
    "www.stackoverflow.com",
    "stackoverflow.com",

    # --- 10. Education & Learning Platforms ---
    "www.coursera.com",
    "coursera.com",
    "www.udemy.com",
    "udemy.com",
    "www.quizlet.com",
    "quizlet.com",
    "www.duolingo.com",
    "duolingo.com",

    # --- 11. Gaming & Interactive Entertainment ---
    "www.steampowered.com",
    "steampowered.com",
    "www.epicgames.com",
    "epicgames.com",
    "www.roblox.com",
    "roblox.com",
    "www.ea.com",
    "ea.com",
    "www.ubisoft.com",
    "ubisoft.com",
    "www.blizzard.com",
    "blizzard.com",
    "www.nintendo.com",
    "nintendo.com",
    "www.playstation.com",
    "playstation.com",
    "www.xbox.com",
    "xbox.com",

    # --- 12. Travel, Logistics & Food Delivery ---
    "www.booking.com",
    "booking.com",
    "www.airbnb.com",
    "airbnb.com",
    "www.expedia.com",
    "expedia.com",
    "www.tripadvisor.com",
    "tripadvisor.com",
    "www.uber.com",
    "uber.com",
    "www.lyft.com",
    "lyft.com",
    "www.doordash.com",
    "doordash.com",
    "www.ubereats.com",
    "ubereats.com",
    "www.grubhub.com",
    "grubhub.com",
    "www.instacart.com",
    "instacart.com",
    "www.dominos.com",
    "dominos.com",
    "www.starbucks.com",
    "starbucks.com",
    "www.mcdonalds.com",
    "mcdonalds.com",
    "www.fedex.com",
    "fedex.com",
    "www.ups.com",
    "ups.com",
    "www.dhl.com",
    "dhl.com",

    # --- 13. Health, Pharma & Biotech ---
    "www.webmd.com",
    "webmd.com",
    "www.healthline.com",
    "healthline.com",
    "www.pfizer.com",
    "pfizer.com",
    "www.jnj.com",
    "jnj.com",
    "www.cvs.com",
    "cvs.com",
    "www.walgreens.com",
    "walgreens.com",

    # --- 14. Real Estate & Housing ---
    "www.zillow.com",
    "zillow.com",
    "www.redfin.com",
    "redfin.com",
    "www.realtor.com",
    "realtor.com",
    "www.trulia.com",
    "trulia.com",
    "www.apartments.com",
    "apartments.com",

    # --- 15. Telecom, Hardware & Automotive ---
    "www.cisco.com",
    "cisco.com",
    "www.samsung.com",
    "samsung.com",
    "www.dell.com",
    "dell.com",
    "www.hp.com",
    "hp.com",
    "www.lenovo.com",
    "lenovo.com",
    "www.intel.com",
    "intel.com",
    "www.amd.com",
    "amd.com",
    "www.nvidia.com",
    "nvidia.com",
    "www.qualcomm.com",
    "qualcomm.com",
    "www.tesla.com",
    "tesla.com",
    "www.ford.com",
    "ford.com",
    "www.gm.com",
    "gm.com",
    "www.bmw.com",
    "bmw.com",
    "www.mercedes-benz.com",
    "mercedes-benz.com",
    "www.toyota.com",
    "toyota.com"
]

def check_sni(sni_host):
    """Attempts a TLS handshake to TARGET_IP using a specific SNI hostname."""
    context = ssl.create_default_context()
    # Disable certificate verification so self-signed certs or domain mismatches don't throw false positives
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    payload = (
        f"GET / HTTP/1.1\r\n"
        f"Host: {sni_host}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
        f"Sec-WebSocket-Version: 13\r\n\r\n"
    ).encode('utf-8')

    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_sock.settimeout(TIMEOUT)

    try:
        # Step 1: Connect raw TCP to your server IP
        raw_sock.connect((TARGET_IP, TARGET_PORT))

        # Step 2: Wrap socket in SSL with the candidate SNI
        ssl_sock = context.wrap_socket(raw_sock, server_hostname=sni_host)

        # Step 3: Send WebSocket request payload
        ssl_sock.sendall(payload)

        # Step 4: Read initial response
        response = ssl_sock.recv(1024).decode('utf-8', errors='ignore')
        ssl_sock.close()

        if "101" in response or "200" in response:
            return (sni_host, "PASS", "HTTP 101/200 OK")
        elif len(response) > 0:
            return (sni_host, "PARTIAL", f"Got Response: {response.splitlines()[0]}")
        else:
            return (sni_host, "FAIL", "Empty response from server")

    except ConnectionResetError:
        return (sni_host, "BLOCKED (RST)", "DPI sent TCP Reset packet")
    except socket.timeout:
        return (sni_host, "BLOCKED (TIMEOUT)", "DPI silently dropped packets")
    except ssl.SSLError as e:
        return (sni_host, "SSL_ERROR", f"TLS Handshake failed: {e.reason}")
    except Exception as e:
        return (sni_host, "ERROR", str(e))

def main():
    print(f"[*] Starting SNI scan against {TARGET_IP}:{TARGET_PORT}...\n")

    with open(OUTPUT_FILE, 'w') as f_out:
        header_console = f"{'SNI Domain':<25} | {'Status':<20} | {'Details'}"
        header_file = f"{'SNI Domain':<25} | {'Status':<20} | {'Details'}"
        print(header_console)
        f_out.write(header_file + '\n')

        separator = "-" * 70
        print(separator)
        f_out.write(separator + '\n')

        working_snis = []

        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = {executor.submit(check_sni, sni): sni for sni in CANDIDATE_SNIS}
            for future in as_completed(futures):
                sni, status, details = future.result()
                result_line = f"{sni:<25} | {status:<20} | {details}"
                print(result_line)
                f_out.write(result_line + '\n')
                if status == "PASS":
                    working_snis.append(sni)

        footer_separator = "=" * 70
        print("\n" + footer_separator)
        f_out.write('\n' + footer_separator + '\n')

        summary_console = f"[+] Scan Complete. Found {len(working_snis)} passing SNI(s):"
        summary_file = f"[+] Scan Complete. Found {len(working_snis)} passing SNI(s):"
        print(summary_console)
        f_out.write(summary_file + '\n')

        for s in working_snis:
            print(f"  - {s}")
            f_out.write(f"  - {s}\n")

    print(f"\n[*] Results also saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()