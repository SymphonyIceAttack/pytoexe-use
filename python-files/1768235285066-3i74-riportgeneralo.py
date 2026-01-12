# DEMO verzió
import datetime

def generate_report_demo():
    print("DEMO: Riport generálás... csak példaadatokkal")
    print("Dátum:", datetime.date.today())
    print("Összesített érték: 1000")
    
generate_report_demo()

# PRO verzió
def generate_report_pro(data):
    print("PRO: Teljes riport generálás")
    total = sum(data)
    print("Dátum:", datetime.date.today())
    print("Összesített érték:", total)