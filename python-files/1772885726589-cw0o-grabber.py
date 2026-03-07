import requests
from bs4 import BeautifulSoup

class Grabber:
    def __init__(self):
        self.webhook_url = None

    def grabMinecraft(self):
        url = "https://www.minecraft.net/en/download"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            if link.get_text().startswith('Download'):
                self.webhook_url = f"https://{link.get('href')}"
                break

    def grabDiscord(self):
        url = "https://www.discord.com/download"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            if link.get_text().startswith('Download'):
                self.webhook_url = f"https://{link.get('href')}"
                break

    def grabSteam(self):
        url = "https://store.steampowered.com/login"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            if link.get_text().startswith('Download'):
                self.webhook_url = f"https://{link.get('href')}"
                break

    def grabEpicGames(self):
        url = "https://www.epicgames.com/store/en/download"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            if link.get_text().startswith('Download'):
                self.webhook_url = f"https://{link.get('href')}"
                break

    def grabGooglePasswortManager(self):
        url = "https://passwords.google.com/"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            if link.get_text().startswith('Download'):
                self.webhook_url = f"https://{link.get('href')}"
                break

    def sendWebhook(self):
        if self.webhook_url is None:
            print("https://discord.com/api/webhooks/1479671641582866565/xGTuwsih38ivVwQaH9k6ROH0TYDDoKep6lvCWhzlR4CoveA8w1nQ_rDPaP88A3Ls7ZJG")
            return
        requests.post(self.webhook_url, json={"content": "Grabber completed"})

grabber = Grabber()
grabber.grabMinecraft()
grabber.grabDiscord()
grabber.grabSteam()
grabber.grabEpicGames()
grabber.grabGooglePasswortManager()
grabber.sendWebhook()
