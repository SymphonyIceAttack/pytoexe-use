import discord
import asyncio
import os
import sys
import time
from threading import Thread

# ============================================================
# COULEURS VIOLET AVEC EFFETS
# ============================================================
VIOLET_FONCE = "\033[38;2;75;0;130m"      
VIOLET_MOYEN = "\033[38;2;106;13;173m"    
VIOLET = "\033[38;2;138;43;226m"          
VIOLET_CLAIR = "\033[38;2;156;81;236m"    
VIOLET_TRES_CLAIR = "\033[38;2;179;118;255m"  
VIOLET_NEON = "\033[38;2;190;90;255m"     
BLANC = "\033[38;2;255;255;255m"
BLANC_GRIS = "\033[38;2;200;200;200m"
ROSE = "\033[38;2;255;85;255m"
VERT = "\033[38;2;0;255;150m"
OR = "\033[38;2;255;215;0m"

# Effets
GRAS = "\033[1m"
SOULIGNE = "\033[4m"
CLIGNOTE = "\033[5m"
INVERSE = "\033[7m"
RESET = "\033[0m"

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def effet_pulse(text, delay=0.05):
    """Effet de pulsation pour le texte"""
    colors = [VIOLET_FONCE, VIOLET_MOYEN, VIOLET, VIOLET_CLAIR, VIOLET_TRES_CLAIR, VIOLET_NEON, VIOLET_TRES_CLAIR, VIOLET_CLAIR, VIOLET, VIOLET_MOYEN, VIOLET_FONCE]
    result = ""
    for i, char in enumerate(text):
        color = colors[i % len(colors)]
        result += f"{color}{GRAS}{char}{RESET}"
    return result

def effet_rainbow_violet(text):
    """Effet arc-en-ciel violet qui bouge"""
    colors = [VIOLET_FONCE, VIOLET_MOYEN, VIOLET, VIOLET_CLAIR, VIOLET_TRES_CLAIR, VIOLET_NEON, VIOLET_TRES_CLAIR, VIOLET_CLAIR, VIOLET, VIOLET_MOYEN]
    result = ""
    for i, char in enumerate(text):
        color = colors[i % len(colors)]
        result += f"{color}{GRAS}{char}{RESET}"
    return result

def gradient_move(text, offset=0):
    """Gradient qui se déplace"""
    colors = [VIOLET_FONCE, VIOLET_MOYEN, VIOLET, VIOLET_CLAIR, VIOLET_TRES_CLAIR, VIOLET_NEON]
    result = ""
    for i, char in enumerate(text):
        color = colors[(i + offset) % len(colors)]
        result += f"{color}{GRAS}{char}{RESET}"
    return result

def print_animated_banner():
    """Affiche le banner avec animation"""
    banner_lines = [
        "██████╗ ███╗   ███╗ █████╗ ██╗     ██╗     ",
        "██╔══██╗████╗ ████║██╔══██╗██║     ██║     ",
        "██║  ██║██╔████╔██║███████║██║     ██║     ",
        "██║  ██║██║╚██╔╝██║██╔══██║██║     ██║     ",
        "██████╔╝██║ ╚═╝ ██║██║  ██║███████╗███████╗",
        "╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝",
        "                                            ",
        "         D M   A L L   T O O L               ",
        "              BY     KAIRO              "
    ]
    
    print()
    for i, line in enumerate(banner_lines):
        # Effet de dégradé qui bouge
        animated_line = gradient_move(line, i)
        print(f"{animated_line}{RESET}")
        time.sleep(0.03)
    print()

def loading_animation(message, duration=1.5):
    """Animation de chargement"""
    chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    for _ in range(int(duration * 10)):
        for char in chars:
            sys.stdout.write(f"\r{VIOLET_CLAIR}{char} {message}{RESET}")
            sys.stdout.flush()
            time.sleep(0.05)
    sys.stdout.write("\r" + " " * 50 + "\r")

class DMAllTool:
    def __init__(self):
        self.client = None
        self.token = None
        self.amis = []
        self.total = 0
        self.envoyes = 0
        self.erreurs = 0
        
    def print_stylish_box(self, title, content, color=VIOLET_CLAIR):
        """Affiche une boîte stylée"""
        print(f"{color}╔{'═' * 54}╗{RESET}")
        print(f"{color}║{RESET} {GRAS}{VIOLET_TRES_CLAIR}{title:^50}{RESET} {color}║{RESET}")
        print(f"{color}╠{'═' * 54}╣{RESET}")
        print(f"{color}║{RESET} {content:^50} {color}║{RESET}")
        print(f"{color}╚{'═' * 54}╝{RESET}")
    
    async def demander_token_anim(self):
        """Demande le token avec animation"""
        clear()
        print_animated_banner()
        
        self.print_stylish_box("🔐 AUTHENTIFICATION", "Entre ton token Discord", VIOLET_MOYEN)
        print()
        
        # Animation de pulsation
        for _ in range(3):
            sys.stdout.write(f"\r{VIOLET_NEON}{GRAS}⚡ TOKEN REQUIS ⚡{RESET}")
            sys.stdout.flush()
            time.sleep(0.3)
            sys.stdout.write(f"\r{VIOLET_FONCE}{GRAS}⚡ TOKEN REQUIS ⚡{RESET}")
            sys.stdout.flush()
            time.sleep(0.3)
        
        print()
        print()
        self.token = input(f"{VIOLET_TRES_CLAIR}{GRAS}➜ {RESET}{BLANC}Token : {RESET}").strip()
        return self.token
    
    async def verifier_token(self):
        """Vérifie le token avec animation"""
        self.client = discord.Client()
        token_valide = False
        
        loading_animation("Vérification du token...", 1)
        
        @self.client.event
        async def on_ready():
            nonlocal token_valide
            token_valide = True
            print(f"\n{VERT}{GRAS}✅ TOKEN ACCEPTÉ !{RESET}")
            print(f"{VIOLET_MOYEN}📱 Connecté : {VIOLET_TRES_CLAIR}{GRAS}{self.client.user}{RESET}\n")
            await asyncio.sleep(1)
            await self.client.close()
        
        try:
            await self.client.start(self.token)
            await self.client.wait_until_ready()
        except:
            token_valide = False
        finally:
            if not token_valide:
                print(f"\n{ROSE}{GRAS}❌ TOKEN INVALIDE !{RESET}")
                for _ in range(3):
                    sys.stdout.write(f"\r{ROSE}⚠️  Vérifie ton token et réessaye ⚠️{RESET}")
                    sys.stdout.flush()
                    time.sleep(0.3)
                    sys.stdout.write(f"\r{VIOLET_FONCE}⚠️  Vérifie ton token et réessaye ⚠️{RESET}")
                    sys.stdout.flush()
                    time.sleep(0.3)
                print()
                await asyncio.sleep(1)
            await self.client.close()
            self.client = None
        
        return token_valide
    
    async def get_friends_anim(self):
        """Récupère les amis avec animation"""
        self.client = discord.Client()
        
        @self.client.event
        async def on_ready():
            print(f"{VIOLET_CLAIR}{GRAS}🔍 Récupération de la liste des amis...{RESET}")
            
            # Animation de chargement
            chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
            for i in range(20):
                sys.stdout.write(f"\r{VIOLET_NEON}{chars[i % len(chars)]} Scanning...{RESET}")
                sys.stdout.flush()
                await asyncio.sleep(0.05)
            
            relations = await self.client.http.get_relationships()
            self.amis = [r for r in relations if r.get('type') == 1]
            self.total = len(self.amis)
            
            print(f"\n\n{VERT}{GRAS}✅ {self.total} AMIS TROUVÉS !{RESET}\n")
            await self.client.close()
        
        await self.client.start(self.token)
        await self.client.wait_until_ready()
        await self.client.close()
        self.client = None
        
        return self.amis
    
    def show_friends_preview(self):
        """Affiche un aperçu stylé des amis"""
        print(f"{VIOLET_TRES_CLAIR}{GRAS}📋 APERÇU DES AMIS{RESET}")
        print(f"{VIOLET_MOYEN}{'─' * 50}{RESET}")
        
        for i, ami in enumerate(self.amis[:8]):
            user = ami.get('user', {})
            name = user.get('username', 'inconnu')
            # Effet gradient sur les noms
            colored_name = gradient_move(name, i)
            print(f"{VIOLET_CLAIR}{i+1:2}.{RESET} {colored_name}")
        
        if self.total > 8:
            print(f"{VIOLET_FONCE}   ... et {self.total - 8} autres amis{RESET}")
        print(f"{VIOLET_MOYEN}{'─' * 50}{RESET}\n")
    
    async def send_messages_anim(self, message):
        """Envoie les messages avec animation stylée"""
        self.client = discord.Client()
        self.envoyes = 0
        self.erreurs = 0
        
        @self.client.event
        async def on_ready():
            print(f"\n{VIOLET_NEON}{GRAS}🚀 LANCEMENT DE L'ENVOI...{RESET}\n")
            print(f"{VIOLET_MOYEN}{'═' * 60}{RESET}\n")
            
            # Animation de démarrage
            for i in range(3):
                sys.stdout.write(f"\r{VIOLET_CLAIR}⚡ Initialisation{'.' * (i+1)}{RESET}")
                sys.stdout.flush()
                await asyncio.sleep(0.3)
            print("\n")
            
            for i, ami in enumerate(self.amis, 1):
                try:
                    user_id = ami['id']
                    user = await self.client.fetch_user(user_id)
                    await user.send(message)
                    self.envoyes += 1
                    
                    # Barre de progression avec effet gradient
                    pourcentage = int((self.envoyes / self.total) * 40)
                    
                    # Effet gradient sur la barre
                    barre = ""
                    for j in range(pourcentage):
                        color = [VIOLET_FONCE, VIOLET_MOYEN, VIOLET, VIOLET_CLAIR, VIOLET_TRES_CLAIR][j % 5]
                        barre += f"{color}█{RESET}"
                    barre += f"{VIOLET_FONCE}{'░' * (40 - pourcentage)}{RESET}"
                    
                    # Affichage principal avec effets
                    compteur = f"{VIOLET_NEON}{GRAS}[{barre}]{RESET}"
                    progress = f"{VIOLET_TRES_CLAIR}{GRAS}{self.envoyes}/{self.total}{RESET}"
                    nom = f"{VIOLET_CLAIR}{gradient_move(user.name, self.envoyes)}{RESET}"
                    
                    sys.stdout.write(f"\r{compteur} {progress} {VIOLET_MOYEN}➜{RESET} {nom}     ")
                    sys.stdout.flush()
                    
                    await asyncio.sleep(2)
                    
                except discord.Forbidden:
                    self.erreurs += 1
                    sys.stdout.write(f"\r{VIOLET_FONCE}[{'░' * 40}]{RESET} {ROSE}{self.envoyes}/{self.total} ➜ BLOQUÉ{RESET}     ")
                    sys.stdout.flush()
                    
                except Exception as e:
                    self.erreurs += 1
                    sys.stdout.write(f"\r{VIOLET_FONCE}[{'░' * 40}]{RESET} {ROSE}{self.envoyes}/{self.total} ➜ ERREUR{RESET}     ")
                    sys.stdout.flush()
            
            print("\n\n")
            print(f"{VIOLET_MOYEN}{'═' * 60}{RESET}")
            
            # Stats finales avec effet
            taux = (self.envoyes/self.total*100) if self.total > 0 else 0
            
            print(f"\n{VIOLET_NEON}{GRAS}📊 RÉSULTAT FINAL{RESET}")
            print(f"{VIOLET_MOYEN}┌{'─' * 44}┐{RESET}")
            print(f"{VIOLET_MOYEN}│{RESET} {VERT}✅ Envoyés   : {GRAS}{self.envoyes}/{self.total}{RESET}                    {VIOLET_MOYEN}│{RESET}")
            print(f"{VIOLET_MOYEN}│{RESET} {ROSE}❌ Échecs     : {self.erreurs}{RESET}                        {VIOLET_MOYEN}│{RESET}")
            print(f"{VIOLET_MOYEN}│{RESET} {VIOLET_TRES_CLAIR}📈 Taux succès: {taux:.1f}%{RESET}                       {VIOLET_MOYEN}│{RESET}")
            
            # Petite animation de réussite
            if taux > 80:
                print(f"{VIOLET_MOYEN}│{RESET} {OR}🏆 Performance : EXCELLENT{RESET}                 {VIOLET_MOYEN}│{RESET}")
            elif taux > 50:
                print(f"{VIOLET_MOYEN}│{RESET} {VIOLET_CLAIR}👍 Performance : BON{RESET}                       {VIOLET_MOYEN}│{RESET}")
            
            print(f"{VIOLET_MOYEN}└{'─' * 44}┘{RESET}\n")
            
            await self.client.close()
        
        await self.client.start(self.token)
        await self.client.wait_until_ready()
        await self.client.close()
        self.client = None
    
    async def run(self):
        """Lance le tool avec animations"""
        # Demande token avec animation
        token_valide = False
        while not token_valide:
            await self.demander_token_anim()
            token_valide = await self.verifier_token()
            if not token_valide:
                continue
        
        # Récupération amis avec animation
        await self.get_friends_anim()
        
        if self.total == 0:
            print(f"{ROSE}❌ Aucun ami trouvé !{RESET}")
            input(f"\n{VIOLET_FONCE}Appuie sur Entrée pour quitter...{RESET}")
            return
        
        # Aperçu des amis
        self.show_friends_preview()
        
        # Demande du message avec effet
        print(f"{VIOLET_TRES_CLAIR}{GRAS}💬 ÉCRIS TON MESSAGE{RESET}")
        print(f"{VIOLET_MOYEN}{'─' * 50}{RESET}")
        print(f"{BLANC_GRIS}➜ Message pour {GRAS}{self.total}{RESET}{BLANC_GRIS} ami(s){RESET}")
        print()
        
        message = input(f"{VIOLET_NEON}{GRAS}✍️  {RESET}{BLANC}Message : {RESET}").strip()
        
        if not message:
            print(f"\n{ROSE}❌ Message vide !{RESET}")
            input(f"\n{VIOLET_FONCE}Appuie sur Entrée pour quitter...{RESET}")
            return
        
        # Confirmation finale avec animation
        clear()
        print_animated_banner()
        
        print(f"\n{VIOLET_NEON}{GRAS}{CLIGNOTE}⚠️  CONFIRMATION FINALE  ⚠️{RESET}\n")
        print(f"{VIOLET_MOYEN}┌{'─' * 54}┐{RESET}")
        print(f"{VIOLET_MOYEN}│{RESET} {BLANC}📨 Message   : {VIOLET_TRES_CLAIR}{message[:45]}{RESET}{'...' if len(message) > 45 else ''}{' ' * (45 - min(45, len(message)))}{VIOLET_MOYEN}│{RESET}")
        print(f"{VIOLET_MOYEN}│{RESET} {BLANC}👥 Amis      : {VIOLET_TRES_CLAIR}{GRAS}{self.total}{RESET}{BLANC} destinataire(s){' ' * 30}{VIOLET_MOYEN}│{RESET}")
        print(f"{VIOLET_MOYEN}│{RESET} {BLANC}⏱️  Délai      : {VIOLET_CLAIR}2 secondes{RESET} entre chaque message{' ' * 20}{VIOLET_MOYEN}│{RESET}")
        print(f"{VIOLET_MOYEN}└{'─' * 54}┘{RESET}")
        
        print()
        print(f"{ROSE}{GRAS}{CLIGNOTE}⚠️  CETTE ACTION EST IRRÉVERSIBLE  ⚠️{RESET}\n")
        
        confirm = input(f"{VIOLET_NEON}{GRAS}➜ TAPE 'OUI' POUR CONFIRMER : {RESET}").strip().upper()
        
        if confirm == "OUI":
            # Animation de confirmation
            loading_animation("Préparation de l'envoi...", 1)
            await self.send_messages_anim(message)
        else:
            print(f"\n{ROSE}❌ ENVOI ANNULÉ !{RESET}")
            for _ in range(5):
                sys.stdout.write(f"\r{VIOLET_FONCE}Annulation{'.' * (_ % 4)}{' ' * 5}{RESET}")
                sys.stdout.flush()
                time.sleep(0.2)
            print()
        
        print(f"\n{VIOLET_TRES_CLAIR}{GRAS}👋 Merci d'avoir utilisé DMALL Tool !{RESET}")
        input(f"\n{VIOLET_FONCE}Appuie sur Entrée pour quitter...{RESET}")

# ============================================================
# LANCEMENT
# ============================================================
async def main():
    tool = DMAllTool()
    await tool.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{ROSE}⚠️  Arrêté par l'utilisateur{RESET}")
        time.sleep(1)
    except Exception as e:
        print(f"\n{ROSE}❌ Erreur: {e}{RESET}")
        input(f"\n{VIOLET_FONCE}Appuie sur Entrée pour quitter...{RESET}")