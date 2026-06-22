import json
import os
from datetime import datetime
import random


# ============================================================
# LAS TASAS DE CANVI 
# ============================================================
tasas = {
    "USD": 1.0,
    "EUR": 0.85,
    "GBP": 0.74,
    "JPY": 157.25,
    "CNY": 6.79,
    "ARS": 1631.60,    
    "MXN": 17.28,
    "COP": 3912.45,
    "BRL": 5.14,
}


# ============================================================
# ELS TEXTOS EN DIFERENTS IDIOMES
# ============================================================
textos = {
    "es_ar": {
        "idioma_nombre": "🇦🇷 Español Argentino (el mejor)",
        "bienvenido": "\n🤣 ¡Buenas! Esto es medio rústico pero funciona",
        "menu": "\n" + "="*50 + "\n🎸 QUE HACEMOS HOY?\n" + "="*50,
        "op1": "1. 💱 Convertir monedas (el clásico)",
        "op2": "2. 📊 Mis gastos (para no andar en rojo)",
        "op3": "3. 🚪 Salir (no me hagas llorar)",
        "elige": "🤘 Elegí una opción: ",
        "cantidad": "💰 Cuánta plata: ",
        "de": "💱 De qué moneda (ej: EUR, USD, ARS): ",
        "a": "💱 A qué moneda (ej: EUR, USD, ARS): ",
        "resultado": "🎸 RESULTADO:",
        "error_moneda": "❌ Esa moneda no existe, payaso",
        "guardar_pregunta": "\n🎭 ¿Guardamos esto como GASTO o INGRESO? (gasto/ingreso/no): ",
        "categoria": "📂 Categoría (comida, alquiler, vicio, etc): ",
        "descripcion": "📝 Contá la bocha (opcional): ",
        "guardado_ok": "✅ Listo, guardado como {}",
        "no_guardado": "Bueno, no lo guardamos (rata)",
        "error_numero": "❌ Eso no es un número, mostro. Aprendé a escribir",
        "config_divisa": "\n🤣 PRIMERA VEZ? VAMOS A CONFIGURAR",
        "pregunta_divisa": "📌 En qué moneda querés guardar tus gastos? (EUR, USD, ARS, MXN): ",
        "divisa_ok": "✅ Joya! Tus ahorros van en {}. No te la patines toda",
        # Cosas del gestor
        "gestor_titulo": "\n=== 🧓 MIS GASTOS (con chistes de El Yayo) ===",
        "gestor_op1": "1. 💸 Anotar GASTO (uh, otra vez vos)",
        "gestor_op2": "2. 💰 Anotar INGRESO (albricias!)",
        "gestor_op3": "3. 📜 Ver todo lo que gasté (no quiero saber)",
        "gestor_op4": "4. 📊 Por categoría (dónde se fue la plata)",
        "gestor_op5": "5. 💵 Cuánto me queda (balance)",
        "gestor_op6": "6. 🔙 Volver al menú principal",
        "gestor_elige": "🤘 Elegí: ",
        "gestor_monto": "💰 Monto: ",
        "gestor_divisa": "💱 En qué moneda me estás dando esto: ",
        "gestor_categoria": "📂 Categoría: ",
        "gestor_desc": "📝 Descripción (opcional): ",
        "exito_gasto": "💸 GASTO: {} {} → {} {} 🫠",
        "exito_ingreso": "💰 INGRESO: {} {} → {} {} 🎉",
        "sin_datos": "📭 No hay nada. Gastá algo, ratón!",
        "balance_titulo": "\n💵 LO QUE TE QUEDA (en {}) - dicho por Peter",
        "ingresos": "💰 Entró:",
        "gastos": "💸 Salió:",
        "balance": "🎸 Te queda:",
        "chau": "\n👋 Chau! Nos vimo en la próxima, dale que vo",
        "chau_chiste": "🎸 'Y si no ahorrás, te va a pasar como a Manganeta...'"
    },
    "es": {
        "idioma_nombre": "🇪🇸 Español",
        "bienvenido": "\n😂 ¡Buenas! Esto funciona a medias pero bueno",
        "menu": "\n" + "="*50 + "\n🎸 QUÉ HACEMOS?\n" + "="*50,
        "op1": "1. 💱 Convertir monedas",
        "op2": "2. 📊 Mis gastos",
        "op3": "3. 🚪 Salir",
        "elige": "🤘 Elige: ",
        "cantidad": "💰 Cantidad: ",
        "de": "💱 De (EUR, USD, ARS): ",
        "a": "💱 A (EUR, USD, ARS): ",
        "resultado": "🎸 RESULTADO:",
        "error_moneda": "❌ Moneda no válida",
        "guardar_pregunta": "\n🎭 ¿Guardar como GASTO o INGRESO? (gasto/ingreso/no): ",
        "categoria": "📂 Categoría: ",
        "descripcion": "📝 Descripción: ",              
        "guardado_ok": "✅ Guardado como {}",
        "no_guardado": "No guardado",
        "error_numero": "❌ Número inválido",
        "config_divisa": "\n😂 PRIMERA VEZ? CONFIGURAMOS",
        "pregunta_divisa": "📌 ¿Moneda para guardar? (EUR, USD, ARS, MXN): ",
        "divisa_ok": "✅ Guardando en {}",
        "gestor_titulo": "\n=== MIS GASTOS ===",
        "gestor_op1": "1. 💸 GASTO",
        "gestor_op2": "2. 💰 INGRESO",
        "gestor_op3": "3. 📜 Historial",
        "gestor_op4": "4. 📊 Por categoría",
        "gestor_op5": "5. 💵 Balance",
        "gestor_op6": "6. 🔙 Volver",
        "gestor_elige": "🤘 Elige: ",
        "gestor_monto": "💰 Monto: ",
        "gestor_divisa": "💱 Moneda: ",
        "gestor_categoria": "📂 Categoría: ",
        "gestor_desc": "📝 Descripción: ",
        "exito_gasto": "💸 GASTO: {} {} → {} {}",
        "exito_ingreso": "💰 INGRESO: {} {} → {} {}",
        "sin_datos": "📭 Sin datos",
        "balance_titulo": "\n💵 BALANCE (en {})",
        "ingresos": "💰 Ingresos:",
        "gastos": "💸 Gastos:",
        "balance": "Balance:",
        "chau": "\n👋 Adiós!",
        "chau_chiste": "🎸 Nos vemos!"
    },
    "ca": {
        "idioma_nombre": "🏴󠁥󠁳󠁰󠁿󠁧 Català",
        "bienvenido": "\n😂 Hola! Això funciona... més o menys",
        "menu": "\n" + "="*50 + "\n🎸 QUÈ FEM?\n" + "="*50,
        "op1": "1. 💱 Convertir monedes",
        "op2": "2. 📊 Les meves despeses",
        "op3": "3. 🚪 Sortir",
        "elige": "🤘 Tria: ",
        "cantidad": "💰 Quantitat: ",
        "de": "💱 De (EUR, USD, ARS): ",
        "a": "💱 A (EUR, USD, ARS): ",
        "resultado": "🎸 RESULTAT:",
        "error_moneda": "❌ Moneda no vàlida",
        "guardar_pregunta": "\n🎭 Guardar com a DESPESA o INGRÉS? (despesa/ingrés/no): ",
        "categoria": "📂 Categoria: ",
        "descripcion": "📝 Descripció: ",
        "guardado_ok": "✅ Guardat com a {}",
        "no_guardado": "No guardat",
        "error_numero": "❌ Número invàlid",
        "config_divisa": "\n😂 PRIMERA VEGADA? CONFIGUREM",
        "pregunta_divisa": "📌 Moneda per guardar? (EUR, USD, ARS, MXN): ",
        "divisa_ok": "✅ Guardant en {}",
        "gestor_titulo": "\n=== GESTOR DE DESPESES ===",
        "gestor_op1": "1. 💸 DESPESA",
        "gestor_op2": "2. 💰 INGRÉS",
        "gestor_op3": "3. 📜 Historial",
        "gestor_op4": "4. 📊 Per categoria",
        "gestor_op5": "5. 💵 Balanç",
        "gestor_op6": "6. 🔙 Tornar",
        "gestor_elige": "🤘 Tria: ",
        "gestor_monto": "💰 Quantitat: ",
        "gestor_divisa": "💱 Moneda: ",
        "gestor_categoria": "📂 Categoria: ",
        "gestor_desc": "📝 Descripció: ",
        "exito_gasto": "💸 DESPESA: {} {} → {} {}",
        "exito_ingreso": "💰 INGRÉS: {} {} → {} {}",
        "sin_datos": "📭 Sense dades",
        "balance_titulo": "\n💵 BALANÇ (en {})",
        "ingresos": "💰 Ingressos:",
        "gastos": "💸 Despeses:",
        "balance": "Balanç:",
        "chau": "\n👋 Adéu!",
        "chau_chiste": "🎸 Ens veiem!"
    },
    "en": {
        "idioma_nombre": "🇬🇧 English",
        "bienvenido": "\n😂 Hi! This kinda works",
        "menu": "\n" + "="*50 + "\n🎸 WHAT TO DO?\n" + "="*50,
        "op1": "1. 💱 Convert currency",
        "op2": "2. 📊 My expenses",
        "op3": "3. 🚪 Exit",
        "elige": "🤘 Choose: ",
        "cantidad": "💰 Amount: ",
        "de": "💱 From (EUR, USD, ARS): ",
        "a": "💱 To (EUR, USD, ARS): ",
        "resultado": "🎸 RESULT:",
        "error_moneda": "❌ Invalid currency",
        "guardar_pregunta": "\n🎭 Save as EXPENSE or INCOME? (expense/income/no): ",
        "categoria": "📂 Category: ",
        "descripcion": "📝 Description: ",
        "guardado_ok": "✅ Saved as {}",
        "no_guardado": "Not saved",
        "error_numero": "❌ Invalid number",
        "config_divisa": "\n😂 FIRST TIME? LET'S SET UP",
        "pregunta_divisa": "📌 Currency to save? (EUR, USD, ARS, MXN): ",
        "divisa_ok": "✅ Saving in {}",
        "gestor_titulo": "\n=== EXPENSE MANAGER ===",
        "gestor_op1": "1. 💸 EXPENSE",
        "gestor_op2": "2. 💰 INCOME",
        "gestor_op3": "3. 📜 History",
        "gestor_op4": "4. 📊 By category",
        "gestor_op5": "5. 💵 Balance",
        "gestor_op6": "6. 🔙 Back",
        "gestor_elige": "🤘 Choose: ",
        "gestor_monto": "💰 Amount: ",
        "gestor_divisa": "💱 Currency: ",
        "gestor_categoria": "📂 Category: ",
        "gestor_desc": "📝 Description: ",
        "exito_gasto": "💸 EXPENSE: {} {} → {} {}",
        "exito_ingreso": "💰 INCOME: {} {} → {} {}",
        "sin_datos": "📭 No data",
        "balance_titulo": "\n💵 BALANCE (in {})",
        "ingresos": "💰 Income:",
        "gastos": "💸 Expenses:",
        "balance": "Balance:",
        "chau": "\n👋 Bye!",
        "chau_chiste": "🎸 See you!"
    }
}


# ============================================================
# CHISTES DEL YAYO Y PETER
# ============================================================
chistes = {
    "es_ar": [
        "🤣 ¡PARÁ LA MANO! Te dije que ahorres, no que te compres un 0km",
        "🎸 '¿Viste que la plata no crece en los árboles?' - 'Y... Peter, andá a cantar'",
        "🧓 El Yayo: 'Yo con 2 pesos compraba el almacén entero'",
        "💸 Peter: 'Tengo un robot chivo que me chorea la plata'",
        "😎 'Manganeta, laucha... ¡gastaste todo en figuritas del Diego!'",
        "🎤 'Me aumentaron el dólar y no llego a fin de mes... reggae'",
        "🧓 '¿Ahorrar? Yo ahorro aire en un frasco, total es gratis'",
    ],
    "es": [
        "😂 ¡Ay madre! Te dije que ahorraras",
        "🎸 El dinero no crece en los árboles",
    ],
    "ca": [
        "😂 Ai mare! Et vaig dir que estalviessis",
        "🎸 Els diners no creixen als arbres",
    ],
    "en": [
        "😂 Oh dear! I told you to save",
        "🎸 Money doesn't grow on trees",
    ]
}


# ============================================================
# LA FÓRMULA MÁGICA PER CONVERTIR
# ============================================================
def convertir(monto, de_moneda, a_moneda):
    # Primero paso a USD (porque el dólar manda)
    if de_moneda not in tasas or a_moneda not in tasas:
        return None
    
    en_usd = monto / tasas[de_moneda]
    # Después convierto de USD a lo que quiero
    return en_usd * tasas[a_moneda]


def tirar_chiste(idioma):
    if idioma in chistes:
        print(f"\n🎭 {random.choice(chistes[idioma])}\n")


# ============================================================
# EL GESTOR DE DESPESES
# ============================================================
class MisGastos:
    def __init__(self):
        self.todas_las_cosas = []  # acá guardo todos los gastos
        self.mi_moneda = None      # en qué moneda quiero guardar
        self.idioma_actual = None  # qué idioma eligió el usuario
        self.archivo_idioma = "mi_idioma.json"
        self.archivo_config = "mi_config.json"
        self.archivo_datos = "mis_gastos.json"
        
        # Cargo todo (si está, sino lo creo)
        self.cargar_idioma()
        self.cargar_config()
        self.cargar_gastos()
    
    # ============================================================
    # CARGO EL IDIOMA (solo la primera vez pregunta)
    # ============================================================
    def cargar_idioma(self):
        if os.path.exists(self.archivo_idioma):
            with open(self.archivo_idioma, "r") as f:
                data = json.load(f)
                self.idioma_actual = data.get("idioma")
        
        if not self.idioma_actual:
            print("\n" + "="*60)
            print("🌍 HOLA! EN QUÉ IDIOMA QUERÉS HABLAR?")
            print("1. 🇦🇷 Español Argentino (con chistes y todo)")
            print("2. 🇪🇸 Español")
            print("3. 🏴󠁥󠁳󠁰󠁿󠁧 Català")
            print("4. 🇬🇧 English")
            
            opcion = input("Elegí (1,2,3,4): ")
            
            if opcion == "1":
                self.idioma_actual = "es_ar"
            elif opcion == "2":
                self.idioma_actual = "es"
            elif opcion == "3":
                self.idioma_actual = "ca"
            else:
                self.idioma_actual = "en"
            
            with open(self.archivo_idioma, "w") as f:
                json.dump({"idioma": self.idioma_actual}, f)
            
            print(f"\n✅ Guardé '{self.idioma_actual}' como tu idioma. No te voy a joder más!")
    
    # ============================================================
    # CONFIGURO LA MONEDA PER GUARDARLA
    # ============================================================
    def cargar_config(self):
        t = textos[self.idioma_actual]
        
        if os.path.exists(self.archivo_config):
            with open(self.archivo_config, "r") as f:
                data = json.load(f)
                self.mi_moneda = data.get("moneda")
        
        if not self.mi_moneda:
            print(t["config_divisa"])
            while True:
                moneda = input(t["pregunta_divisa"]).upper()
                if moneda in tasas:
                    self.mi_moneda = moneda
                    with open(self.archivo_config, "w") as f:
                        json.dump({"moneda": moneda}, f)
                    print(t["divisa_ok"].format(moneda))
                    tirar_chiste(self.idioma_actual)
                    break
                else:
                    print(t["error_moneda"])
    
    # ============================================================
    # CARREGO LES DESPESES 
    # ============================================================
    def cargar_gastos(self):
        if os.path.exists(self.archivo_datos):
            with open(self.archivo_datos, "r") as f:
                self.todas_las_cosas = json.load(f)
    
    # ============================================================
    # GUARDO LES DESPESES
    # ============================================================
    def guardar_gastos(self):
        with open(self.archivo_datos, "w") as f:
            json.dump(self.todas_las_cosas, f, indent=2)
    
    # ============================================================
    # ANOTAR UNA DESPESA O INGRES
    # ============================================================
    def anotar(self, tipo, monto_original, de_que_moneda, categoria, descripcion=""):
        t = textos[self.idioma_actual]
        
        
        monto_convertido = convertir(monto_original, de_que_moneda, self.mi_moneda)
        
        if monto_convertido is None:
            print(t["error_moneda"])
            return False
        
        registro = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tipo": tipo,
            "monto_original": monto_original,
            "moneda_original": de_que_moneda,
            "monto_final": round(monto_convertido, 2),
            "moneda_final": self.mi_moneda,
            "categoria": categoria if categoria else "sin categoria",
            "descripcion": descripcion
        }
        
        self.todas_las_cosas.append(registro)
        self.guardar_gastos()
        
        if tipo in ["gasto", "despesa", "expense"]:
            print(t["exito_gasto"].format(monto_original, de_que_moneda, round(monto_convertido, 2), self.mi_moneda))
        else:
            print(t["exito_ingreso"].format(monto_original, de_que_moneda, round(monto_convertido, 2), self.mi_moneda))
        
        return True
    
    # ============================================================
    # VEURE TOT EL HISTORIAL
    # ============================================================
    def ver_historial(self):
        t = textos[self.idioma_actual]
        
        if not self.todas_las_cosas:
            print(t["sin_datos"])
            return
        
        print("\n" + "="*70)
        print(f"📋 TODO LO QUE GASTÉ/INGRESÉ (en {self.mi_moneda})")
        print("="*70)
        
        for cosa in self.todas_las_cosas[-15:]:  # muestro las últimas 15
            if cosa["tipo"] in ["ingreso", "ingrés", "income"]:
                emoji = "💰"
            else:
                emoji = "💸"
            
            print(f"{emoji} {cosa['fecha'][:16]} | {cosa['tipo']} | {cosa['categoria']}")
            print(f"   --> Me diste: {cosa['monto_original']} {cosa['moneda_original']}")
            print(f"   --> Yo guardé: {cosa['monto_final']} {cosa['moneda_final']}")
            if cosa['descripcion']:
                print(f"   📝 {cosa['descripcion']}")
            print("-"*40)
        
        print("="*70)
    
    # ============================================================
    # RESUM PER CATEGORÍA
    # ============================================================
    def resumen_por_categoria(self):
        t = textos[self.idioma_actual]
        
        if not self.todas_las_cosas:
            print(t["sin_datos"])
            return
        
        categorias = {}
        
        for cosa in self.todas_las_cosas:
            cat = cosa["categoria"]
            if cat not in categorias:
                categorias[cat] = {"gasto": 0, "ingreso": 0}
            
            if cosa["tipo"] in ["gasto", "despesa", "expense"]:
                categorias[cat]["gasto"] += cosa["monto_final"]
            else:
                categorias[cat]["ingreso"] += cosa["monto_final"]
        
        print("\n" + "="*50)
        print(f"📊 POR CATEGORÍA ({self.mi_moneda})")
        print("="*50)
        
        for cat, valores in categorias.items():
            balance = valores["ingreso"] - valores["gasto"]
            print(f"📌 {cat}")
            print(f"   💸 Gastos: {valores['gasto']:.2f}")
            print(f"   💰 Ingresos: {valores['ingreso']:.2f}")
            if balance >= 0:
                print(f"   🟢 Balance: {balance:.2f}")
            else:
                print(f"   🔴 Balance: {balance:.2f} (estás en roja, mostro!)")
            print("")
        
        print("="*50)
    
    # ============================================================
    # TOTAL
    # ============================================================
    def balance_total(self):
        t = textos[self.idioma_actual]
        
        total_gastos = 0
        total_ingresos = 0
        
        for cosa in self.todas_las_cosas:
            if cosa["tipo"] in ["gasto", "despesa", "expense"]:
                total_gastos += cosa["monto_final"]
            else:
                total_ingresos += cosa["monto_final"]
        
        balance = total_ingresos - total_gastos
        
        print(t["balance_titulo"].format(self.mi_moneda))
        print("="*40)
        print(f"{t['ingresos']} {total_ingresos:.2f}")
        print(f"{t['gastos']} {total_gastos:.2f}")
        print(f"{t['balance']} {balance:.2f}")
        print("="*40)
        
        if balance < 0 and self.idioma_actual == "es_ar":
            print("\n🤣 El Yayo: '¡Pará la mano! Estás en rojo, mostro! Ganá más o gastá menos!'")
        
        return balance
    
    # ============================================================
    # EL MENÚ DEL GESTOR
    # ============================================================
    def menu_gestor(self):
        t = textos[self.idioma_actual]
        
        while True:
            print(t["gestor_titulo"])
            print(f"💾 Estoy guardando todo en: {self.mi_moneda}")
            print(t["gestor_op1"])
            print(t["gestor_op2"])
            print(t["gestor_op3"])
            print(t["gestor_op4"])
            print(t["gestor_op5"])
            print(t["gestor_op6"])
            
            op = input(t["gestor_elige"])
            
            if op == "1" or op == "2":
                try:
                    monto = float(input(t["gestor_monto"]))
                    moneda = input(t["gestor_divisa"]).upper()
                    categoria = input(t["gestor_categoria"])
                    desc = input(t["gestor_desc"])
                    
                    if op == "1":
                        tipo = "gasto"
                        if self.idioma_actual == "es_ar":
                            print("🧓 El Yayo: 'Uh, otro gasto... pará la mano!'")
                    else:
                        tipo = "ingreso"
                        if self.idioma_actual == "es_ar":
                            print("💰 Peter: '¡Albricias! Llegó la plata, no la gastes toda!'")
                    
                    self.anotar(tipo, monto, moneda, categoria, desc)
                    tirar_chiste(self.idioma_actual)
                    
                except:
                    print(t["error_numero"])
            
            elif op == "3":
                self.ver_historial()
            
            elif op == "4":
                self.resumen_por_categoria()
            
            elif op == "5":
                self.balance_total()
            
            elif op == "6":
                print(t["volver"])
                break
            
            else:
                print("❌ Eso no es una opción válida, mostro!")


# ============================================================
# EL CONVERSOR DE DIVISES
# ============================================================
def conversor(mis_gastos):
    t = textos[mis_gastos.idioma_actual]
    
    try:
        monto = float(input(t["cantidad"]))
        de_moneda = input(t["de"]).upper()
        a_moneda = input(t["a"]).upper()
        
        resultado = convertir(monto, de_moneda, a_moneda)
        
        if resultado is None:
            print(t["error_moneda"])
            return
        
        print(f"\n{t['resultado']} {round(resultado, 2)} {a_moneda}")
        
        guardar = input(t["guardar_pregunta"]).lower()
        
        if guardar in ["gasto", "ingreso", "despesa", "ingrés", "expense", "income"]:
            if guardar in ["gasto", "despesa", "expense"]:
                tipo_gasto = "gasto"
                if mis_gastos.idioma_actual == "es_ar":
                    print("🧓 El Yayo: 'Uh, otro gasto... pará la mano!'")
            else:
                tipo_gasto = "ingreso"
                if mis_gastos.idioma_actual == "es_ar":
                    print("💰 Peter: '¡Albricias! Llegó la plata!'")
            
            categoria = input(t["categoria"])
            desc = input(t["descripcion"])
            if a_moneda != mis_gastos.mi_moneda:
                monto_final = convertir(resultado, a_moneda, mis_gastos.mi_moneda)
            else:
                monto_final = resultado
            
            if monto_final is None:
                print(t["error_moneda"])
                return
            
            # Creo el registro manualmente (porque viene del conversor)
            registro = {
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tipo": tipo_gasto,
                "monto_original": monto,
                "moneda_original": de_moneda,
                "monto_final": round(monto_final, 2),
                "moneda_final": mis_gastos.mi_moneda,
                "categoria": categoria if categoria else "conversión",
                "descripcion": f"[Conv] {desc}" if desc else "[Conversión]"
            }
            
            mis_gastos.todas_las_cosas.append(registro)
            mis_gastos.guardar_gastos()
            
            print(t["guardado_ok"].format(tipo_gasto))
            tirar_chiste(mis_gastos.idioma_actual)
        else:
            print(t["no_guardado"])
            
    except:
        print(t["error_numero"])


# ============================================================
# PRINCIPAL
# ============================================================
def main():
   
    mis_gastos = MisGastos()
    
    t = textos[mis_gastos.idioma_actual]
    print(t["bienvenido"])
    
    while True:
        print(t["menu"])
        print(t["op1"])
        print(t["op2"])
        print(t["op3"])
        
        opcion = input(t["elige"])
        
        if opcion == "1":
            conversor(mis_gastos)
        
        elif opcion == "2":
            mis_gastos.menu_gestor()
        
        elif opcion == "3":
            print(t["chau"])
            print(t["chau_chiste"])
            break
        
        else:
            print("❌ Eso no es 1, 2 o 3. Aprendé a leer, mostro!")


# ============================================================
# ARRANCA EL PROGRAMA
# ============================================================
if __name__ == "__main__":
    main()