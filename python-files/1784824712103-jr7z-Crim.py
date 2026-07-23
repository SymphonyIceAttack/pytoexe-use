import math
import random

# Database
DATA = {
    "Firearms": {
        "Beretta": {"Type": "Pistol", "Price": 200, "Refill price": 180, "Slots": 3, "Damage": 17, "Limb damage": 31.45, "Headshot damage": 23, "Firerate": 3.7, "Recoil control": 18, "Armor penetration": 0.45, "Max damage range": 1250, "Mobility": 16, "Reload time": 2.25, "Ammo in magazine": 12, "Ammo": 48},
        "G-17": {"Type": "Pistol", "Price": 250, "Refill price": 150, "Slots": 3, "Damage": 21, "Limb damage": 38.85, "Headshot damage": 29, "Firerate": 5, "Recoil control": 21, "Armor penetration": 0.353, "Max damage range": 2000, "Mobility": 16, "Reload time": 2.25, "Ammo in magazine": 14, "Ammo": 56},
        "TEC-9": {"Type": "Pistol", "Price": 350, "Refill price": 220, "Slots": 3, "Damage": 18, "Limb damage": 33.3, "Headshot damage": 26, "Firerate": 2.5, "Recoil control": 19, "Armor penetration": 0.33, "Max damage range": 1550, "Mobility": 15, "Reload time": 3, "Ammo in magazine": 18, "Ammo": 72},
        "M1911": {"Type": "Pistol", "Price": 450, "Refill price": 200, "Slots": 3, "Damage": 29, "Limb damage": 53.65, "Headshot damage": 43, "Firerate": 4.5, "Recoil control": 26, "Armor penetration": 0.42, "Max damage range": 2550, "Mobility": 16, "Reload time": 2.5, "Ammo in magazine": 8, "Ammo": 32},
        "FNP-45": {"Type": "Pistol", "Price": 800, "Refill price": 250, "Slots": 3.5, "Damage": 26, "Limb damage": 48.1, "Headshot damage": 37, "Firerate": 5.1, "Recoil control": 20, "Armor penetration": 0.55, "Max damage range": 2100, "Mobility": 16, "Reload time": 2.25, "Ammo in magazine": 12, "Ammo": 48},
        "Deagle": {"Type": "Pistol", "Price": 900, "Refill price": 250, "Slots": 3.5, "Damage": 37, "Limb damage": 68.45, "Headshot damage": 58, "Firerate": 2.5, "Recoil control": 45, "Armor penetration": 0.57, "Max damage range": 3150, "Mobility": 14.5, "Reload time": 3, "Ammo in magazine": 7, "Ammo": 28},
        "Magnum": {"Type": "Pistol", "Price": 1200, "Refill price": 450, "Slots": 3.5, "Damage": 51, "Limb damage": 94.35, "Headshot damage": 102, "Firerate": 2, "Recoil control": 55, "Armor penetration": 0.52, "Max damage range": 4150, "Mobility": 14.75, "Reload time": 3, "Ammo in magazine": 6, "Ammo": 24},
        "G-18": {"Type": "Pistol", "Price": 1050, "Refill price": 250, "Slots": 3, "Damage": 18, "Limb damage": 33.3, "Headshot damage": 26, "Firerate": 13, "Recoil control": 21, "Armor penetration": 0.41, "Max damage range": 1550, "Mobility": 16, "Reload time": 2.25, "Ammo in magazine": 20, "Ammo": 60},
        "Hawkeye": {"Type": "Pistol", "Price": 1200, "Refill price": 300, "Slots": 3.5, "Damage": 101, "Limb damage": 186.85, "Headshot damage": 202, "Firerate": 5, "Recoil control": 2, "Armor penetration": 0.95, "Max damage range": 99999, "Mobility": 14.75, "Reload time": 3, "Ammo in magazine": 1, "Ammo": 2},
        "Uzi": {"Type": "Smg", "Price": 400, "Refill price": 250, "Slots": 4, "Damage": 16, "Limb damage": 29.6, "Headshot damage": 23, "Firerate": 8.2, "Recoil control": 21, "Armor penetration": 0.37, "Max damage range": 1500, "Mobility": 14.5, "Reload time": 3, "Ammo in magazine": 25, "Ammo": 100},
        "MAC-10": {"Type": "Smg", "Price": 1100, "Refill price": 300, "Slots": 4, "Damage": 15, "Limb damage": 27.75, "Headshot damage": 21, "Firerate": 13, "Recoil control": 18, "Armor penetration": 0.51, "Max damage range": 1450, "Mobility": 14.5, "Reload time": 3, "Ammo in magazine": 25, "Ammo": 100},
        "MP7": {"Type": "Smg", "Price": 1700, "Refill price": 300, "Slots": 4.5, "Damage": 16, "Limb damage": 29.6, "Headshot damage": 23, "Firerate": 12, "Recoil control": 17, "Armor penetration": 0.6, "Max damage range": 1500, "Mobility": 14.5, "Reload time": 3, "Ammo in magazine": 25, "Ammo": 100},
        "UMP-45": {"Type": "Smg", "Price": 1900, "Refill price": 100, "Slots": 4.5, "Damage": 23, "Limb damage": 42.55, "Headshot damage": 34, "Firerate": 6.6, "Recoil control": 19, "Armor penetration": 0.66, "Max damage range": 2050, "Mobility": 14, "Reload time": 3.25, "Ammo in magazine": 25, "Ammo": 100},
        "Tommy Gun": {"Type": "Smg", "Price": 1300, "Refill price": 350, "Slots": 5, "Damage": 17, "Limb damage": 31.45, "Headshot damage": 24, "Firerate": 9.2, "Recoil control": 17, "Armor penetration": 0.57, "Max damage range": 1850, "Mobility": 14, "Reload time": 4, "Ammo in magazine": 50, "Ammo": 150},
        "MP5": {"Type": "Smg", "Price": 1800, "Refill price": 150, "Slots": 4.5, "Damage": 19, "Limb damage": 35.15, "Headshot damage": 26.6, "Firerate": 9.3, "Recoil control": 18, "Armor penetration": 0.6, "Max damage range": 1650, "Mobility": 14.15, "Reload time": 3.25, "Ammo in magazine": 25, "Ammo": 100},
        "Sawn-Off": {"Type": "Shotgun", "Price": 175, "Refill price": 150, "Slots": 3.5, "Damage": 96, "Limb damage": 177.6, "Headshot damage": 136, "Firerate": 2, "Recoil control": 45, "Armor penetration": 0.15, "Max damage range": 11, "Mobility": 14.75, "Reload time": 2.5, "Ammo in magazine": 2, "Ammo": 10},
        "Super-Shorty": {"Type": "Shotgun", "Price": 850, "Refill price": 200, "Slots": 3.5, "Damage": 112, "Limb damage": 207.2, "Headshot damage": 152, "Firerate": 0.9, "Recoil control": 35, "Armor penetration": 0.2, "Max damage range": 15, "Mobility": 14.5, "Reload time": 3, "Ammo in magazine": 3, "Ammo": 15},
        "Ithaca-37": {"Type": "Shotgun", "Price": 750, "Refill price": 250, "Slots": 5, "Damage": 120, "Limb damage": 222, "Headshot damage": 152, "Firerate": 0.8, "Recoil control": 60, "Armor penetration": 0.2, "Max damage range": 20, "Mobility": 14, "Reload time": 6.25, "Ammo in magazine": 5, "Ammo": 25},
        "UTS-15": {"Type": "Shotgun", "Price": 25000, "Refill price": 99999, "Slots": 7, "Damage": 217, "Limb damage": 401.45, "Headshot damage": 217, "Firerate": 1.2, "Recoil control": 78.26, "Armor penetration": 0.525, "Max damage range": 450, "Mobility": 12, "Reload time": 11.25, "Ammo in magazine": 15, "Ammo": 60},
        "AKS-74U": {"Type": "AR", "Price": 1750, "Refill price": 300, "Slots": 5.5, "Damage": 24, "Limb damage": 44.4, "Headshot damage": 36, "Firerate": 7, "Recoil control": 21, "Armor penetration": 0.68, "Max damage range": 2050, "Mobility": 13, "Reload time": 3.5, "Ammo in magazine": 30, "Ammo": 120},
        "M4A1": {"Type": "AR", "Price": 3100, "Refill price": 350, "Slots": 6, "Damage": 21, "Limb damage": 38.85, "Headshot damage": 31, "Firerate": 8.5, "Recoil control": 19, "Armor penetration": 0.7, "Max damage range": 3950, "Mobility": 14, "Reload time": 3, "Ammo in magazine": 30, "Ammo": 120},
        "SCAR-H": {"Type": "AR", "Price": 3500, "Refill price": 300, "Slots": 6, "Damage": 31, "Limb damage": 57.35, "Headshot damage": 47, "Firerate": 6.5, "Recoil control": 23, "Armor penetration": 0.72, "Max damage range": 3000, "Mobility": 12.75, "Reload time": 3.5, "Ammo in magazine": 20, "Ammo": 80},
        "AKM": {"Type": "AR", "Price": 5600, "Refill price": 350, "Slots": 6.5, "Damage": 29, "Limb damage": 53.65, "Headshot damage": 44, "Firerate": 7, "Recoil control": 24, "Armor penetration": 0.8, "Max damage range": 4400, "Mobility": 12.7, "Reload time": 3.85, "Ammo in magazine": 30, "Ammo": 120},
        "SKS": {"Type": "DMR", "Price": 650, "Refill price": 250, "Slots": 6.5, "Damage": 29, "Limb damage": 53.65, "Headshot damage": 44, "Firerate": 4.5, "Recoil control": 21, "Armor penetration": 0.73, "Max damage range": 2900, "Mobility": 12.7, "Reload time": 4, "Ammo in magazine": 10, "Ammo": 40},
        "FN-FAL": {"Type": "DMR", "Price": 3300, "Refill price": 400, "Slots": 6.5, "Damage": 37, "Limb damage": 68.45, "Headshot damage": 60, "Firerate": 4, "Recoil control": 23, "Armor penetration": 0.8, "Max damage range": 4700, "Mobility": 12.75, "Reload time": 3.5, "Ammo in magazine": 20, "Ammo": 80},
        "M60": {"Type": "LMG", "Price": 7000, "Refill price": 1500, "Slots": 7.5, "Damage": 23, "Limb damage": 42.55, "Headshot damage": 35, "Firerate": 7.7, "Recoil control": 25, "Armor penetration": 0.85, "Max damage range": 4100, "Mobility": 11, "Reload time": 8, "Ammo in magazine": 100, "Ammo": 200},
        "Mare": {"Type": "Sniper Rifle", "Price": 4000, "Refill price": 400, "Slots": 5, "Damage": 60, "Limb damage": 111, "Headshot damage": 120, "Firerate": 1, "Recoil control": 65, "Armor penetration": 0.8, "Max damage range": 4250, "Mobility": 14, "Reload time": 3.6, "Ammo in magazine": 6, "Ammo": 24},
        "Scout": {"Type": "Sniper Rifle", "Price": 6000, "Refill price": 600, "Slots": 6.5, "Damage": 52, "Limb damage": 96.2, "Headshot damage": 121, "Firerate": 0.7, "Recoil control": 55, "Armor penetration": 0.8, "Max damage range": 6350, "Mobility": 14, "Reload time": 4.5, "Ammo in magazine": 10, "Ammo": 30},
        "Savage": {"Type": "Sniper Rifle", "Price": 9000, "Refill price": 800, "Slots": 7, "Damage": 75, "Limb damage": 138.75, "Headshot damage": 150, "Firerate": 0.6, "Recoil control": 77, "Armor penetration": 0.8, "Max damage range": 12300, "Mobility": 13.25, "Reload time": 3.75, "Ammo in magazine": 5, "Ammo": 20},
        "BFG": {"Type": "Sniper Rifle", "Price": 18000, "Refill price": 1400, "Slots": 8, "Damage": 130, "Limb damage": 240.5, "Headshot damage": 130, "Firerate": 1, "Recoil control": 125, "Armor penetration": 0.99, "Max damage range": 27300, "Mobility": 11, "Reload time": 4.5, "Ammo in magazine": 1, "Ammo": 5},
        "Firework Launcher": {"Type": "Launcher", "Price": 1776, "Refill price": 500, "Slots": 7.5, "Damage": 60, "Limb damage": None, "Headshot damage": 60, "Firerate": 1, "Recoil control": 40, "Armor penetration": 1, "Max damage range": 99999, "Mobility": 13, "Reload time": 4, "Ammo in magazine": 1, "Ammo": 3},
        "M320": {"Type": "Launcher", "Price": 8000, "Refill price": 850, "Slots": 4.5, "Damage": 115, "Limb damage": None, "Headshot damage": 175, "Firerate": 1.5, "Recoil control": 20, "Armor penetration": 1, "Max damage range": 5000, "Mobility": 15, "Reload time": 3.5, "Ammo in magazine": 1, "Ammo": 6},
        "RPG": {"Type": "Launcher", "Price": 12000, "Refill price": 1000, "Slots": 8, "Damage": 185, "Limb damage": None, "Headshot damage": 185, "Firerate": 1, "Recoil control": 80, "Armor penetration": 1, "Max damage range": 99999, "Mobility": 12, "Reload time": 6, "Ammo in magazine": 1, "Ammo": 3},
        "AT4": {"Type": "Launcher", "Price": 7500, "Refill price": 0, "Slots": 6, "Damage": 230, "Limb damage": None, "Headshot damage": 230, "Firerate": 1, "Recoil control": 80, "Armor penetration": 1, "Max damage range": 99999, "Mobility": 12, "Reload time": 0, "Ammo in magazine": 1, "Ammo": 1},
        "Musket": {"Type": "Muzzle-Loading Rifle", "Price": 2990, "Refill price": 300, "Slots": 7, "Damage": 102, "Limb damage": 188.7, "Headshot damage": 138, "Firerate": 1, "Recoil control": 55, "Armor penetration": 0.99, "Max damage range": 2600, "Mobility": 11, "Reload time": 7, "Ammo in magazine": 1, "Ammo": 6}
    },
    "Melees": {
        "Wrench": {"Type": "Blunt", "Price": 20, "Slots": 1.5, "Damage": 23, "Bleeding Damage": 0, "Stamina": 3, "Attack Cooldown": 0.6, "Attack Delay": 0.2, "Attack time": 0.1, "Stun time": 0.3, "Mobility": 8, "Can block": 0, "Effects can inflict": 2, "Can dismember/break neck": False, "Limb damage": 25, "Limb damage (head)": 20},
        "Crowbar": {"Type": "Blunt", "Price": 50, "Slots": 3.5, "Damage": 34, "Bleeding Damage": 0, "Stamina": 15, "Attack Cooldown": 1.2, "Attack Delay": 0.3, "Attack time": 0.2, "Stun time": 0.5, "Mobility": 7, "Can block": 0, "Effects can inflict": 2, "Can dismember/break neck": True, "Limb damage": 55, "Limb damage (head)": 37},
        "Golf Club": {"Type": "Blunt", "Price": 55, "Slots": 4, "Damage": 39, "Bleeding Damage": 0, "Stamina": 9, "Attack Cooldown": 1.2, "Attack Delay": 0.3, "Attack time": 0.2, "Stun time": 0.5, "Mobility": 7, "Can block": 0, "Effects can inflict": 2, "Can dismember/break neck": True, "Limb damage": 85, "Limb damage (head)": 45},
        "Shovel": {"Type": "Blunt", "Price": 60, "Slots": 4, "Damage": 60, "Bleeding Damage": 0, "Stamina": 14, "Attack Cooldown": 2.5, "Attack Delay": 0.5, "Attack time": 0.3, "Stun time": 0, "Mobility": 6.5, "Can block": 0, "Effects can inflict": 2, "Can dismember/break neck": True, "Limb damage": 100, "Limb damage (head)": 40},
        "Bat": {"Type": "Blunt", "Price": 65, "Slots": 4, "Damage": 34, "Bleeding Damage": 0, "Stamina": 8, "Attack Cooldown": 1.2, "Attack Delay": 0.4, "Attack time": 0.2, "Stun time": 0.4, "Mobility": 6.5, "Can block": 13, "Effects can inflict": 2, "Can dismember/break neck": True, "Limb damage": 55, "Limb damage (head)": 40},
        "Baton": {"Type": "Blunt", "Price": 160, "Slots": 2, "Damage": 18, "Bleeding Damage": 0, "Stamina": 4, "Attack Cooldown": 0.5, "Attack Delay": 0.1, "Attack time": 0.1, "Stun time": 0.3, "Mobility": 8, "Can block": 5, "Effects can inflict": 2, "Can dismember/break neck": True, "Limb damage": 35, "Limb damage (head)": 25},
        "Metal bat": {"Type": "Blunt", "Price": 325, "Slots": 4, "Damage": 39, "Bleeding Damage": 5, "Stamina": 11, "Attack Cooldown": 1.3, "Attack Delay": 0.5, "Attack time": 0.2, "Stun time": 0.5, "Mobility": 6.5, "Can block": 22, "Effects can inflict": 3, "Can dismember/break neck": True, "Limb damage": 100, "Limb damage (head)": 60},
        "Sledgehammer": {"Type": "Blunt", "Price": 375, "Slots": 6, "Damage": 70, "Bleeding Damage": 5, "Stamina": 15, "Attack Cooldown": 2.2, "Attack Delay": 0.7, "Attack time": 0.3, "Stun time": 0.6, "Mobility": 5.65, "Can block": 22, "Effects can inflict": 3, "Can dismember/break neck": True, "Limb damage": 125, "Limb damage (head)": 125},
        "Candy Crowbar": {"Type": "Blunt", "Price": 999, "Slots": 6, "Damage": 60, "Bleeding Damage": 0, "Stamina": 14, "Attack Cooldown": 2.5, "Attack Delay": 0.5, "Attack time": 0.3, "Stun time": 0, "Mobility": 7, "Can block": 0, "Effects can inflict": 2, "Can dismember/break neck": True, "Limb damage": 100, "Limb damage (head)": 40},
        "Shiv": {"Type": "Blade", "Price": 10, "Slots": 0.5, "Damage": 18, "Bleeding Damage": 8, "Stamina": 1, "Attack Cooldown": 0.5, "Attack Delay": 0.1, "Attack time": 0.1, "Stun time": 0.3, "Mobility": 8, "Can block": 0, "Effects can inflict": 2, "Can dismember/break neck": False, "Limb damage": 17, "Limb damage (head)": 12},
        "Bayonet": {"Type": "Blade", "Price": 35, "Slots": 1.5, "Damage": 24, "Bleeding Damage": 5, "Stamina": 4, "Attack Cooldown": 0.6, "Attack Delay": 0.2, "Attack time": 0.1, "Stun time": 0.2, "Mobility": 8, "Can block": 0, "Effects can inflict": 2, "Can dismember/break neck": False, "Limb damage": 21, "Limb damage (head)": 12},
        "Taiga": {"Type": "Blade", "Price": 80, "Slots": 3, "Damage": 27, "Bleeding Damage": 7, "Stamina": 6, "Attack Cooldown": 0.7, "Attack Delay": 0.2, "Attack time": 0.1, "Stun time": 0.3, "Mobility": 8, "Can block": 16, "Effects can inflict": 3, "Can dismember/break neck": True, "Limb damage": 35, "Limb damage (head)": 35},
        "Balisong": {"Type": "Blade", "Price": 70, "Slots": 1, "Damage": 18, "Bleeding Damage": 6, "Stamina": 3, "Attack Cooldown": 0.3, "Attack Delay": 0, "Attack time": 0.1, "Stun time": 0.2, "Mobility": 8, "Can block": 0, "Effects can inflict": 2, "Can dismember/break neck": False, "Limb damage": 17, "Limb damage (head)": 12},
        "Rambo": {"Type": "Blade", "Price": 90, "Slots": 3, "Damage": 36, "Bleeding Damage": 15, "Stamina": 7, "Attack Cooldown": 0.8, "Attack Delay": 0.2, "Attack time": 0.1, "Stun time": 0.3, "Mobility": 8, "Can block": 0, "Effects can inflict": 2, "Can dismember/break neck": False, "Limb damage": 34, "Limb damage (head)": 20},
        "Machete": {"Type": "Blade", "Price": 300, "Slots": 4, "Damage": 34, "Bleeding Damage": 7, "Stamina": 7, "Attack Cooldown": 0.3, "Attack Delay": 0.2, "Attack time": 0.1, "Stun time": 0.3, "Mobility": 8, "Can block": 20, "Effects can inflict": 3, "Can dismember/break neck": True, "Limb damage": 60, "Limb damage (head)": 60},
        "Katana": {"Type": "Blade", "Price": 350, "Slots": 5, "Damage": 31, "Bleeding Damage": 7, "Stamina": 7, "Attack Cooldown": 0.6, "Attack Delay": 0.1, "Attack time": 0.2, "Stun time": 0.4, "Mobility": 8, "Can block": 18, "Effects can inflict": 3, "Can dismember/break neck": True, "Limb damage": 60, "Limb damage (head)": 60},
        "Cursed Dagger": {"Type": "Blade", "Price": 999, "Slots": 3, "Damage": 33, "Bleeding Damage": 10, "Stamina": 5, "Attack Cooldown": 1.5, "Attack Delay": 0.2, "Attack time": 0.1, "Stun time": 0.5, "Mobility": 8, "Can block": 0, "Effects can inflict": 4, "Can dismember/break neck": False, "Limb damage": 33, "Limb damage (head)": 20},
        "Slayer Sword": {"Type": "Blade", "Price": 33333, "Slots": 9, "Damage": 170, "Bleeding Damage": 10, "Stamina": 22.5, "Attack Cooldown": 1.5, "Attack Delay": 0.4, "Attack time": 0.3, "Stun time": 1, "Mobility": 5.5, "Can block": 25, "Effects can inflict": 4, "Can dismember/break neck": True, "Limb damage": 170, "Limb damage (head)": 170},
        "Scythe": {"Type": "Blade", "Price": 55555, "Slots": 9, "Damage": 55, "Bleeding Damage": 10, "Stamina": 15, "Attack Cooldown": 1.1, "Attack Delay": 0.2, "Attack time": 0.3, "Stun time": 0.6, "Mobility": 6, "Can block": 24, "Effects can inflict": 5, "Can dismember/break neck": True, "Limb damage": 100, "Limb damage (head)": 100},
        "Fallen Blade": {"Type": "Blade", "Price": 22222, "Slots": 7, "Damage": 56, "Bleeding Damage": 15, "Stamina": 14, "Attack Cooldown": 1.1, "Attack Delay": 0.2, "Attack time": 0.2, "Stun time": 0.4, "Mobility": 8, "Can block": 23, "Effects can inflict": 3, "Can dismember/break neck": True, "Limb damage": 110, "Limb damage (head)": 110},
        "Eradicator": {"Type": "Blade", "Price": 99999, "Slots": 4, "Damage": 308, "Bleeding Damage": 0, "Stamina": 5, "Attack Cooldown": 2, "Attack Delay": 0.2, "Attack time": 0.7, "Stun time": 2, "Mobility": 15.5, "Can block": 27, "Effects can inflict": 2, "Can dismember/break neck": True, "Limb damage": 1000, "Limb damage (head)": 1000},
        "Black Bayonet": {"Type": "Blade", "Price": 999999, "Slots": 0, "Damage": 70, "Bleeding Damage": 5, "Stamina": 7, "Attack Cooldown": 0.5, "Attack Delay": 0.1, "Attack time": 0.1, "Stun time": 0.3, "Mobility": 8, "Can block": 0, "Effects can inflict": 2, "Can dismember/break neck": False, "Limb damage": 70, "Limb damage (head)": 70},
        "Fists": {"Type": "Special", "Price": 0, "Slots": 0, "Damage": 12, "Bleeding Damage": 0, "Stamina": 4, "Attack Cooldown": 0.5, "Attack Delay": 0.2, "Attack time": 0.1, "Stun time": 0.2, "Mobility": 8, "Can block": 3, "Effects can inflict": 2, "Can dismember/break neck": False, "Limb damage": 12, "Limb damage (head)": 7},
        "Knuckledusters": {"Type": "Special", "Price": 0, "Slots": 0, "Damage": 17, "Bleeding Damage": 0, "Stamina": 4, "Attack Cooldown": 0.5, "Attack Delay": 0.2, "Attack time": 0.1, "Stun time": 0.2, "Mobility": 8, "Can block": 3, "Effects can inflict": 2, "Can dismember/break neck": False, "Limb damage": 17, "Limb damage (head)": 10},
        "Nunchucks": {"Type": "Special", "Price": 0, "Slots": 0, "Damage": 15, "Bleeding Damage": 0, "Stamina": 4, "Attack Cooldown": 0.4, "Attack Delay": 0.1, "Attack time": 0.1, "Stun time": 0.2, "Mobility": 8, "Can block": 2, "Effects can inflict": 2, "Can dismember/break neck": False, "Limb damage": 15, "Limb damage (head)": 9},
        "Fire Axe": {"Type": "Special", "Price": 150, "Slots": 4, "Damage": 55, "Bleeding Damage": 15, "Stamina": 11, "Attack Cooldown": 1.6, "Attack Delay": 0.6, "Attack time": 0.1, "Stun time": 0.6, "Mobility": 6, "Can block": 0, "Effects can inflict": 3, "Can dismember/break neck": True, "Limb damage": 100, "Limb damage (head)": 115},
        "Chainsaw": {"Type": "Special", "Price": 400, "Slots": 6, "Damage": 260, "Bleeding Damage": 5, "Stamina": 35, "Attack Cooldown": 3, "Attack Delay": 0.2, "Attack time": 1.6, "Stun time": 0.6, "Mobility": 5.5, "Can block": 0, "Effects can inflict": 3, "Can dismember/break neck": True, "Limb damage": 370, "Limb damage (head)": 370}
    },
    "Throwables": {
        "Molotov": {"Price": 90, "Spending requirement": 150, "Slots": 1, "DPS": 47, "Active time": 20, "Radius": 20, "Stun time": 0.2},
        "Incendiary": {"Price": 100, "Spending requirement": 175, "Slots": 1, "DPS": 47, "Active time": 20, "Radius": 20, "Stun time": 0.2},
        "Frag grenade": {"Price": 200, "Spending requirement": 300, "Slots": 1, "Max Damage": 175, "Radius": 45, "Max Stun time": 4},
        "C4": {"Price": 400, "Spending requirement": 350, "Slots": 1.5, "Max Damage": 185, "Radius": 65, "Max Stun time": 4},
        "Pumpkin  bomb": {"Price": 500, "Slots": 1, "Max Damage": "175 + Cursed Burning", "Radius": 55, "Max Stun time": 2.5},
        "Smoke grenade": {"Price": 50, "Spending requirement": 100, "Slot": 1, "Active time": 36, "Radius": 35},
        "Stun grenade": {"Price": 100, "Spending requirement": 175, "Slot": 1, "Max Stun Time": 4, "Radius": 50},
        "Flashbang": {"Price": 70, "Spending requirement": 150, "Slot": 1, "Max blind time": 9, "Radius": 65},
        "CS grenade": {"Price": 60, "Spending requirement": 125, "Slot": 1, "Active time": 30, "Radius": 25, "DPS": 16, "Stun time": 3.5}
    },
    "Misc": {
        "Airstrike": {"Price": "1000 + 49000", "Max Damage": 230, "Slot": 1, "Max Stun Time": 5, "Radius": 115},
        "Precision strike": {"Price": "1000 + 29000", "Max Damage": 230, "Slot": 1, "Max Stun Time": 5, "Radius": 115},
        "Splint": {"Price": 20, "Use Time": 2.5, "Slot": 0.5, "Health": 10, "Limb health": 40},
        "Bandage": {"Price": 30, "Use Time": 2.5, "Slot": 0.5, "Health": 35, "Limb health": 20},
        "Medkit": {"Price": 50, "Use Time": 7, "Slot": 1.5, "Health": 90, "Limb health": 100},
        "Antidote": {"Price": 201, "Use Time": 3, "Slot": 1, "Health": 30, "Limb health": 30},
        "Rage dose": {"Price": 250, "Use Time": 3, "Slot": 1, "Duration": 20, "Speed buff": 30, "Health buff": 20},
        "Lockpick": {"Price": 10, "Uses": 3, "Slot": 0.5},
        "Pepper Spray": {"Price": 85, "Range": 8, "Slot": 1},
        "T-1 Backpack": {"Price": 800, "Extra Slots": 3}
    },
    "Armor": {
        "T-1 Helmet": {"Price": 750, "Armor HP": 60, "Melee Resistance": 0.15, "Concussion Reduction": 0.19, "Shell-Shock Reduction": 0.15, "Bleed Reduction": 0, "Firearm Resistance": 0, "Firearm Limb Damage Resistance": 0, "Extra Melee Resistance": 0, "Melee Limb Damage Resistance": 0.15},
        "T-2 Helmet": {"Price": 1200, "Armor HP": 85, "Melee Resistance": 0.25, "Concussion Reduction": 0.3, "Shell-Shock Reduction": 0.25, "Bleed Reduction": 0, "Firearm Resistance": 0.15, "Firearm Limb Damage Resistance": 0.2, "Extra Melee Resistance": 0, "Melee Limb Damage Resistance": 0.25},
        "T-3 Helmet": {"Price": None, "Armor HP": 200, "Melee Resistance": 0.35, "Concussion Reduction": 0.4, "Shell-Shock Reduction": 0.4, "Bleed Reduction": 0, "Firearm Resistance": 0.3, "Firearm Limb Damage Resistance": 0.3, "Extra Melee Resistance": 0.35, "Melee Limb Damage Resistance": 0.35},
        "Fallen Head": {"Price": None, "Armor HP": 99999, "Melee Resistance": 0.26, "Bleed Reduction": 1, "Firearm Resistance": 1, "Firearm Limb Damage Resistance": 0, "Extra Melee Resistance": 0, "Melee Limb Damage Resistance": 0.1},
        "X-24 Head": {"Price": None, "Armor HP": 99999, "Melee Resistance": 0.5, "Bleed Reduction": 1, "Firearm Resistance": 0.3, "Firearm Limb Damage Resistance": 0.3, "Extra Melee Resistance": 0, "Melee Limb Damage Resistance": 0.3, "Extra Hp": 50},
        "T-1 Vest": {"Price": 1500, "Armor HP": 85, "Melee Resistance": 0.19, "Bleed Reduction": 0.35, "Blast Resistance": 0.15, "Flame Resistance": 0.05, "Extra Slots": 3, "Firearm Resistance": 0, "Firearm Limb Damage Resistance": 0, "Extra Melee Resistance": 0.2, "Melee Limb Damage Resistance": 0.19},
        "T-2 Vest": {"Price": 2300, "Armor HP": 100, "Melee Resistance": 0.27, "Bleed Reduction": 0.44, "Blast Resistance": 0.19, "Flame Resistance": 0.09, "Extra Slots": 4, "Firearm Resistance": 0.25, "Firearm Limb Damage Resistance": 0.2, "Extra Melee Resistance": 0.3, "Melee Limb Damage Resistance": 0.26},
        "T-3 Vest": {"Price": None, "Armor HP": 200, "Melee Resistance": 0.35, "Bleed Reduction": 0.7, "Blast Resistance": 0.44, "Flame Resistance": 0.19, "Extra Slots": 6, "Firearm Resistance": 0.3, "Firearm Limb Damage Resistance": 0.3, "Extra Melee Resistance": 0.5, "Melee Limb Damage Resistance": 0.49},
        "Fallen body": {"Price": None, "Armor HP": 99999, "Melee Resistance": 0.36, "Bleed Reduction": 1, "Blast Resistance": 0.5, "Extra Slots": 0, "Firearm Resistance": 1, "Firearm Limb Damage Resistance": 0, "Extra Melee Resistance": 0, "Melee Limb Damage Resistance": 0.1},
        "X-24 body": {"Price": None, "Armor HP": 99999, "Melee Resistance": 0.5, "Bleed Reduction": 1, "Blast Resistance": 0.4, "Extra Slots": 0, "Firearm Resistance": 0.3, "Firearm Limb Damage Resistance": 0.3, "Extra Melee Resistance": 0, "Melee Limb Damage Resistance": 0.3, "Extra Hp": 50},
        "T-3 Kit": {"Price": 15000, "Armor HP": 200, "Melee Resistance": 0.35, "Bleed Reduction": 0.7, "Blast Resistance": 0.44, "Flame Resistance": 0.19, "Concussion Reduction": 0.4, "Shell-Shock Reduction": 0.4, "Extra Slots": 6}
    }
}

FORBIDDEN_ITEMS = [
    "Pumpkin bomb", "Pumpkin  bomb", "Airstrike", "Precision strike", "T-3 Helmet",
    "UTS-15", "Firework Launcher", "Musket", "Hawkeye", "MP5", "Fallen Head", "Fallen body",
    "Candy Crowbar", "Cursed Dagger", "Slayer Sword", "Scythe", "X-24 Head", "T-3 Vest",
    "Fallen Blade", "Eradicator", "Black Bayonet", "Knuckledusters", "Nunchucks", "X-24 body"
]

FIREARMS_HIGHER_BETTER = ["Damage", "Limb damage", "Headshot damage", "Firerate", "Armor penetration", "Max damage range", "Mobility", "Ammo in magazine", "Ammo"]
FIREARMS_LOWER_BETTER = ["Price", "Refill price", "Slots", "Recoil control", "Reload time"]

MELEES_HIGHER_BETTER = ["Damage", "Bleeding Damage", "Attack time", "Stun time", "Mobility", "Can block", "Effects can inflict", "Can dismember/break neck", "Limb damage", "Limb damage (head)"]
MELEES_LOWER_BETTER = ["Price", "Slots", "Stamina", "Attack Cooldown", "Attack Delay"]

def get_item_by_name(name):
    if not name:
        return None, None, None
    name_lower = name.strip().lower()

    partial_matches = []

    for category, items in DATA.items():
        for item_key, stats in items.items():
            if item_key.lower() == name_lower:
                return item_key, stats, category
            elif name_lower in item_key.lower():
                partial_matches.append((item_key, stats, category))

    if len(partial_matches) == 1:
        return partial_matches[0]
    elif len(partial_matches) > 1:
        print(f"[-] Multiple items match '{name}':")
        for match in partial_matches:
            print(f"    - {match[0]} [{match[2]}]")
        print("[-] Please type a more specific name.")
        return None, None, None

    return None, None, None

def safe_float_convert(val):
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, bool):
        return 1.0 if val else 0.0
    val_str = str(val).lower()
    if "+" in val_str:
        parts = val_str.split("+")
        total = 0.0
        for p in parts:
            p_clean = ''.join(c for c in p if c.isdigit() or c == '.')
            if p_clean:
                total += float(p_clean)
        return total
    clean = ''.join(c for c in val_str if c.isdigit() or c == '.')
    return float(clean) if clean else 0.0

def get_overall_score(stats1, stats2, higher_better, lower_better):
    w1_wins = 0
    w2_wins = 0
    all_keys = set(list(stats1.keys()) + list(stats2.keys()))
    all_keys.discard("Type")

    for stat in all_keys:
        v1_num = safe_float_convert(stats1.get(stat, 0))
        v2_num = safe_float_convert(stats2.get(stat, 0))

        if v1_num != v2_num:
            if stat in higher_better:
                if v1_num > v2_num: w1_wins += 1
                else: w2_wins += 1
            elif stat in lower_better:
                if v1_num < v2_num: w1_wins += 1
                else: w2_wins += 1
            else:
                if v1_num > v2_num: w1_wins += 1
                else: w2_wins += 1
    return w1_wins, w2_wins

def compare_weapons(wpn1_name, wpn2_name, category, higher_better, lower_better):
    w1_key, stats1, cat1 = get_item_by_name(wpn1_name)
    w2_key, stats2, cat2 = get_item_by_name(wpn2_name)

    if not w1_key or not w2_key:
        print("[-] Comparison cancelled due to missing or ambiguous item names.")
        return

    if cat1 != category or cat2 != category:
        print(f"[-] Both items must belong to the '{category}' category!")
        return

    print(f"\n[Comparison] Results: {w1_key} vs {w2_key} ")
    print("-" * 55)

    w1_wins, w2_wins = 0, 0
    all_keys = set(list(stats1.keys()) + list(stats2.keys()))
    all_keys.discard("Type")

    for stat in sorted(all_keys):
        val1 = stats1.get(stat, 0)
        val2 = stats2.get(stat, 0)
        v1_num = safe_float_convert(val1)
        v2_num = safe_float_convert(val2)

        sign = "="
        if v1_num != v2_num:
            if stat in higher_better:
                if v1_num > v2_num:
                    sign = ">"
                    w1_wins += 1
                else:
                    sign = "<"
                    w2_wins += 1
            elif stat in lower_better:
                if v1_num < v2_num:
                    sign = ">"
                    w1_wins += 1
                else:
                    sign = "<"
                    w2_wins += 1
            else:
                sign = ">" if v1_num > v2_num else "<"

        print(f"{stat:25s}: {str(val1):<8s} {sign}  {str(val2)}")

    print("-" * 55)
    if w1_wins > w2_wins:
        print(f"[WINNER] {w1_key} have more better stats! (Stat wins: {w1_wins} vs {w2_wins})")
    elif w2_wins > w1_wins:
        print(f"[WINNER] {w2_key} have more better stats! (Stat wins: {w2_wins} vs {w1_wins})")
    else:
        print("[WINNER] It's a tie! Both items are equally balanced against each other.")

def main():
    while True:
        print("\n=== MAIN MENU ===")
        print("1. Characteristics & Advanced Analysis")
        print("2. Compare Firearms")
        print("3. Compare Melee Weapons")
        print("4. Game Session Statistics")
        print("5. Random Loadout Generator")
        print("6. TTK / Target HP Analyzer")
        print("7. Exit")

        choice = input("Select menu option (1-7): ").strip()

        if choice == "1":
            print("\n--- Mode 1: Stats Analysis ---")
            print("1. View specific item stats")
            print("2. Show global weapon TOP by selected stat")
            sub_mode = input("Select sub-mode (1-2): ").strip()

            if sub_mode == "1":
                print("\n--- Available Items ---")
                for category, items in DATA.items():
                    print(f"\n[{category}]:")
                    item_names = list(items.keys())
                    for i in range(0, len(item_names), 3):
                        chunk = item_names[i:i+3]
                        print("  " + "".join(f"{name:.<25}" for name in chunk))

                name = input("\nEnter item name: ")
                item_key, stats, cat = get_item_by_name(name)
                if item_key:
                    print(f"\n[Info] Stats for [{cat}] -> {item_key}:")
                    for k, v in stats.items():
                        print(f"  - {k}: {v}")

                    if cat in ["Firearms", "Melees"]:
                        print("\n[Analysis] Advanced Comparison Menu:")
                        print("1. Show weapons BETTER in a specific stat")
                        print("2. Show weapons WORSE in a specific stat")
                        print("3. Show weapons BETTER overall")
                        print("4. Show weapons WORSE overall")
                        print("5. Skip and return to main menu")
                        sub_choice = input("Select an option (1-5): ").strip()

                        higher_better_list = FIREARMS_HIGHER_BETTER if cat == "Firearms" else MELEES_HIGHER_BETTER
                        lower_better_list = FIREARMS_LOWER_BETTER if cat == "Firearms" else MELEES_LOWER_BETTER

                        if sub_choice in ["1", "2"]:
                            target_stat = input("Enter exact stat name (e.g., Damage): ").strip()
                            actual_stat = next((k for k in stats.keys() if k.lower() == target_stat.lower()), None)

                            if actual_stat:
                                is_higher_better = actual_stat in higher_better_list or (actual_stat not in lower_better_list)
                                base_val = safe_float_convert(stats[actual_stat])
                                results = []

                                for other_name, other_stats in DATA[cat].items():
                                    if other_name == item_key: continue
                                    if actual_stat not in other_stats: continue

                                    other_val = safe_float_convert(other_stats[actual_stat])

                                    if sub_choice == "1":
                                        is_better = (is_higher_better and other_val > base_val) or (not is_higher_better and other_val < base_val)
                                        if is_better:
                                            results.append((other_name, other_val, abs(other_val - base_val)))
                                    else:
                                        is_worse = (is_higher_better and other_val < base_val) or (not is_higher_better and other_val > base_val)
                                        if is_worse:
                                            results.append((other_name, other_val, abs(base_val - other_val)))

                                results.sort(key=lambda x: x[2], reverse=True)

                                condition_text = "BETTER" if sub_choice == "1" else "WORSE"
                                print(f"\n[TOP] Weapons that are {condition_text} in '{actual_stat}' than {item_key} (Base: {base_val}):")
                                if results:
                                    for i, (name, val, diff) in enumerate(results, 1):
                                        print(f"  {i}. {name}: {val} (Difference: {diff:.2f})")
                                else:
                                    print("  No items matching the condition were found.")
                            else:
                                print("[-] Stat not found on this item.")

                        elif sub_choice in ["3", "4"]:
                            results = []
                            for other_name, other_stats in DATA[cat].items():
                                if other_name == item_key: continue
                                base_wins, other_wins = get_overall_score(stats, other_stats, higher_better_list, lower_better_list)

                                if sub_choice == "3":
                                    if other_wins > base_wins:
                                        results.append((other_name, other_wins, base_wins, other_wins - base_wins))
                                else:
                                    if base_wins > other_wins:
                                        results.append((other_name, other_wins, base_wins, base_wins - other_wins))

                            results.sort(key=lambda x: x[3], reverse=True)

                            condition_text = "BETTER OVERALL" if sub_choice == "3" else "WORSE OVERALL"
                            print(f"\n[TOP] Weapons that are {condition_text} than {item_key}:")
                            if results:
                                for i, (name, ow, bw, margin) in enumerate(results, 1):
                                    print(f"  {i}. {name} (Wins: {ow} vs {bw}) -> Advantage: {margin} points")
                            else:
                                print("  No items matching the condition were found.")
                else:
                    if name:
                        print("[-] Item not found.")

            elif sub_mode == "2":
                print("\nSelect category to build TOP:")
                print("1. Firearms")
                print("2. Melees")
                cat_choice = input("Your choice (1-2): ").strip()
                cat = "Firearms" if cat_choice == "1" else "Melees" if cat_choice == "2" else None

                if cat:
                    sample_item = list(DATA[cat].values())[0]
                    available_stats = [k for k in sample_item.keys() if k != "Type"]

                    print(f"\nAvailable stats for {cat}:")
                    for i in range(0, len(available_stats), 3):
                        chunk = available_stats[i:i+3]
                        print("  " + "".join(f"{stat:.<30}" for stat in chunk))

                    target_stat = input("\nEnter stat of interest: ").strip()
                    actual_stat = next((k for k in sample_item.keys() if k.lower() == target_stat.lower()), None)

                    if actual_stat:
                        higher_better_list = FIREARMS_HIGHER_BETTER if cat == "Firearms" else MELEES_HIGHER_BETTER
                        lower_better_list = FIREARMS_LOWER_BETTER if cat == "Firearms" else MELEES_LOWER_BETTER
                        is_higher_better = actual_stat in higher_better_list or (actual_stat not in lower_better_list)

                        results = []
                        for wpn_name, wpn_stats in DATA[cat].items():
                            if actual_stat in wpn_stats:
                                val = safe_float_convert(wpn_stats[actual_stat])
                                results.append((wpn_name, val))

                        results.sort(key=lambda x: x[1], reverse=is_higher_better)

                        print(f"\n[TOP] Weapon rating by '{actual_stat}' (from best to worst):")
                        for i, (wpn_name, val) in enumerate(results, 1):
                            print(f"  {i}. {wpn_name}: {val}")
                    else:
                        print("[-] This stat is missing from the items.")
                else:
                    print("[-] Invalid category choice.")

        elif choice == "2":
            wpn1 = input("Enter first firearm: ")
            wpn2 = input("Enter second firearm: ")
            compare_weapons(wpn1, wpn2, "Firearms", FIREARMS_HIGHER_BETTER, FIREARMS_LOWER_BETTER)

        elif choice == "3":
            wpn1 = input("Enter first melee weapon: ")
            wpn2 = input("Enter second melee weapon: ")
            compare_weapons(wpn1, wpn2, "Melees", MELEES_HIGHER_BETTER, MELEES_LOWER_BETTER)

        elif choice == "4":
            print("\n--- SESSION START ---")
            try:
                start_money = float(input("Enter current money: "))
                start_xp = float(input("Enter current XP: "))
            except ValueError:
                print("[-] Balance and XP must be numbers!")
                continue

            deaths = 0
            kills = 0
            assists = 0
            total_spent = 0.0
            bought_items = {}

            print("\nLog recording active. Enter purchased item names or quick action commands:")
            print("  'd' - Death")
            print("  'k' - Kill")
            print("  'a' - Assist")
            print("To stop the session, enter your current amount of money (number).")

            while True:
                action = input("Action / Item: ").strip()
                if not action:
                    continue

                if action.lower() == "d":
                    deaths += 1
                    print("[X] Death added to log.")
                    continue
                if action.lower() == "k":
                    kills += 1
                    print("[+] Kill added to log.")
                    continue
                if action.lower() == "a":
                    assists += 1
                    print("[+] Assist added to log.")
                    continue

                if action.replace('.', '', 1).isdigit():
                    end_money = float(action)
                    break

                item_key, item_stats, _ = get_item_by_name(action)
                display_name = item_key if item_key else action

                if item_key is None and action.lower() not in ["d", "k", "a"]:
                    print("[-] Item not added. Please try again with a more specific name.")
                    continue

                bought_items[display_name] = bought_items.get(display_name, 0) + 1

                if item_stats and "Price" in item_stats:
                    price = safe_float_convert(item_stats["Price"])
                    total_spent += price
                    print(f"[Purchased] Added: {display_name} (${price:.2f})")
                else:
                    print(f"[Purchased] Added: {display_name} (Price missing in DB)")

            try:
                end_xp = float(input("Enter final XP: "))
            except ValueError:
                print("Input error. Session XP set to 0.")
                end_xp = start_xp

            kd_ratio = kills / deaths if deaths > 0 else float(kills)

            print("\n[Statistics] GAME SESSION RESULTS:")
            print(f"  Profit: ${end_money - start_money:.2f}")
            print(f"  Total spent on buys: ${total_spent:.2f}")
            print(f"  XP earned: {end_xp - start_xp:.2f}")
            print(f"  Combat stats: Kills: {kills} | Assists: {assists} | Deaths: {deaths}")
            print(f"  K/D Ratio: {kd_ratio:.2f}")
            print("  Purchased equipment:")
            if bought_items:
                for item, count in bought_items.items():
                    print(f"    - {item}: {count}x")
            else:
                print("    - No equipment was purchased.")

        elif choice == "5":
            print("\n--- Select Loadout Cost Category ---")
            print("1. Cheap Loadout (<= $1000)")
            print("2. Regular Loadout ($1001 - $4000, mid-tier weapons)")
            print("3. Expensive Loadout (>= $4000, high-tier firearms, armor sets only)")
            print("4. Custom Bounds (Set Min and Max budget)")
            tier_choice = input("Your choice (1-4): ").strip()

            min_budget = 0
            max_budget = 0

            if tier_choice == "1":
                min_budget = 0
                max_budget = 1000
                num_extras_max = 2
                min_firearm_price = 0
                min_melee_price = 0
                always_dual_firearms = False
                allow_t3 = False
                armor_pool_type = "cheap"
            elif tier_choice == "2":
                min_budget = 1001
                max_budget = 4000
                num_extras_max = 3
                min_firearm_price = 401
                min_melee_price = 161
                always_dual_firearms = False
                allow_t3 = False
                armor_pool_type = "regular"
            elif tier_choice == "3":
                min_budget = 4000
                max_budget = 9999999
                num_extras_max = 4
                min_firearm_price = 1101
                min_melee_price = 0
                always_dual_firearms = True
                allow_t3 = True
                armor_pool_type = "expensive"
            elif tier_choice == "4":
                try:
                    min_budget = float(input("Enter minimum loadout budget: "))
                    max_budget = float(input("Enter maximum loadout budget: "))
                except ValueError:
                    print("[-] Input error. Switching to default Regular limit ($1001-$4000).")
                    min_budget = 1001
                    max_budget = 4000

                num_extras_max = 3
                allow_t3 = True

                if min_budget >= 4000:
                    min_firearm_price = 1101
                    min_melee_price = 0
                    always_dual_firearms = True
                    armor_pool_type = "expensive"
                elif min_budget >= 1000:
                    min_firearm_price = 401
                    min_melee_price = 161
                    always_dual_firearms = False
                    armor_pool_type = "regular"
                else:
                    min_firearm_price = 0
                    min_melee_price = 0
                    always_dual_firearms = False
                    armor_pool_type = "cheap"
            else:
                print("[-] Invalid choice. Defaulting to Regular mode ($1001-$4000).")
                min_budget = 1001
                max_budget = 4000
                num_extras_max = 3
                min_firearm_price = 401
                min_melee_price = 161
                always_dual_firearms = False
                allow_t3 = False
                armor_pool_type = "regular"

            valid_firearms = [k for k, v in DATA["Firearms"].items() if k not in FORBIDDEN_ITEMS and safe_float_convert(v.get("Price", 0)) >= min_firearm_price]
            valid_melees = [k for k, v in DATA["Melees"].items() if k not in FORBIDDEN_ITEMS and safe_float_convert(v.get("Price", 0)) >= min_melee_price]

            if not valid_firearms:
                print("[-] Error: No firearms fit the minimum price requirements.")
                continue

            while True:
                attempts = 0
                success = False

                while attempts < 3000:
                    attempts += 1
                    base_slots = 10
                    used_slots = 0
                    total_cost = 0
                    loadout = []

                    if armor_pool_type == "expensive":
                        armor_options = ["None", "T-1 Set", "T-2 Set"]
                        if allow_t3: armor_options.append("T-3 Kit")
                    else:
                        armor_options = ["None", "T-1 Helmet", "T-1 Vest", "T-1 Set", "T-2 Helmet", "T-2 Vest", "T-2 Set"]
                        if allow_t3: armor_options.append("T-3 Kit")

                    chosen_armor = random.choice(armor_options)

                    if chosen_armor == "T-3 Kit":
                        total_cost += safe_float_convert(DATA["Armor"]["T-3 Kit"]["Price"])
                        base_slots += safe_float_convert(DATA["Armor"]["T-3 Kit"]["Extra Slots"])
                        loadout.append("Armor: T-3 Kit")
                    elif chosen_armor != "None":
                        tier = "T-1" if "T-1" in chosen_armor else "T-2"
                        has_helmet = "Helmet" in chosen_armor or "Set" in chosen_armor
                        has_vest = "Vest" in chosen_armor or "Set" in chosen_armor

                        desc_parts = []
                        if has_helmet:
                            total_cost += safe_float_convert(DATA["Armor"][f"{tier} Helmet"]["Price"])
                            desc_parts.append("Helmet")
                        if has_vest:
                            total_cost += safe_float_convert(DATA["Armor"][f"{tier} Vest"]["Price"])
                            base_slots += safe_float_convert(DATA["Armor"][f"{tier} Vest"]["Extra Slots"])
                            desc_parts.append("Vest")

                        loadout.append(f"Armor: {tier} Set ({' + '.join(desc_parts)})")
                    else:
                        loadout.append("Armor: No Armor")

                    if total_cost > max_budget:
                        continue

                    use_dual_firearms = always_dual_firearms or (random.random() < 0.40)

                    fa1 = random.choice(valid_firearms)
                    fa1_type = DATA["Firearms"][fa1].get("Type")
                    f1_price = safe_float_convert(DATA["Firearms"][fa1].get("Price", 0))
                    f1_slots = safe_float_convert(DATA["Firearms"][fa1].get("Slots", 0))

                    if use_dual_firearms:
                        valid_fa2 = [f for f in valid_firearms if DATA["Firearms"][f].get("Type") != fa1_type]
                        if not valid_fa2:
                            valid_fa2 = valid_firearms

                        fa2 = random.choice(valid_fa2)
                        f2_price = safe_float_convert(DATA["Firearms"][fa2].get("Price", 0))
                        f2_slots = safe_float_convert(DATA["Firearms"][fa2].get("Slots", 0))

                        total_cost += (f1_price + f2_price)
                        used_slots += (f1_slots + f2_slots)
                        loadout.append(f"Firearm 1: {fa1}")
                        loadout.append(f"Firearm 2: {fa2}")
                    else:
                        if not valid_melees: continue
                        melee = random.choice(valid_melees)
                        m_price = safe_float_convert(DATA["Melees"][melee].get("Price", 0))
                        m_slots = safe_float_convert(DATA["Melees"][melee].get("Slots", 0))

                        total_cost += (f1_price + m_price)
                        used_slots += (f1_slots + m_slots)
                        loadout.append(f"Melee: {melee}")
                        loadout.append(f"Firearm: {fa1}")

                    if total_cost > max_budget or used_slots > base_slots:
                        continue

                    pool = []
                    for cat in ["Throwables", "Misc"]:
                        for item, st in DATA[cat].items():
                            if item not in FORBIDDEN_ITEMS:
                                pool.append((item, st))

                    if "Bandage" in DATA["Misc"]:
                        for _ in range(10):
                            pool.append(("Bandage", DATA["Misc"]["Bandage"]))

                    num_extras = random.randint(1, num_extras_max)
                    misc_counts = {}
                    min_slot_req = 0.5

                    for _ in range(num_extras):
                        if used_slots >= base_slots - min_slot_req:
                            break

                        fitting_pool = []
                        for i, s in pool:
                            slot_val = safe_float_convert(s.get("Slot", s.get("Slots", 0)))
                            price_val = safe_float_convert(s.get("Price", 0))
                            if slot_val <= (base_slots - used_slots) and (total_cost + price_val) <= max_budget:
                                fitting_pool.append((i, s))

                        if not fitting_pool:
                            break

                        item_name, item_stats = random.choice(fitting_pool)
                        i_slots = safe_float_convert(item_stats.get("Slot", item_stats.get("Slots", 0)))

                        used_slots += i_slots
                        total_cost += safe_float_convert(item_stats.get("Price", 0))
                        misc_counts[item_name] = misc_counts.get(item_name, 0) + 1

                        if item_name == "T-1 Backpack" and misc_counts[item_name] == 1:
                            base_slots += safe_float_convert(item_stats.get("Extra Slots", 0))

                    if total_cost > max_budget or total_cost < min_budget:
                        continue

                    for item, count in misc_counts.items():
                        loadout.append(f"Extra: {item} (x{count})")

                    print("\n[Random] RANDOM LOADOUT GENERATED:")
                    for line in loadout:
                        print("  " + line)
                    print("-" * 30)
                    print(f"[Slots] Inventory weight: {used_slots} / {base_slots}")
                    print(f"[Price] Total cost: ${total_cost:.2f}")
                    success = True
                    break

                if not success:
                    print("[-] Could not generate a loadout with these strict budget constraints. Try widening the Min/Max gap.")

                reroll = input("\n[Prompt] Generate another loadout with the same settings? (y/n): ").strip().lower()
                if reroll not in ['y', 'yes', '1']:
                    break

        elif choice == "6":
            wpn_name = input("Enter attacking weapon: ")
            item_key, stats, cat = get_item_by_name(wpn_name)

            if not item_key or cat not in ["Firearms", "Melees"]:
                print("[-] Weapon not found or inapplicable for damage tests.")
                continue

            hit_loc = input("Hit zone (body / head)? ").strip().lower()
            if hit_loc not in ["head", "body"]:
                print("Defaulting to body.")
                hit_loc = "body"

            if hit_loc == "head":
                valid_armor = [k for k in DATA["Armor"].keys() if "Helmet" in k or k in ["Fallen Head", "X-24 Head"]]
            else:
                valid_armor = [k for k in DATA["Armor"].keys() if "Vest" in k or k in ["Fallen body", "X-24 body"]]

            print("\nAvailable armor for this zone:")
            print("None, " + ", ".join(valid_armor))
            armor_choice = input("Select target armor (Leave empty for None): ").strip()

            target_max_hp = 150.0 if ("X-24" in armor_choice or "x-24" in armor_choice) else 100.0
            target_hp = target_max_hp
            limb_hp = target_max_hp
            hits = 0
            limb_broken_at = -1
            instant_killed = False

            a_key, armor_stats, a_cat = get_item_by_name(armor_choice)

            if a_key and a_key in valid_armor:
                armor_hp = safe_float_convert(armor_stats.get("Armor HP", 0))
                melee_res = safe_float_convert(armor_stats.get("Melee Resistance", 0))
                extra_melee_res = safe_float_convert(armor_stats.get("Extra Melee Resistance", 0))
                melee_limb_res = safe_float_convert(armor_stats.get("Melee Limb Damage Resistance", 0))
                firearm_res = safe_float_convert(armor_stats.get("Firearm Resistance", 0))
                firearm_limb_res = safe_float_convert(armor_stats.get("Firearm Limb Damage Resistance", 0))
                bleed_red = safe_float_convert(armor_stats.get("Bleed Reduction", 0))
                print(f"[DEFENSE] Target is equipped with {a_key} ({armor_hp} Armor HP). Target HP: {target_max_hp}")
            else:
                armor_hp = 0
                melee_res = extra_melee_res = melee_limb_res = 0.0
                firearm_res = firearm_limb_res = bleed_red = 0.0
                print(f"[Player] Target has no armor. Target HP: {target_max_hp}")

            if hit_loc == "head" and "Headshot damage" in stats:
                base_dmg = safe_float_convert(stats["Headshot damage"])
            else:
                base_dmg = safe_float_convert(stats.get("Damage", stats.get("Max Damage", 0)))

            if base_dmg <= 0:
                print("[-] This item deals 0 base damage.")
                continue

            armor_pen = safe_float_convert(stats.get("Armor penetration", 1.0))
            is_melee = (cat == "Melees")
            is_launcher = (stats.get("Type") == "Launcher")

            initial_target_dmg = 0
            initial_armor_dmg = 0
            initial_limb_dmg = 0

            # Calculate initial hit statistics
            if armor_hp > 0:
                if is_melee:
                    initial_target_dmg = base_dmg * (1 - melee_res) * (1 - extra_melee_res)
                    initial_armor_dmg = 0
                    if hit_loc == "body":
                        limb_base = safe_float_convert(stats.get("Limb damage", 0))
                    else:
                        limb_base = safe_float_convert(stats.get("Limb damage (head)", 0))
                    initial_limb_dmg = limb_base * (1 - melee_limb_res)
                elif is_launcher:
                    blast_res = safe_float_convert(armor_stats.get("Blast Resistance", 0))
                    initial_target_dmg = base_dmg * (1 - blast_res) if a_key else base_dmg
                    initial_armor_dmg = 0
                    if hit_loc == "body":
                        initial_limb_dmg = 0
                    else:
                        initial_limb_dmg = 0
                else:
                    initial_target_dmg = base_dmg * armor_pen * (1 - firearm_res)
                    initial_armor_dmg = base_dmg * (1 - armor_pen)
                    if hit_loc == "body":
                        initial_limb_dmg = base_dmg * 1.85 * (1 - firearm_limb_res)
                    else:
                        initial_limb_dmg = 0
            else:
                initial_target_dmg = base_dmg
                initial_armor_dmg = 0
                if is_melee:
                    if hit_loc == "body":
                        initial_limb_dmg = safe_float_convert(stats.get("Limb damage", 0))
                    else:
                        initial_limb_dmg = safe_float_convert(stats.get("Limb damage (head)", 0))
                else:
                    if hit_loc == "body":
                        initial_limb_dmg = base_dmg * 1.85
                    else:
                        initial_limb_dmg = 0

            print("-" * 30)
            print(f"[Analysis] Damage to target HP per hit: {initial_target_dmg:.2f}")
            print(f"[Analysis] Damage to armor per hit: {initial_armor_dmg:.2f}")
            if is_melee or hit_loc == "body":
                print(f"[Analysis] Damage to limb per hit: {initial_limb_dmg:.2f}")
            print("-" * 30)

            while target_hp > 0:
                hits += 1
                current_target_dmg = 0
                current_limb_dmg = 0
                armor_dmg = 0

                if armor_hp > 0:
                    if is_melee:
                        current_target_dmg = base_dmg * (1 - melee_res) * (1 - extra_melee_res)
                        armor_dmg = 0

                        if hit_loc == "body":
                            limb_base = safe_float_convert(stats.get("Limb damage", 0))
                        else:
                            limb_base = safe_float_convert(stats.get("Limb damage (head)", 0))
                        current_limb_dmg = limb_base * (1 - melee_limb_res)
                    elif is_launcher:
                        blast_res = safe_float_convert(armor_stats.get("Blast Resistance", 0))
                        current_target_dmg = base_dmg * (1 - blast_res)
                        armor_dmg = 0
                        if hit_loc == "body":
                            current_limb_dmg = 0
                    else:
                        current_target_dmg = base_dmg * armor_pen * (1 - firearm_res)
                        armor_dmg = base_dmg * (1 - armor_pen)

                        if hit_loc == "body":
                            current_limb_dmg = base_dmg * 1.85 * (1 - firearm_limb_res)
                else:
                    current_target_dmg = base_dmg
                    if is_melee:
                        if hit_loc == "body":
                            current_limb_dmg = safe_float_convert(stats.get("Limb damage", 0))
                        else:
                            current_limb_dmg = safe_float_convert(stats.get("Limb damage (head)", 0))
                    else:
                        if hit_loc == "body":
                            current_limb_dmg = base_dmg * 1.85

                target_hp -= current_target_dmg

                if hit_loc == "body" or (is_melee and hit_loc == "head"):
                    if limb_hp > 0:
                        limb_hp -= current_limb_dmg
                        if limb_hp <= 0:
                            limb_broken_at = hits

                            if is_melee and hit_loc == "head" and stats.get("Can dismember/break neck", False):
                                instant_killed = True
                                target_hp = 0

                if target_hp <= 0:
                    break

                if is_melee:
                    interval = safe_float_convert(stats.get("Attack Cooldown", 0)) + \
                               safe_float_convert(stats.get("Attack Delay", 0)) + \
                               safe_float_convert(stats.get("Attack time", 0))
                    bleed_total = safe_float_convert(stats.get("Bleeding Damage", 0))
                    bleed_dps = (bleed_total * (1 - bleed_red)) / 9.0

                    target_hp -= (bleed_dps * interval)

                    if target_hp <= 0:
                        break

                if armor_hp > 0:
                    armor_hp -= armor_dmg
                    if armor_hp <= 0:
                        print(f"[!] Hit {hits}: Target armor is FULLY BROKEN!")

                if current_target_dmg <= 0 and current_limb_dmg <= 0 and (not is_melee or bleed_total <= 0):
                    print("[Warning] Weapon is powerless against this target's armor, damage completely blocked.")
                    break

            if instant_killed:
                print(f"[FATALITY] Hit {hits}: Target's neck broken/dismembered! Instant Kill!")
            elif limb_broken_at != -1 and limb_broken_at <= hits:
                print(f"[Limb Status] Target's limb broke/dismembered on hit/shot {limb_broken_at}.")

            if target_hp <= 0:
                print(f"[Result] Hits/shots required to eliminate target: {hits}")

        elif choice == "7":
            print("Program terminated.")
            break
        else:
            print("[-] Error: invalid main menu option selected.")

if __name__ == "__main__":
    main()
