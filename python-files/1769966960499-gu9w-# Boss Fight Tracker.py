# Boss Fight Tracker
# Salva questo file come boss_tracker.py
# Puoi eseguirlo con: python boss_tracker.py

def main():
    print("=== Boss Fight Tracker ===")

    # Impostazioni iniziali
    boss_hp = int(input("Inserisci HP iniziale del boss: "))
    boss_san = int(input("Inserisci SAN iniziale del boss: "))

    # Parametri della meccanica
    hp_threshold = boss_hp / 2  # soglia: metà HP
    hp_to_san_ratio_above = 1   # SAN persa per ogni 10 HP sopra soglia
    hp_to_san_ratio_below = 2   # SAN persa per ogni 10 HP sotto soglia

    round_num = 1

    while boss_hp > 0 and boss_san > 0:
        print(f"\n--- Turno {round_num} ---")
        print(f"HP boss: {boss_hp} | SAN boss: {boss_san}")

        # Input danni HP
        try:
            damage_hp = int(input("Danno totale HP subito dal boss questo turno: "))
        except:
            damage_hp = 0

        # Calcolo SAN persa dal danno HP
        if boss_hp - damage_hp < hp_threshold:
            san_loss = (damage_hp // 10) * hp_to_san_ratio_below
        else:
            san_loss = (damage_hp // 10) * hp_to_san_ratio_above

        # Aggiornamento HP e SAN
        boss_hp -= damage_hp
        boss_san -= san_loss

        if boss_hp < 0:
            boss_hp = 0
        if boss_san < 0:
            boss_san = 0

        # Input danno da pozione SAN
        try:
            potion_san = int(input("SAN inflitta al boss da pozioni questo turno: "))
        except:
            potion_san = 0

        boss_san -= potion_san
        if boss_san < 0:
            boss_san = 0

        print(f"Risultato turno {round_num}_
