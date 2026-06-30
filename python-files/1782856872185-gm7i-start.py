import urllib.request
import json

# === НАСТРОЙКИ ===
MCP_URL = "https://justrunmy.app/api/mcp"
MCP_TOKEN = "CfDJ8I6qJxyfn1BFmLYpveog23/vP4UcGEl3eGBjR4mM7gPcM2sAgOooxkm8pwCzLg4Iw0YdxBE9Qxn1R/mq8lrYaWAcg\u002B8wUCYiv3M6hcQioR2\u002BuGnzvUGKNtnGURHaiDIUxyQwuGWKqbrzBwE0PrEr0pxgDhu03b6MGx4GX6MI7M1YaESKd/FyJWz/rAv2GmoDO4Oy9g3td6SNN/4H1QUtHFgp06W/t5yBJbYmdb\u002BIadufsuui9\u002Bztn\u002Bs2nX\u002Bb6dS/SYTC3WezsgKFmOKu/DLBm\u002BsmqfvA22XjFdLV7\u002BNxbMqoUD93c\u002BDsp9ygHeHUvtjImLaMLuDTx2QMNvKB7VQKaDpp14Vi/frrWG8RevxCtCtrAQ0vvRF7vywt5sGGXPcY7IBurS29RzZ8trUrSTS8Bd2Os3oLhf/nlln1gA5sgf73zaxa4kwIZzVrEpXlidYQmhj4\u002BXSxU6Z9RcR\u002BBaRbivrmOOIKiShAWXa1zGH8Em1\u002BVdWRHPk4ZrUg10XFmjfCMfc7zvrMilxokIZ6uaKD4KyqCTLr21IG2JXg/kLplpiNc91yGU8LaL3yeNaf4wKLD\u002BNFgEi\u002ByW/dc7h9u3CU9fhHNjOowDFPBcSSRd5TY7CzzrWZFUZh92remaSpZ3XApZZsp2Z8OwdwS/4mS9SY/uPZfdzVlreITQ3ZsQcc3eZD9IJ9xaxtTY3PzC7tDsfo46DR6h5aVGhBvn37z7kirur85SonZOSYp1AZFpCsgZpXjK7\u002B8\u002BNIdvUG6SwEkFq4hbvYqVttNsObkQmfChRSoy3tHop/nb7sJyURIC58IZQBwHaHdbfJSEVdvlFvYq2mVd0UWccs\u002BOVWXcEqJv82LndhI9Ju6v9\u002BAOMdMxNpmj5/Umzksvfu8CyupsgWzG5Pbg=="  # значение X-User-Identity из mcp.json
APP_ID = "39124"

def call_mcp(method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        MCP_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "X-User-Identity": MCP_TOKEN
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def restart_app():
    print("Отправляю запрос на рестарт...")
    result = call_mcp("tools/call", {
        "name": "jrnm_restart_app",
        "arguments": {"app_id": APP_ID}
    })
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("Готово.")

if __name__ == "__main__":
    restart_app()