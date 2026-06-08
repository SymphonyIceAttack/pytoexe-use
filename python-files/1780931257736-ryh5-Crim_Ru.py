import math
import random

# База данных
DATA = {
    "Firearms": {
        "Beretta": {"Type": "Pistol", "Price": 200, "Refill price": 180, "Slots": 3, "Damage": 17, "Headshot damage": 23, "Firerate": 3.7, "Recoil control": 18, "Armor penetration": 0.45, "Max damage range": 1250, "Mobility": 16, "Reload time": 2.25, "Ammo in magazine": 12, "Ammo": 48},
        "G-17": {"Type": "Pistol", "Price": 250, "Refill price": 150, "Slots": 3, "Damage": 21, "Headshot damage": 29, "Firerate": 5, "Recoil control": 21, "Armor penetration": 0.353, "Max damage range": 2000, "Mobility": 16, "Reload time": 2.25, "Ammo in magazine": 14, "Ammo": 56},
        "TEC-9": {"Type": "Pistol", "Price": 350, "Refill price": 220, "Slots": 3, "Damage": 18, "Headshot damage": 26, "Firerate": 2.5, "Recoil control": 19, "Armor penetration": 0.33, "Max damage range": 1550, "Mobility": 15, "Reload time": 3, "Ammo in magazine": 18, "Ammo": 72},
        "M1911": {"Type": "Pistol", "Price": 450, "Refill price": 200, "Slots": 3, "Damage": 29, "Headshot damage": 43, "Firerate": 4.5, "Recoil control": 26, "Armor penetration": 0.42, "Max damage range": 2550, "Mobility": 16, "Reload time": 2.5, "Ammo in magazine": 8, "Ammo": 32},
        "FNP-45": {"Type": "Pistol", "Price": 800, "Refill price": 250, "Slots": 3.5, "Damage": 26, "Headshot damage": 37, "Firerate": 5.1, "Recoil control": 20, "Armor penetration": 0.55, "Max damage range": 2100, "Mobility": 16, "Reload time": 2.25, "Ammo in magazine": 12, "Ammo": 48},
        "Deagle": {"Type": "Pistol", "Price": 900, "Refill price": 250, "Slots": 3.5, "Damage": 37, "Headshot damage": 58, "Firerate": 2.5, "Recoil control": 45, "Armor penetration": 0.57, "Max damage range": 3150, "Mobility": 14.5, "Reload time": 3, "Ammo in magazine": 7, "Ammo": 28},
        "Magnum": {"Type": "Pistol", "Price": 1200, "Refill price": 450, "Slots": 3.5, "Damage": 51, "Headshot damage": 102, "Firerate": 2, "Recoil control": 55, "Armor penetration": 0.52, "Max damage range": 4150, "Mobility": 14.75, "Reload time": 3, "Ammo in magazine": 6, "Ammo": 24},
        "G-18": {"Type": "Pistol", "Price": 1050, "Refill price": 250, "Slots": 3, "Damage": 18, "Headshot damage": 26, "Firerate": 13, "Recoil control": 21, "Armor penetration": 0.41, "Max damage range": 1550, "Mobility": 16, "Reload time": 2.25, "Ammo in magazine": 20, "Ammo": 60},
        "Hawkeye": {"Type": "Pistol", "Price": 1200, "Refill price": 300, "Slots": 3.5, "Damage": 101, "Headshot damage": 202, "Firerate": 5, "Recoil control": 2, "Armor penetration": 0.95, "Max damage range": 99999, "Mobility": 14.75, "Reload time": 3, "Ammo in magazine": 1, "Ammo": 2},
        "Uzi": {"Type": "Smg", "Price": 400, "Refill price": 250, "Slots": 4, "Damage": 16, "Headshot damage": 23, "Firerate": 8.2, "Recoil control": 21, "Armor penetration": 0.37, "Max damage range": 1500, "Mobility": 14.5, "Reload time": 3, "Ammo in magazine": 25, "Ammo": 100},
        "MAC-10": {"Type": "Smg", "Price": 1100, "Refill price": 300, "Slots": 4, "Damage": 15, "Headshot damage": 21, "Firerate": 13, "Recoil control": 18, "Armor penetration": 0.51, "Max damage range": 1450, "Mobility": 14.5, "Reload time": 3, "Ammo in magazine": 25, "Ammo": 100},
        "MP7": {"Type": "Smg", "Price": 1700, "Refill price": 300, "Slots": 4.5, "Damage": 16, "Headshot damage": 23, "Firerate": 12, "Recoil control": 17, "Armor penetration": 0.6, "Max damage range": 1500, "Mobility": 14.5, "Reload time": 3, "Ammo in magazine": 25, "Ammo": 100},
        "UMP-45": {"Type": "Smg", "Price": 1900, "Refill price": 100, "Slots": 4.5, "Damage": 23, "Headshot damage": 34, "Firerate": 6.6, "Recoil control": 19, "Armor penetration": 0.66, "Max damage range": 2050, "Mobility": 14, "Reload time": 3.25, "Ammo in magazine": 25, "Ammo": 100},
        "Tommy Gun": {"Type": "Smg", "Price": 1300, "Refill price": 350, "Slots": 5, "Damage": 17, "Headshot damage": 24, "Firerate": 9.2, "Recoil control": 17, "Armor penetration": 0.57, "Max damage range": 1850, "Mobility": 14, "Reload time": 4, "Ammo in magazine": 50, "Ammo": 150},
        "MP5": {"Type": "Smg", "Price": 1800, "Refill price": 150, "Slots": 4.5, "Damage": 19, "Headshot damage": 26.6, "Firerate": 9.3, "Recoil control": 18, "Armor penetration": 0.6, "Max damage range": 1650, "Mobility": 14.15, "Reload time": 3.25, "Ammo in magazine": 25, "Ammo": 100},
        "Sawn-Off": {"Type": "Shotgun", "Price": 175, "Refill price": 150, "Slots": 3.5, "Damage": 96, "Headshot damage": 136, "Firerate": 2, "Recoil control": 45, "Armor penetration": 0.15, "Max damage range": 11, "Mobility": 14.75, "Reload time": 2.5, "Ammo in magazine": 2, "Ammo": 10},
        "Super-Shorty": {"Type": "Shotgun", "Price": 850, "Refill price": 200, "Slots": 3.5, "Damage": 112, "Headshot damage": 152, "Firerate": 0.9, "Recoil control": 35, "Armor penetration": 0.2, "Max damage range": 15, "Mobility": 14.5, "Reload time": 3, "Ammo in magazine": 3, "Ammo": 15},
        "Ithaca-37": {"Type": "Shotgun", "Price": 750, "Refill price": 250, "Slots": 5, "Damage": 120, "Headshot damage": 152, "Firerate": 0.8, "Recoil control": 60, "Armor penetration": 0.2, "Max damage range": 20, "Mobility": 14, "Reload time": 6.25, "Ammo in magazine": 5, "Ammo": 25},
        "UTS-15": {"Type": "Shotgun", "Price": 25000, "Refill price": 99999, "Slots": 7, "Damage": 217, "Headshot damage": 217, "Firerate": 1.2, "Recoil control": 78.26, "Armor penetration": 0.525, "Max damage range": 450, "Mobility": 12, "Reload time": 11.25, "Ammo in magazine": 15, "Ammo": 60},
        "AKS-74U": {"Type": "AR", "Price": 1750, "Refill price": 300, "Slots": 5.5, "Damage": 24, "Headshot damage": 36, "Firerate": 7, "Recoil control": 21, "Armor penetration": 0.68, "Max damage range": 2050, "Mobility": 13, "Reload time": 3.5, "Ammo in magazine": 30, "Ammo": 120},
        "M4A1": {"Type": "AR", "Price": 3100, "Refill price": 350, "Slots": 6, "Damage": 21, "Headshot damage": 31, "Firerate": 8.5, "Recoil control": 19, "Armor penetration": 0.7, "Max damage range": 3950, "Mobility": 14, "Reload time": 3, "Ammo in magazine": 30, "Ammo": 120},
        "SCAR-H": {"Type": "AR", "Price": 3500, "Refill price": 300, "Slots": 6, "Damage": 31, "Headshot damage": 47, "Firerate": 6.5, "Recoil control": 23, "Armor penetration": 0.72, "Max damage range": 3000, "Mobility": 12.75, "Reload time": 3.5, "Ammo in magazine": 20, "Ammo": 80},
        "AKM": {"Type": "AR", "Price": 5600, "Refill price": 350, "Slots": 6.5, "Damage": 29, "Headshot damage": 44, "Firerate": 7, "Recoil control": 24, "Armor penetration": 0.8, "Max damage range": 4400, "Mobility": 12.7, "Reload time": 3.85, "Ammo in magazine": 30, "Ammo": 120},
        "SKS": {"Type": "DMR", "Price": 650, "Refill price": 250, "Slots": 6.5, "Damage": 29, "Headshot damage": 44, "Firerate": 4.5, "Recoil control": 21, "Armor penetration": 0.73, "Max damage range": 2900, "Mobility": 12.7, "Reload time": 4, "Ammo in magazine": 10, "Ammo": 40},
        "FN-FAL": {"Type": "DMR", "Price": 3300, "Refill price": 400, "Slots": 6.5, "Damage": 37, "Headshot damage": 60, "Firerate": 4, "Recoil control": 23, "Armor penetration": 0.8, "Max damage range": 4700, "Mobility": 12.75, "Reload time": 3.5, "Ammo in magazine": 20, "Ammo": 80},
        "M60": {"Type": "LMG", "Price": 7000, "Refill price": 1500, "Slots": 7.5, "Damage": 23, "Headshot damage": 35, "Firerate": 7.7, "Recoil control": 25, "Armor penetration": 0.85, "Max damage range": 4100, "Mobility": 11, "Reload time": 8, "Ammo in magazine": 100, "Ammo": 200},
        "Mare": {"Type": "Sniper Rifle", "Price": 4000, "Refill price": 400, "Slots": 5, "Damage": 60, "Headshot damage": 120, "Firerate": 1, "Recoil control": 65, "Armor penetration": 0.8, "Max damage range": 4250, "Mobility": 14, "Reload time": 3.6, "Ammo in magazine": 6, "Ammo": 24},
        "Scout": {"Type": "Sniper Rifle", "Price": 6000, "Refill price": 600, "Slots": 6.5, "Damage": 52, "Headshot damage": 121, "Firerate": 0.7, "Recoil control": 55, "Armor penetration": 0.8, "Max damage range": 6350, "Mobility": 14, "Reload time": 4.5, "Ammo in magazine": 10, "Ammo": 30},
        "Savage": {"Type": "Sniper Rifle", "Price": 9000, "Refill price": 800, "Slots": 7, "Damage": 75, "Headshot damage": 150, "Firerate": 0.6, "Recoil control": 77, "Armor penetration": 0.8, "Max damage range": 12300, "Mobility": 13.25, "Reload time": 3.75, "Ammo in magazine": 5, "Ammo": 20},
        "BFG": {"Type": "Sniper Rifle", "Price": 18000, "Refill price": 1400, "Slots": 8, "Damage": 130, "Headshot damage": 130, "Firerate": 1, "Recoil control": 125, "Armor penetration": 0.99, "Max damage range": 27300, "Mobility": 11, "Reload time": 4.5, "Ammo in magazine": 1, "Ammo": 5},
        "Firework Launcher": {"Type": "Launcher", "Price": 1776, "Refill price": 500, "Slots": 7.5, "Damage": 60, "Headshot damage": 60, "Firerate": 1, "Recoil control": 40, "Armor penetration": 1, "Max damage range": 99999, "Mobility": 13, "Reload time": 4, "Ammo in magazine": 1, "Ammo": 3},
        "M320": {"Type": "Launcher", "Price": 8000, "Refill price": 850, "Slots": 4.5, "Damage": 175, "Headshot damage": 175, "Firerate": 1.5, "Recoil control": 20, "Armor penetration": 1, "Max damage range": 5000, "Mobility": 15, "Reload time": 3.5, "Ammo in magazine": 1, "Ammo": 6},
        "RPG": {"Type": "Launcher", "Price": 12000, "Refill price": 1000, "Slots": 8, "Damage": 185, "Headshot damage": 185, "Firerate": 1, "Recoil control": 80, "Armor penetration": 1, "Max damage range": 99999, "Mobility": 12, "Reload time": 6, "Ammo in magazine": 1, "Ammo": 3},
        "AT4": {"Type": "Launcher", "Price": 7500, "Refill price": 0, "Slots": 6, "Damage": 230, "Headshot damage": 230, "Firerate": 1, "Recoil control": 80, "Armor penetration": 1, "Max damage range": 99999, "Mobility": 12, "Reload time": 0, "Ammo in magazine": 1, "Ammo": 1},
        "Musket": {"Type": "Muzzle-Loading Rifle", "Price": 2990, "Refill price": 300, "Slots": 7, "Damage": 102, "Headshot damage": 138, "Firerate": 1, "Recoil control": 55, "Armor penetration": 0.99, "Max damage range": 2600, "Mobility": 11, "Reload time": 7, "Ammo in magazine": 1, "Ammo": 6}
    },
    "Melees": {
        "Wrench": {"Type": "Blunt", "Price": 20, "Slots": 1.5, "Damage": 23, "Bleeding Damage": 0, "Stamina": 3, "Attack Cooldown": 0.6, "Attack Delay": 0.2, "Attack time": 0.1, "Stun time": 0.3, "Mobility": 8, "Can block": 0, "How many effects can inflict": 2},
        "Crowbar": {"Type": "Blunt", "Price": 50, "Slots": 3.5, "Damage": 34, "Bleeding Damage": 0, "Stamina": 15, "Attack Cooldown": 1.2, "Attack Delay": 0.3, "Attack time": 0.2, "Stun time": 0.5, "Mobility": 7, "Can block": 0, "How many effects can inflict": 2},
        "Golf Club": {"Type": "Blunt", "Price": 55, "Slots": 4, "Damage": 39, "Bleeding Damage": 0, "Stamina": 9, "Attack Cooldown": 1.2, "Attack Delay": 0.3, "Attack time": 0.2, "Stun time": 0.5, "Mobility": 7, "Can block": 0, "How many effects can inflict": 2},
        "Shovel": {"Type": "Blunt", "Price": 60, "Slots": 4, "Damage": 60, "Bleeding Damage": 0, "Stamina": 14, "Attack Cooldown": 2.5, "Attack Delay": 0.5, "Attack time": 0.3, "Stun time": 0, "Mobility": 6.5, "Can block": 0, "How many effects can inflict": 2},
        "Bat": {"Type": "Blunt", "Price": 65, "Slots": 4, "Damage": 34, "Bleeding Damage": 0, "Stamina": 8, "Attack Cooldown": 1.2, "Attack Delay": 0.4, "Attack time": 0.2, "Stun time": 0.4, "Mobility": 6.5, "Can block": 13, "How many effects can inflict": 2},
        "Baton": {"Type": "Blunt", "Price": 160, "Slots": 2, "Damage": 18, "Bleeding Damage": 0, "Stamina": 4, "Attack Cooldown": 0.5, "Attack Delay": 0.1, "Attack time": 0.1, "Stun time": 0.3, "Mobility": 8, "Can block": 5, "How many effects can inflict": 2},
        "Metal bat": {"Type": "Blunt", "Price": 325, "Slots": 4, "Damage": 39, "Bleeding Damage": 5, "Stamina": 11, "Attack Cooldown": 1.3, "Attack Delay": 0.5, "Attack time": 0.2, "Stun time": 0.5, "Mobility": 6.5, "Can block": 22, "How many effects can inflict": 3},
        "Sledgehammer": {"Type": "Blunt", "Price": 375, "Slots": 6, "Damage": 70, "Bleeding Damage": 5, "Stamina": 15, "Attack Cooldown": 2.2, "Attack Delay": 0.7, "Attack time": 0.3, "Stun time": 0.6, "Mobility": 5.65, "Can block": 22, "How many effects can inflict": 3},
        "Candy Crowbar": {"Type": "Blunt", "Price": 999, "Slots": 6, "Damage": 60, "Bleeding Damage": 0, "Stamina": 14, "Attack Cooldown": 2.5, "Attack Delay": 0.5, "Attack time": 0.3, "Stun time": 0, "Mobility": 7, "Can block": 0, "How many effects can inflict": 2},
        "Shiv": {"Type": "Blade", "Price": 10, "Slots": 0.5, "Damage": 18, "Bleeding Damage": 8, "Stamina": 1, "Attack Cooldown": 0.5, "Attack Delay": 0.1, "Attack time": 0.1, "Stun time": 0.3, "Mobility": 8, "Can block": 0, "How many effects can inflict": 2},
        "Bayonet": {"Type": "Blade", "Price": 35, "Slots": 1.5, "Damage": 24, "Bleeding Damage": 5, "Stamina": 4, "Attack Cooldown": 0.6, "Attack Delay": 0.2, "Attack time": 0.1, "Stun time": 0.2, "Mobility": 8, "Can block": 0, "How many effects can inflict": 2},
        "Taiga": {"Type": "Blade", "Price": 80, "Slots": 3, "Damage": 27, "Bleeding Damage": 7, "Stamina": 6, "Attack Cooldown": 0.7, "Attack Delay": 0.2, "Attack time": 0.1, "Stun time": 0.3, "Mobility": 8, "Can block": 16, "How many effects can inflict": 3},
        "Balisong": {"Type": "Blade", "Price": 70, "Slots": 1, "Damage": 18, "Bleeding Damage": 6, "Stamina": 3, "Attack Cooldown": 0.3, "Attack Delay": 0, "Attack time": 0.1, "Stun time": 0.2, "Mobility": 8, "Can block": 0, "How many effects can inflict": 2},
        "Rambo": {"Type": "Blade", "Price": 90, "Slots": 3, "Damage": 36, "Bleeding Damage": 15, "Stamina": 7, "Attack Cooldown": 0.8, "Attack Delay": 0.2, "Attack time": 0.1, "Stun time": 0.3, "Mobility": 8, "Can block": 0, "How many effects can inflict": 2},
        "Machete": {"Type": "Blade", "Price": 300, "Slots": 4, "Damage": 34, "Bleeding Damage": 7, "Stamina": 7, "Attack Cooldown": 0.3, "Attack Delay": 0.2, "Attack time": 0.1, "Stun time": 0.3, "Mobility": 8, "Can block": 20, "How many effects can inflict": 3},
        "Katana": {"Type": "Blade", "Price": 350, "Slots": 5, "Damage": 31, "Bleeding Damage": 7, "Stamina": 7, "Attack Cooldown": 0.6, "Attack Delay": 0.1, "Attack time": 0.2, "Stun time": 0.4, "Mobility": 8, "Can block": 18, "How many effects can inflict": 3},
        "Cursed Dagger": {"Type": "Blade", "Price": 999, "Slots": 3, "Damage": 33, "Bleeding Damage": 99999, "Stamina": 5, "Attack Cooldown": 1.5, "Attack Delay": 0.2, "Attack time": 0.1, "Stun time": 0.5, "Mobility": 8, "Can block": 0, "How many effects can inflict": 4},
        "Slayer Sword": {"Type": "Blade", "Price": 33333, "Slots": 9, "Damage": 170, "Bleeding Damage": 10, "Stamina": 22.5, "Attack Cooldown": 1.5, "Attack Delay": 0.4, "Attack time": 0.3, "Stun time": 1, "Mobility": 5.5, "Can block": 25, "How many effects can inflict": 4},
        "Scythe": {"Type": "Blade", "Price": 55555, "Slots": 9, "Damage": 55, "Bleeding Damage": 99999, "Stamina": 15, "Attack Cooldown": 1.1, "Attack Delay": 0.2, "Attack time": 0.3, "Stun time": 0.6, "Mobility": 6, "Can block": 24, "How many effects can inflict": 5},
        "Fallen Blade": {"Type": "Blade", "Price": 22222, "Slots": 7, "Damage": 56, "Bleeding Damage": 99999, "Stamina": 14, "Attack Cooldown": 1.1, "Attack Delay": 0.2, "Attack time": 0.2, "Stun time": 0.4, "Mobility": 8, "Can block": 23, "How many effects can inflict": 3},
        "Eradicator": {"Type": "Blade", "Price": 99999, "Slots": 4, "Damage": 308, "Bleeding Damage": 0, "Stamina": 5, "Attack Cooldown": 2, "Attack Delay": 0.2, "Attack time": 0.7, "Stun time": 2, "Mobility": 15.5, "Can block": 27, "How many effects can inflict": 2},
        "Black Bayonet": {"Type": "Blade", "Price": 999999, "Slots": 0, "Damage": 70, "Bleeding Damage": 5, "Stamina": 7, "Attack Cooldown": 0.5, "Attack Delay": 0.1, "Attack time": 0.1, "Stun time": 0.3, "Mobility": 8, "Can block": 0, "How many effects can inflict": 2},
        "Fists": {"Type": "Special", "Price": 0, "Slots": 0, "Damage": 12, "Bleeding Damage": 0, "Stamina": 4, "Attack Cooldown": 0.5, "Attack Delay": 0.2, "Attack time": 0.1, "Stun time": 0.2, "Mobility": 8, "Can block": 3, "How many effects can inflict": 2},
        "Knuckledusters": {"Type": "Special", "Price": 0, "Slots": 0, "Damage": 17, "Bleeding Damage": 0, "Stamina": 4, "Attack Cooldown": 0.5, "Attack Delay": 0.2, "Attack time": 0.1, "Stun time": 0.2, "Mobility": 8, "Can block": 3, "How many effects can inflict": 2},
        "Nunchucks": {"Type": "Special", "Price": 0, "Slots": 0, "Damage": 15, "Bleeding Damage": 0, "Stamina": 4, "Attack Cooldown": 0.4, "Attack Delay": 0.1, "Attack time": 0.1, "Stun time": 0.2, "Mobility": 8, "Can block": 2, "How many effects can inflict": 2},
        "Fire Axe": {"Type": "Special", "Price": 150, "Slots": 4, "Damage": 55, "Bleeding Damage": 15, "Stamina": 11, "Attack Cooldown": 1.6, "Attack Delay": 0.6, "Attack time": 0.1, "Stun time": 0.6, "Mobility": 6, "Can block": 0, "How many effects can inflict": 3},
        "Chainsaw": {"Type": "Special", "Price": 400, "Slots": 6, "Damage": 208, "Bleeding Damage": 5, "Stamina": 35, "Attack Cooldown": 3, "Attack Delay": 0.2, "Attack time": 1.6, "Stun time": 0.6, "Mobility": 5.5, "Can block": 0, "How many effects can inflict": 3}
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
        "T-1 Helmet": {"Price": 750, "Armor HP": 60, "Melee Resistance": 0.15, "Concusssion Reduction": 0.19, "Shell-Shock Reduction": 0.15, "Bleed Reduction": 0},
        "T-2 Helmet": {"Price": 1200, "Armor HP": 85, "Melee Resistance": 0.25, "Concusssion Reduction": 0.3, "Shell-Shock Reduction": 0.25, "Bleed Reduction": 0},
        "T-1 Vest": {"Price": 1500, "Armor HP": 85, "Melee Resistance": 0.19, "Bleed Reduction": 0.35, "Blast Resistance": 0.15, "Flame Resistance": 0.05, "Extra Slots": 3},
        "T-2 Vest": {"Price": 2300, "Armor HP": 100, "Melee Resistance": 0.27, "Bleed Reduction": 0.44, "Blast Resistance": 0.19, "Flame Resistance": 0.09, "Extra Slots": 4},
        "T-3 Kit": {"Price": 15000, "Armor HP": 200, "Melee Resistance": 0.35, "Bleed Reduction": 0.7, "Blast Resistance": 0.44, "Flame Resistance": 0.19, "Concusssion Reduction": 0.4, "Shell-Shock Reduction": 0.4, "Extra Slots": 6}
    }
}

FORBIDDEN_ITEMS = [
    "Pumpkin bomb", "Pumpkin  bomb", "Airstrike", "Precision strike",
    "UTS-15", "Firework Launcher", "Musket", "Hawkeye",
    "Candy Crowbar", "Cursed Dagger", "Slayer Sword", "Scythe",
    "Fallen Blade", "Eradicator", "Black Bayonet", "Knuckledusters", "Nunchuckss", "Nunchucks"
]

FIREARMS_HIGHER_BETTER = ["Damage", "Headshot damage", "Firerate", "Armor penetration", "Max damage range", "Mobility", "Ammo in magazine", "Ammo"]
FIREARMS_LOWER_BETTER = ["Price", "Refill price", "Slots", "Recoil control", "Reload time"]

MELEES_HIGHER_BETTER = ["Damage", "Bleeding Damage", "Attack time", "Stun time", "Mobility", "Can block", "How many effects can inflict"]
MELEES_LOWER_BETTER = ["Price", "Slots", "Stamina", "Attack Cooldown", "Attack Delay"]

def get_item_by_name(name):
    name_lower = name.strip().lower()
    for category, items in DATA.items():
        for item_key, stats in items.items():
            if item_key.lower() == name_lower:
                return item_key, stats, category
    return None, None, None

def safe_float_convert(val):
    if isinstance(val, (int, float)):
        return float(val)
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
    items = DATA[category]
    w1_key = next((k for k in items if k.lower() == wpn1_name.lower()), None)
    w2_key = next((k for k in items if k.lower() == wpn2_name.lower()), None)

    if not w1_key or not w2_key:
        print("[-] Одно или оба оружия не найдены в этой категории!")
        return

    stats1 = items[w1_key]
    stats2 = items[w2_key]

    print(f"\n[Сравнение] Результаты: {w1_key} vs {w2_key} ")
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
        print(f"[ПОБЕДИТЕЛЬ] {w1_key} эффективнее! (Побед по пунктам: {w1_wins} против {w2_wins})")
    elif w2_wins > w1_wins:
        print(f"[ПОБЕДИТЕЛЬ] {w2_key} эффективнее! (Побед по пунктам: {w2_wins} против {w1_wins})")
    else:
        print("[ПОБЕДИТЕЛЬ] Ничья! Оба предмета сбалансированы друг относительно друга.")

def main():
    while True:
        print("\n=== ГЛАВНОЕ МЕНЮ ===")
        print("1. Характеристики и расширенный анализ")
        print("2. Сравнить огнестрельное оружие")
        print("3. Сравнить оружие ближнего боя")
        print("4. Статистика игровой сессии")
        print("5. Генератор случайного набора")
        print("6. Анализатор ТТК / ОЗ мишени")
        print("7. Выход")

        choice = input("Выберите пункт меню (1-7): ").strip()

        if choice == "1":
            print("\n--- Режим 1: Анализ характеристик ---")
            print("1. Посмотреть характеристики конкретного предмета")
            print("2. Вывести глобальный ТОП оружия по выбранной характеристике")
            sub_mode = input("Выберите подрежим (1-2): ").strip()

            if sub_mode == "1":
                print("\nПолный список доступных предметов в базе данных:")
                for category, items in DATA.items():
                    print(f"  [{category}]: {', '.join(items.keys())}")

                name = input("\nВведите название интересующего предмета: ")
                item_key, stats, cat = get_item_by_name(name)
                if item_key:
                    print(f"\n[Инфо] Характеристики для [{cat}] -> {item_key}:")
                    for k, v in stats.items():
                        print(f"  - {k}: {v}")

                    if cat in ["Firearms", "Melees"]:
                        print("\n[Анализ] Меню сравнения:")
                        print("1. Показать оружие ЛУЧШЕ по конкретной характеристике")
                        print("2. Показать оружие ХУЖЕ по конкретной характеристике")
                        print("3. Показать оружие ЛУЧШЕ в общем итоге")
                        print("4. Показать оружие ХУЖЕ в общем итоге")
                        print("5. Пропустить и вернуться в главное меню")
                        sub_choice = input("Выберите вариант (1-5): ").strip()

                        higher_better_list = FIREARMS_HIGHER_BETTER if cat == "Firearms" else MELEES_HIGHER_BETTER
                        lower_better_list = FIREARMS_LOWER_BETTER if cat == "Firearms" else MELEES_LOWER_BETTER

                        if sub_choice in ["1", "2"]:
                            target_stat = input("Введите точное название характеристики (например, Damage): ").strip()
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

                                condition_text = "ЛУЧШЕ" if sub_choice == "1" else "ХУЖЕ"
                                print(f"\n[ТОП] Оружие, которое {condition_text} в '{actual_stat}', чем {item_key} (База: {base_val}):")
                                if results:
                                    for i, (name, val, diff) in enumerate(results, 1):
                                        print(f"  {i}. {name}: {val} (Разница: {diff:.2f})")
                                else:
                                    print("  Предметов, соответствующих условию, не найдено.")
                            else:
                                print("[-] Характеристика не найдена на данном предмете.")

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

                            condition_text = "В ЦЕЛОМ ЛУЧШЕ" if sub_choice == "3" else "В ЦЕЛОМ ХУЖЕ"
                            print(f"\n[ТОП] Оружие, которое {condition_text}, чем {item_key}:")
                            if results:
                                for i, (name, ow, bw, margin) in enumerate(results, 1):
                                    print(f"  {i}. {name} (Побед: {ow} vs {bw}) -> Перевес: {margin} очков")
                            else:
                                print("  Предметов, соответствующих условию, не найдено.")
                else:
                    print("[-] Предмет не найден.")

            elif sub_mode == "2":
                print("\nВыберите категорию для построения ТОПа:")
                print("1. Огнестрельное оружие (Firearms)")
                print("2. Оружие ближнего боя (Melees)")
                cat_choice = input("Ваш выбор (1-2): ").strip()
                cat = "Firearms" if cat_choice == "1" else "Melees" if cat_choice == "2" else None

                if cat:
                    sample_item = list(DATA[cat].values())[0]
                    available_stats = [k for k in sample_item.keys() if k != "Type"]
                    print(f"\nДоступные характеристики для категории {cat}:")
                    print(", ".join(available_stats))

                    target_stat = input("\nВведите интересующую характеристику: ").strip()
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

                        print(f"\n[ТОП] Рейтинг оружия по параметру '{actual_stat}' (от лучшего к худшему):")
                        for i, (wpn_name, val) in enumerate(results, 1):
                            print(f"  {i}. {wpn_name}: {val}")
                    else:
                        print("[-] Данная характеристика отсутствует.")
                else:
                    print("[-] Неверный выбор категории.")

        elif choice == "2":
            wpn1 = input("Введите первое огнестрельное оружие: ")
            wpn2 = input("Введите второе огнестрельное оружие: ")
            compare_weapons(wpn1, wpn2, "Firearms", FIREARMS_HIGHER_BETTER, FIREARMS_LOWER_BETTER)

        elif choice == "3":
            wpn1 = input("Введите первое оружие ближнего боя: ")
            wpn2 = input("Введите второе оружие ближнего боя: ")
            compare_weapons(wpn1, wpn2, "Melees", MELEES_HIGHER_BETTER, MELEES_LOWER_BETTER)

        elif choice == "4":
            print("\n--- НАЧАЛО СЕССИИ ---")
            try:
                start_money = float(input("Введите текущие деньги: "))
                start_xp = float(input("Введите текущий XP: "))
            except ValueError:
                print("[-] Баланс и опыт должны быть введены числами!")
                continue

            deaths = 0
            kills = 0
            assists = 0
            total_spent = 0.0
            bought_items = {}

            print("\nЗапись лога активна. Вводите названия купленных вещей или команды быстрого действия:")
            print("  'd' - Смерть")
            print("  'k' - Убийство врага")
            print("  'a' - Помощь в убийстве")
            print("Для остановки сессии введите ваше количество денег на данный момент (число).")

            while True:
                action = input("Действие / Вещь: ").strip()
                if not action:
                    continue

                if action.lower() == "d":
                    deaths += 1
                    print("[X] Смерть добавлена в лог.")
                    continue
                if action.lower() == "k":
                    kills += 1
                    print("[+] Убийство добавлено в лог.")
                    continue
                if action.lower() == "a":
                    assists += 1
                    print("[+] Ассист добавлен в лог.")
                    continue

                if action.replace('.', '', 1).isdigit():
                    end_money = float(action)
                    break

                item_key, item_stats, _ = get_item_by_name(action)
                display_name = item_key if item_key else action
                bought_items[display_name] = bought_items.get(display_name, 0) + 1

                if item_stats and "Price" in item_stats:
                    price = safe_float_convert(item_stats["Price"])
                    total_spent += price
                    print(f"[Куплено] Добавлено: {display_name} (${price:.2f})")
                else:
                    print(f"[Куплено] Добавлено: {display_name} (Цена отсутствует в БД)")

            try:
                end_xp = float(input("Введите финальный XP: "))
            except ValueError:
                print("Ошибка ввода. Опыт сессии приравнен к 0.")
                end_xp = start_xp

            kd_ratio = kills / deaths if deaths > 0 else float(kills)

            print("\n[Статистика] РЕЗУЛЬТАТЫ ИГРОВОЙ СЕССИИ:")
            print(f"  Чистый профит: ${end_money - start_money:.2f}")
            print(f"  Всего потрачено на закупки: ${total_spent:.2f}")
            print(f"  Заработано XP: {end_xp - start_xp:.2f}")
            print(f"  Статистика боя: Убийств: {kills} | Помощь: {assists} | Смертей: {deaths}")
            print(f"  Соотношение K/D: {kd_ratio:.2f}")
            print("  Приобретенное снаряжение:")
            if bought_items:
                for item, count in bought_items.items():
                    print(f"    - {item}: {count}x")
            else:
                print("    - Снаряжение не покупалось.")

        elif choice == "5":
            print("\n--- Выберите категорию стоимости набора ---")
            print("1. Дешёвый набор (Стоимость строго до $1000)")
            print("2. Обычный набор (С ограничением до $4000)")
            print("3. По установленной цене (Кастомное ограничение)")
            tier_choice = input("Ваш выбор (1-3): ").strip()

            if tier_choice == "1":
                max_budget = 1000
                num_extras_max = 1
            elif tier_choice == "2":
                max_budget = 4000
                num_extras_max = 3
            elif tier_choice == "3":
                try:
                    max_budget = float(input("Введите максимальный бюджет набора: "))
                    num_extras_max = 3
                except ValueError:
                    print("[-] Ошибка ввода. Переключение на стандартный лимит $4000.")
                    max_budget = 4000
                    num_extras_max = 3
            else:
                print("[-] Неверный выбор. По умолчанию выбран обычный режим ($4000).")
                max_budget = 4000
                num_extras_max = 3

            attempts = 0
            while True:
                attempts += 1
                if attempts > 300:
                    print("[-] Превышено число попыток генерации. Попробуйте изменить параметры или увеличить бюджет.")
                    break

                base_slots = 10
                used_slots = 0
                total_cost = 0
                loadout = []

                # Обновленный список брони: добавлена возможность выпадения по отдельности
                armor_options = [
                    "None",
                    "T-1 Helmet", "T-1 Vest", "T-1 Set",
                    "T-2 Helmet", "T-2 Vest", "T-2 Set"
                ]
                chosen_armor = random.choice(armor_options)

                if chosen_armor != "None":
                    tier = "T-1" if "T-1" in chosen_armor else "T-2"
                    has_helmet = "Helmet" in chosen_armor or "Set" in chosen_armor
                    has_vest = "Vest" in chosen_armor or "Set" in chosen_armor

                    desc_parts = []
                    if has_helmet:
                        total_cost += safe_float_convert(DATA["Armor"][f"{tier} Helmet"]["Price"])
                        desc_parts.append("Шлем")
                    if has_vest:
                        total_cost += safe_float_convert(DATA["Armor"][f"{tier} Vest"]["Price"])
                        base_slots += safe_float_convert(DATA["Armor"][f"{tier} Vest"]["Extra Slots"])
                        desc_parts.append("Жилет")

                    loadout.append(f"Броня: Комплект {tier} ({' + '.join(desc_parts)})")
                else:
                    loadout.append("Броня: Набор без брони")

                if total_cost > max_budget:
                    continue

                # Выбор холодного оружия
                valid_melees = [k for k in DATA["Melees"].keys() if k not in FORBIDDEN_ITEMS]
                melee = random.choice(valid_melees)
                m_stats = DATA["Melees"][melee]
                total_cost += safe_float_convert(m_stats.get("Price", 0))
                used_slots += safe_float_convert(m_stats.get("Slots", 0))
                loadout.append(f"Ближний бой: {melee}")

                if total_cost > max_budget:
                    continue

                # Выбор огнестрельного оружия
                valid_firearms = [k for k in DATA["Firearms"].keys() if k not in FORBIDDEN_ITEMS]
                firearm = random.choice(valid_firearms)
                f_stats = DATA["Firearms"][firearm]
                total_cost += safe_float_convert(f_stats.get("Price", 0))
                used_slots += safe_float_convert(f_stats.get("Slots", 0))
                loadout.append(f"Огнестрельное оружие: {firearm}")

                if total_cost > max_budget or used_slots > base_slots:
                    continue

                # Формирование пула доп. вещей с повышенным шансом для Bandage
                pool = []
                for cat in ["Throwables", "Misc"]:
                    for item, st in DATA[cat].items():
                        if item not in FORBIDDEN_ITEMS:
                            pool.append((item, st))

                if "Bandage" in DATA["Misc"]:
                    for _ in range(6):
                        pool.append(("Bandage", DATA["Misc"]["Bandage"]))

                num_extras = random.randint(0, num_extras_max)
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

                if total_cost > max_budget:
                    continue

                for item, count in misc_counts.items():
                    loadout.append(f"Дополнительно: {item} (x{count})")

                print("\n[Рандом] СЛУЧАЙНЫЙ НАБОР СГЕНЕРИРОВАН:")
                for line in loadout:
                    print("  " + line)
                print("-" * 30)
                print(f"[Слоты] Вес инвентаря: {used_slots} / {base_slots}")
                print(f"[Цена] Полная себестоимость: ${total_cost:.2f}")

                if tier_choice == "2" and total_cost > 4000:
                    print("\n[Внимание] ПРЕДУПРЕЖДЕНИЕ: Стоимость сборки перешагнула порог в $4000!")
                    reroll = input("Сгенерировать другой набор? (y/n): ").strip().lower()
                    if reroll in ['y', 'yes', '1']:
                        continue
                break

        elif choice == "6":
            wpn_name = input("Введите оружие: ")
            item_key, stats, cat = get_item_by_name(wpn_name)

            if not item_key or cat not in ["Firearms", "Melees", "Throwables"]:
                print("[-] Оружие не найдено или неприменимо для тестов урона.")
                continue

            hit_loc = input("Зона попадания (body / head)? ").strip().lower()
            if hit_loc not in ["head", "body"]:
                print("По умолчанию выбрано: body.")
                hit_loc = "body"

            if hit_loc == "head":
                valid_armor = [k for k in DATA["Armor"].keys() if "Helmet" in k or k == "T-3 Kit"]
            else:
                valid_armor = [k for k in DATA["Armor"].keys() if "Vest" in k or k == "T-3 Kit"]

            print("\nДоступная броня для этой зоны:")
            print("None, " + ", ".join(valid_armor))
            armor_choice = input("Выберите броню цели (Оставьте пустым для None): ").strip()

            target_hp = 100.0
            hits = 0

            a_key, armor_stats, a_cat = get_item_by_name(armor_choice)

            if a_key and a_key in valid_armor:
                armor_hp = safe_float_convert(armor_stats.get("Armor HP", 0))
                melee_res = safe_float_convert(armor_stats.get("Melee Resistance", 0))
                blast_res = safe_float_convert(armor_stats.get("Blast Resistance", 0))
                print(f"[ЗАЩИТА] На цели экипирован {a_key} ({armor_hp} ОЗ брони).")
            else:
                armor_hp = 0
                melee_res = blast_res = 0.0
                print("[Игрок] Цель не защищена броней.")

            if hit_loc == "head" and "Headshot damage" in stats:
                base_dmg = safe_float_convert(stats["Headshot damage"])
            else:
                base_dmg = safe_float_convert(stats.get("Damage", stats.get("Max Damage", 0)))

            if base_dmg <= 0:
                print("[-] Данный предмет наносит 0 единиц базового урона.")
                continue

            armor_pen = safe_float_convert(stats.get("Armor penetration", 1.0))
            is_melee = (cat == "Melees")
            is_launcher = (stats.get("Type") == "Launcher")

            print("-" * 30)

            while target_hp > 0:
                hits += 1
                current_target_dmg = 0

                if armor_hp > 0:
                    if is_melee:
                        current_target_dmg = base_dmg * (1 - melee_res)
                        armor_dmg = base_dmg * melee_res
                    elif is_launcher:
                        current_target_dmg = base_dmg * (1 - blast_res)
                        armor_dmg = base_dmg * blast_res
                    else:
                        current_target_dmg = base_dmg * armor_pen
                        armor_dmg = base_dmg * (1 - armor_pen)

                    target_hp -= current_target_dmg
                    armor_hp -= armor_dmg

                    if armor_hp <= 0:
                        print(f"[!] Точка {hits}: Броня цели ПОЛНОСТЬЮ СЛОМАНА!")
                else:
                    current_target_dmg = base_dmg
                    target_hp -= current_target_dmg

                if current_target_dmg <= 0 and armor_hp > 0:
                    print("[Внимание] Оружие бессильно против данной брони, урон заблокирован.")
                    break

            if target_hp <= 0:
                print(f"[Результат] На уничтожение цели потребовалось ударов/выстрелов: {hits}")

        elif choice == "7":
            print("Работа программы завершена.")
            break
        else:
            print("[-] Ошибка: выбран неверный пункт главного меню.")

if __name__ == "__main__":
    main()
