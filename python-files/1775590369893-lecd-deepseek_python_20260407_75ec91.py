"""
Aplicación de Evaluación de Soluciones Energéticas
Interfaz gráfica con tkinter y matplotlib.
Autor: Asistente de IA
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math
import json
from dataclasses import dataclass, asdict
from datetime import datetime
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# ============================================================================
# CONSTANTES Y PARÁMETROS GLOBALES
# ============================================================================

TIPO_CAMBIO_MXN_USD = 18.57
IVA = 0.16
INFLACION_ANUAL = 0.05
INCREMENTO_TARIFA_CFE = 0.04
TASA_DESCUENTO = 0.10
FEC = 0.000435
FECOGEN = 0.0002
HORAS_SOLARES_POR_DIA = 5.5
HORAS_OPERACION_COGEN = 24 * 365 * 0.95

# ============================================================================
# ESTRUCTURAS DE DATOS (igual que antes)
# ============================================================================

@dataclass
class Cliente:
    razon_social: str = ""
    ubicacion: str = ""
    modelo_operacion: str = "24/7"
    demanda_electrica_kw: float = 500.0
    capacidad_transformador_kva: float = 1500.0
    tarifa_cfe: str = "GDMTH"
    horas_base_verano: int = 4
    horas_intermedio_verano: int = 16
    horas_punta_verano: int = 2
    horas_base_invierno: int = 4
    horas_intermedio_invierno: int = 14
    horas_punta_invierno: int = 4
    porcentaje_demanda_cubrir: str = "PARCIAL"
    demanda_termica: bool = False
    suministro_combustible: str = "N/A"
    temperatura_requerida_c: float = 0.0
    giro_sector: str = ""
    area_suelo_m2: float = 0.0
    area_techo_m2: float = 0.0
    plan_expansion: str = "NULO"
    recurso_solar_hse: str = ">5 HSE"
    recurso_eolico: bool = False
    acceso_ducto_gas: bool = False
    suministro_energia_actual: str = "CFE"
    enfoque_ambiental: str = "MEDIO"
    tipo_inversion: str = "Venta del proyecto al cliente"
    modo_operacion_red: str = "Interconectado a la red eléctrica de CFE"

@dataclass
class ReciboCFE:
    periodo: str = "ENE 25"
    kwh_base: float = 66765.0
    kwh_intermedio: float = 113555.0
    kwh_punta: float = 29349.0
    kw_base: float = 587.0
    kw_intermedio: float = 583.0
    kw_punta: float = 509.0
    factor_carga: float = 0.57
    dias_periodo: int = 31
    kvArh: float = 75037.0
    factor_potencia: float = 94.15
    tarifa: str = "GDMTH"
    multiplicador: int = 80
    precio_base: float = 0.9624
    precio_intermedio: float = 1.8859
    precio_punta: float = 2.1515
    cargo_fijo: float = 245.25

@dataclass
class ConfiguracionTecnologia:
    costo_panel_mxn: float = 2472.4
    costo_inversor_mxn: float = 116600
    costo_mantenimiento_anual_por_kwp_usd: float = 10.0
    eficiencia_sistema: float = 0.85
    degradacion_anual_pv: float = 0.005
    costo_turbina_por_kw_usd: float = 3000.0
    costo_mantenimiento_anual_por_kw_usd: float = 50.0
    eficiencia_electrica_turbina: float = 0.77
    precio_gas_natural_usd_por_mmbtu: float = 3.5
    costo_bateria_por_kwh_usd: float = 250.0
    costo_bateria_por_kw_usd: float = 300.0
    eficiencia_bateria: float = 0.9
    ciclos_vida: int = 10000
    degradacion_anual_bess: float = 0.02
    tipo_cambio: float = TIPO_CAMBIO_MXN_USD

# ============================================================================
# FUNCIONES DE CÁLCULO (idénticas a la versión anterior)
# ============================================================================

def calcular_generacion_fotovoltaica(area_m2: float, irradiancia_hse: float = 5.5,
                                     eficiencia_panel: float = 0.213,
                                     densidad_potencia_kwp_por_m2: float = 0.2) -> dict:
    area_por_panel_m2 = 2.382 * 1.134
    num_paneles = int(area_m2 / area_por_panel_m2) if area_m2 > 0 else 0
    potencia_instalada_kwp = num_paneles * 0.620
    generacion_anual_kwh = potencia_instalada_kwp * irradiancia_hse * 365 * 0.85
    return {
        "potencia_kwp": potencia_instalada_kwp,
        "num_paneles": num_paneles,
        "generacion_anual_kwh": generacion_anual_kwh,
        "area_utilizada_m2": num_paneles * area_por_panel_m2
    }

def calcular_cogeneracion(demanda_electrica_kw: float, demanda_termica: bool,
                          horas_operacion_dia: int = 24, dias_anio: int = 365,
                          eficiencia: float = 0.77) -> dict:
    potencia_turbina_kw = demanda_electrica_kw
    horas_operacion_anual = horas_operacion_dia * dias_anio * 0.95
    generacion_anual_kwh = potencia_turbina_kw * horas_operacion_anual
    consumo_energia_primaria_kwh = generacion_anual_kwh / eficiencia
    consumo_mmbtu_anual = consumo_energia_primaria_kwh * 3412 / 1e6
    return {
        "potencia_turbina_kw": potencia_turbina_kw,
        "generacion_anual_kwh": generacion_anual_kwh,
        "consumo_mmbtu_anual": consumo_mmbtu_anual,
        "horas_operacion_anual": horas_operacion_anual
    }

def calcular_baterias(energia_requerida_kwh: float, potencia_requerida_kw: float) -> dict:
    capacidad_kwh = energia_requerida_kwh
    potencia_kw = potencia_requerida_kw
    energia_util_anual_kwh = capacidad_kwh * 365 * 0.9
    return {
        "capacidad_kwh": capacidad_kwh,
        "potencia_kw": potencia_kw,
        "energia_util_anual_kwh": energia_util_anual_kwh
    }

def calcular_inversion_pv(potencia_kwp: float, config: ConfiguracionTecnologia) -> float:
    num_paneles = math.ceil(potencia_kwp / 0.620) if potencia_kwp > 0 else 0
    costo_paneles = num_paneles * config.costo_panel_mxn
    num_inversores = max(1, math.ceil(potencia_kwp / 100)) if potencia_kwp > 0 else 0
    costo_inversores = num_inversores * config.costo_inversor_mxn
    estructura = 40000 if potencia_kwp > 0 else 0
    componentes = 50000 if potencia_kwp > 0 else 0
    total = costo_paneles + costo_inversores + estructura + componentes
    return total * (1 + IVA)

def calcular_opex_pv(potencia_kwp: float, config: ConfiguracionTecnologia) -> float:
    return potencia_kwp * config.costo_mantenimiento_anual_por_kwp_usd * config.tipo_cambio

def calcular_inversion_cogen(potencia_kw: float, config: ConfiguracionTecnologia) -> float:
    costo_usd = potencia_kw * config.costo_turbina_por_kw_usd
    return costo_usd * config.tipo_cambio * (1 + IVA)

def calcular_opex_cogen(potencia_kw: float, config: ConfiguracionTecnologia,
                        consumo_mmbtu_anual: float) -> float:
    oym_usd = potencia_kw * config.costo_mantenimiento_anual_por_kw_usd
    combustible_usd = consumo_mmbtu_anual * config.precio_gas_natural_usd_por_mmbtu
    total_usd = oym_usd + combustible_usd
    return total_usd * config.tipo_cambio

def calcular_inversion_bess(capacidad_kwh: float, potencia_kw: float, config: ConfiguracionTecnologia) -> float:
    costo_usd = capacidad_kwh * config.costo_bateria_por_kwh_usd + potencia_kw * config.costo_bateria_por_kw_usd
    return costo_usd * config.tipo_cambio * (1 + IVA)

def calcular_ahorro_cfe(recibo: ReciboCFE, generacion_kwh: float,
                        generacion_kw_demanda: float = 0) -> float:
    precio_promedio = (recibo.precio_base + recibo.precio_intermedio + recibo.precio_punta) / 3
    ahorro_energia = generacion_kwh * precio_promedio
    ahorro_demanda = generacion_kw_demanda * recibo.precio_punta * 30
    return ahorro_energia + ahorro_demanda

def flujo_caja_anual(inversion_inicial: float, opex_anual: float, ahorro_anual: float,
                     años: int = 10, inflacion: float = INFLACION_ANUAL,
                     incremento_tarifa: float = INCREMENTO_TARIFA_CFE) -> list:
    flujo = [-inversion_inicial]
    for año in range(1, años+1):
        opex_actual = opex_anual * (1 + inflacion) ** (año-1)
        ahorro_actual = ahorro_anual * (1 + incremento_tarifa) ** (año-1)
        flujo.append(ahorro_actual - opex_actual)
    return flujo

def calcular_vna(flujo: list, tasa: float = TASA_DESCUENTO) -> float:
    return sum(cf / (1 + tasa)**i for i, cf in enumerate(flujo))

def calcular_tir(flujo: list) -> float:
    def vna_tasa(tasa):
        return sum(cf / (1 + tasa)**i for i, cf in enumerate(flujo))
    if vna_tasa(0) <= 0:
        return 0
    tir = 0.01
    while vna_tasa(tir) > 0 and tir < 1:
        tir += 0.01
    return tir

def calcular_payback(flujo: list) -> float:
    acumulado = 0
    for i, cf in enumerate(flujo):
        acumulado += cf
        if acumulado >= 0:
            if i == 0:
                return 0
            prev_acum = acumulado - cf
            fraccion = -prev_acum / cf if cf != 0 else 0
            return i - 1 + fraccion
    return float('inf')

def evaluar_viabilidad(cliente: Cliente, recibo: ReciboCFE) -> dict:
    if (cliente.modelo_operacion in ["24/7", "24/6"] and
        cliente.tarifa_cfe == "GDMTH" and
        cliente.demanda_termica and
        cliente.suministro_combustible in ["GND", "GNC", "GND y GNC"] and
        cliente.porcentaje_demanda_cubrir == "TOTAL" and
        cliente.recurso_solar_hse != ">5 HSE"):
        return {
            "recomendacion": "Cogeneración",
            "escenario": "Cogeneración a gas natural para autoconsumo total",
            "justificacion": "El sitio opera 24/7, tiene demanda térmica y acceso a gas natural."
        }
    elif (cliente.modelo_operacion in ["24/7", "24/6"] and
          cliente.tarifa_cfe == "GDMTH" and
          cliente.demanda_termica and
          cliente.suministro_combustible in ["GND", "GNC", "GND y GNC"] and
          cliente.porcentaje_demanda_cubrir in ["PARCIAL", "TOTAL"] and
          cliente.recurso_solar_hse == ">5 HSE" and
          cliente.area_techo_m2 + cliente.area_suelo_m2 >= 200):
        return {
            "recomendacion": "Cogeneración + Fotovoltaica",
            "escenario": "Sistema híbrido con turbinas de gas y paneles solares",
            "justificacion": "La cogeneración cubre la base, la FV reduce consumo en horario intermedio."
        }
    elif (cliente.modelo_operacion in ["24/7", "24/6"] and
          cliente.tarifa_cfe == "GDMTH" and
          not cliente.demanda_termica and
          cliente.recurso_solar_hse == ">5 HSE" and
          cliente.area_techo_m2 + cliente.area_suelo_m2 >= 100):
        return {
            "recomendacion": "Fotovoltaica + Almacenamiento (BESS)",
            "escenario": "FV para autoconsumo y BESS para gestión de punta",
            "justificacion": "Alta irradiación y operación continua. BESS desplaza consumo a punta."
        }
    elif (cliente.modelo_operacion in ["24/7", "24/6"] and
          cliente.tarifa_cfe == "GDMTH" and
          cliente.recurso_solar_hse != ">5 HSE" and
          not cliente.demanda_termica and
          cliente.porcentaje_demanda_cubrir in ["PARCIAL", "TOTAL"]):
        return {
            "recomendacion": "Sistema de Almacenamiento con Baterías",
            "escenario": "BESS para carga en horario base y descarga en punta",
            "justificacion": "Aprovecha diferencia tarifaria sin generación propia."
        }
    elif (cliente.recurso_solar_hse == ">5 HSE" and
          cliente.area_techo_m2 + cliente.area_suelo_m2 >= 50 and
          not cliente.demanda_termica):
        return {
            "recomendacion": "Fotovoltaica",
            "escenario": "Generación solar para autoconsumo en horario intermedio",
            "justificacion": "Recurso solar adecuado y área disponible."
        }
    else:
        return {
            "recomendacion": "No viable",
            "escenario": "Ninguna tecnología es claramente beneficiosa",
            "justificacion": "Condiciones del sitio no favorecen solución técnico-económica."
        }

def calcular_emisiones(recibo: ReciboCFE, generacion_pv_kwh: float, generacion_cogen_kwh: float) -> dict:
    consumo_anual_cfe = (recibo.kwh_base + recibo.kwh_intermedio + recibo.kwh_punta) * 12
    emisiones_sin_proyecto = consumo_anual_cfe * FEC
    emisiones_con_proyecto = (consumo_anual_cfe - generacion_pv_kwh - generacion_cogen_kwh) * FEC
    emisiones_generacion_cogen = generacion_cogen_kwh * FECOGEN
    reduccion_neta = emisiones_sin_proyecto - (emisiones_con_proyecto + emisiones_generacion_cogen)
    return {
        "emisiones_originales_tco2e": emisiones_sin_proyecto,
        "emisiones_finales_tco2e": emisiones_con_proyecto + emisiones_generacion_cogen,
        "reduccion_neta_tco2e": reduccion_neta,
        "reduccion_porcentual": (reduccion_neta / emisiones_sin_proyecto) * 100 if emisiones_sin_proyecto > 0 else 0
    }

def evaluar_proyecto(cliente: Cliente, recibo: ReciboCFE, config: ConfiguracionTecnologia) -> dict:
    viabilidad = evaluar_viabilidad(cliente, recibo)
    generacion_pv_kwh = 0
    generacion_cogen_kwh = 0
    generacion_bess_kwh = 0
    inversion_total = 0
    opex_anual = 0
    ahorro_anual = 0
    recomendacion = viabilidad["recomendacion"]

    if "Fotovoltaica" in recomendacion or "FV" in recomendacion:
        area_total = cliente.area_techo_m2 + cliente.area_suelo_m2
        pv = calcular_generacion_fotovoltaica(area_total)
        generacion_pv_kwh = pv["generacion_anual_kwh"]
        inversion_pv = calcular_inversion_pv(pv["potencia_kwp"], config)
        opex_pv = calcular_opex_pv(pv["potencia_kwp"], config)
        inversion_total += inversion_pv
        opex_anual += opex_pv
        ahorro_anual += calcular_ahorro_cfe(recibo, generacion_pv_kwh / 12) * 12

    if "Cogeneración" in recomendacion:
        cogen = calcular_cogeneracion(cliente.demanda_electrica_kw, cliente.demanda_termica)
        generacion_cogen_kwh = cogen["generacion_anual_kwh"]
        inversion_cogen = calcular_inversion_cogen(cogen["potencia_turbina_kw"], config)
        opex_cogen = calcular_opex_cogen(cogen["potencia_turbina_kw"], config, cogen["consumo_mmbtu_anual"])
        inversion_total += inversion_cogen
        opex_anual += opex_cogen
        ahorro_anual += calcular_ahorro_cfe(recibo, generacion_cogen_kwh / 12) * 12

    if "Almacenamiento" in recomendacion or "BESS" in recomendacion:
        potencia_bess = recibo.kw_punta
        energia_bess = potencia_bess * 2
        bess = calcular_baterias(energia_bess, potencia_bess)
        generacion_bess_kwh = bess["energia_util_anual_kwh"]
        inversion_bess = calcular_inversion_bess(bess["capacidad_kwh"], bess["potencia_kw"], config)
        opex_bess = inversion_bess * 0.02
        inversion_total += inversion_bess
        opex_anual += opex_bess
        ahorro_bess = generacion_bess_kwh * recibo.precio_punta
        ahorro_anual += ahorro_bess

    flujo = flujo_caja_anual(inversion_total, opex_anual, ahorro_anual)
    vna = calcular_vna(flujo)
    tir = calcular_tir(flujo)
    payback = calcular_payback(flujo)
    emisiones = calcular_emisiones(recibo, generacion_pv_kwh, generacion_cogen_kwh)

    resultado = {
        "cliente": asdict(cliente),
        "recibo": asdict(recibo),
        "viabilidad": viabilidad,
        "tecnologias": {
            "potencia_fv_kwp": generacion_pv_kwh / (HORAS_SOLARES_POR_DIA * 365) if generacion_pv_kwh > 0 else 0,
            "generacion_fv_anual_kwh": generacion_pv_kwh,
            "potencia_cogen_kw": generacion_cogen_kwh / HORAS_OPERACION_COGEN if generacion_cogen_kwh > 0 else 0,
            "generacion_cogen_anual_kwh": generacion_cogen_kwh,
            "capacidad_bess_kwh": 0,
            "generacion_bess_anual_kwh": generacion_bess_kwh
        },
        "financiero": {
            "inversion_total_mxn": inversion_total,
            "opex_anual_mxn": opex_anual,
            "ahorro_anual_mxn": ahorro_anual,
            "flujo_caja_anual_mxn": flujo,
            "VAN_mxn": vna,
            "TIR": tir,
            "payback_anios": payback
        },
        "ambiental": emisiones
    }
    return resultado

# ============================================================================
# APLICACIÓN GRÁFICA CON TKINTER
# ============================================================================

class EvaluadorEnergiaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Evaluador de Soluciones Energéticas - 3EGAS")
        self.root.geometry("1300x800")
        self.config = ConfiguracionTecnologia()
        self.resultado = None
        self.setup_ui()

    def setup_ui(self):
        # Crear pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)

        # Pestaña de entrada de datos
        self.frame_entrada = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_entrada, text="Datos del Proyecto")

        # Pestaña de resultados
        self.frame_resultados = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_resultados, text="Resultados y Gráficos")

        self.crear_widgets_entrada()
        self.crear_widgets_resultados()

    def crear_widgets_entrada(self):
        # Frame principal con scroll
        canvas = tk.Canvas(self.frame_entrada)
        scrollbar = ttk.Scrollbar(self.frame_entrada, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Sección Cliente
        ttk.Label(scrollable_frame, text="DATOS DEL CLIENTE", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=5, sticky="w")
        ttk.Label(scrollable_frame, text="Razón Social:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.entry_razon = ttk.Entry(scrollable_frame, width=40)
        self.entry_razon.grid(row=1, column=1, sticky="w", padx=5)
        self.entry_razon.insert(0, "ARTIFIBRAS S.A. DE C.V.")

        ttk.Label(scrollable_frame, text="Ubicación:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
        self.entry_ubicacion = ttk.Entry(scrollable_frame, width=40)
        self.entry_ubicacion.grid(row=2, column=1, sticky="w", padx=5)
        self.entry_ubicacion.insert(0, "BLVD. INDUSTRIAL #445, URUAPAN")

        ttk.Label(scrollable_frame, text="Modelo de Operación:").grid(row=3, column=0, sticky="e", padx=5, pady=2)
        self.combo_modelo = ttk.Combobox(scrollable_frame, values=["24/7", "24/6", "24/7 CON STAND-BY PARA EVITAR PUNTA"], state="readonly")
        self.combo_modelo.grid(row=3, column=1, sticky="w", padx=5)
        self.combo_modelo.set("24/7")

        ttk.Label(scrollable_frame, text="Demanda Eléctrica (kW):").grid(row=4, column=0, sticky="e", padx=5, pady=2)
        self.entry_demanda = ttk.Entry(scrollable_frame, width=15)
        self.entry_demanda.grid(row=4, column=1, sticky="w", padx=5)
        self.entry_demanda.insert(0, "500")

        ttk.Label(scrollable_frame, text="Capacidad Transformador (kVA):").grid(row=5, column=0, sticky="e", padx=5, pady=2)
        self.entry_transf = ttk.Entry(scrollable_frame, width=15)
        self.entry_transf.grid(row=5, column=1, sticky="w", padx=5)
        self.entry_transf.insert(0, "1500")

        ttk.Label(scrollable_frame, text="Tarifa CFE:").grid(row=6, column=0, sticky="e", padx=5, pady=2)
        self.combo_tarifa = ttk.Combobox(scrollable_frame, values=["GDMTH", "GDMTO"], state="readonly")
        self.combo_tarifa.grid(row=6, column=1, sticky="w", padx=5)
        self.combo_tarifa.set("GDMTH")

        ttk.Label(scrollable_frame, text="Porcentaje Demanda a Cubrir:").grid(row=7, column=0, sticky="e", padx=5, pady=2)
        self.combo_porcentaje = ttk.Combobox(scrollable_frame, values=["PARCIAL", "TOTAL"], state="readonly")
        self.combo_porcentaje.grid(row=7, column=1, sticky="w", padx=5)
        self.combo_porcentaje.set("PARCIAL")

        ttk.Label(scrollable_frame, text="Demanda Térmica (calor de proceso):").grid(row=8, column=0, sticky="e", padx=5, pady=2)
        self.var_termica = tk.BooleanVar(value=True)
        ttk.Checkbutton(scrollable_frame, variable=self.var_termica).grid(row=8, column=1, sticky="w", padx=5)

        ttk.Label(scrollable_frame, text="Suministro de Combustible:").grid(row=9, column=0, sticky="e", padx=5, pady=2)
        self.combo_combustible = ttk.Combobox(scrollable_frame, values=["N/A", "GND", "GNC", "GND y GNC"], state="readonly")
        self.combo_combustible.grid(row=9, column=1, sticky="w", padx=5)
        self.combo_combustible.set("GND")

        ttk.Label(scrollable_frame, text="Área en Techo (m²):").grid(row=10, column=0, sticky="e", padx=5, pady=2)
        self.entry_techo = ttk.Entry(scrollable_frame, width=15)
        self.entry_techo.grid(row=10, column=1, sticky="w", padx=5)
        self.entry_techo.insert(0, "72")

        ttk.Label(scrollable_frame, text="Área en Suelo (m²):").grid(row=11, column=0, sticky="e", padx=5, pady=2)
        self.entry_suelo = ttk.Entry(scrollable_frame, width=15)
        self.entry_suelo.grid(row=11, column=1, sticky="w", padx=5)
        self.entry_suelo.insert(0, "30")

        ttk.Label(scrollable_frame, text="Recurso Solar (HSE):").grid(row=12, column=0, sticky="e", padx=5, pady=2)
        self.combo_solar = ttk.Combobox(scrollable_frame, values=[">5 HSE", "<5 HSE", "N/A"], state="readonly")
        self.combo_solar.grid(row=12, column=1, sticky="w", padx=5)
        self.combo_solar.set(">5 HSE")

        ttk.Label(scrollable_frame, text="Acceso a Ducto de Gas:").grid(row=13, column=0, sticky="e", padx=5, pady=2)
        self.var_gas = tk.BooleanVar(value=True)
        ttk.Checkbutton(scrollable_frame, variable=self.var_gas).grid(row=13, column=1, sticky="w", padx=5)

        ttk.Label(scrollable_frame, text="Enfoque Ambiental:").grid(row=14, column=0, sticky="e", padx=5, pady=2)
        self.combo_ambiental = ttk.Combobox(scrollable_frame, values=["NULO", "BAJO", "MEDIO", "ALTO"], state="readonly")
        self.combo_ambiental.grid(row=14, column=1, sticky="w", padx=5)
        self.combo_ambiental.set("MEDIO")

        # Sección Recibo CFE
        ttk.Label(scrollable_frame, text="DATOS DEL RECIBO CFE", font=("Arial", 12, "bold")).grid(row=15, column=0, columnspan=2, pady=10, sticky="w")
        ttk.Label(scrollable_frame, text="kWh Base:").grid(row=16, column=0, sticky="e", padx=5, pady=2)
        self.entry_kwh_base = ttk.Entry(scrollable_frame, width=15)
        self.entry_kwh_base.grid(row=16, column=1, sticky="w", padx=5)
        self.entry_kwh_base.insert(0, "66765")

        ttk.Label(scrollable_frame, text="kWh Intermedio:").grid(row=17, column=0, sticky="e", padx=5, pady=2)
        self.entry_kwh_int = ttk.Entry(scrollable_frame, width=15)
        self.entry_kwh_int.grid(row=17, column=1, sticky="w", padx=5)
        self.entry_kwh_int.insert(0, "113555")

        ttk.Label(scrollable_frame, text="kWh Punta:").grid(row=18, column=0, sticky="e", padx=5, pady=2)
        self.entry_kwh_punta = ttk.Entry(scrollable_frame, width=15)
        self.entry_kwh_punta.grid(row=18, column=1, sticky="w", padx=5)
        self.entry_kwh_punta.insert(0, "29349")

        ttk.Label(scrollable_frame, text="kW Base:").grid(row=19, column=0, sticky="e", padx=5, pady=2)
        self.entry_kw_base = ttk.Entry(scrollable_frame, width=15)
        self.entry_kw_base.grid(row=19, column=1, sticky="w", padx=5)
        self.entry_kw_base.insert(0, "587")

        ttk.Label(scrollable_frame, text="kW Intermedio:").grid(row=20, column=0, sticky="e", padx=5, pady=2)
        self.entry_kw_int = ttk.Entry(scrollable_frame, width=15)
        self.entry_kw_int.grid(row=20, column=1, sticky="w", padx=5)
        self.entry_kw_int.insert(0, "583")

        ttk.Label(scrollable_frame, text="kW Punta:").grid(row=21, column=0, sticky="e", padx=5, pady=2)
        self.entry_kw_punta = ttk.Entry(scrollable_frame, width=15)
        self.entry_kw_punta.grid(row=21, column=1, sticky="w", padx=5)
        self.entry_kw_punta.insert(0, "509")

        ttk.Label(scrollable_frame, text="Factor de Potencia (%):").grid(row=22, column=0, sticky="e", padx=5, pady=2)
        self.entry_fp = ttk.Entry(scrollable_frame, width=15)
        self.entry_fp.grid(row=22, column=1, sticky="w", padx=5)
        self.entry_fp.insert(0, "94.15")

        ttk.Label(scrollable_frame, text="Días del Periodo:").grid(row=23, column=0, sticky="e", padx=5, pady=2)
        self.entry_dias = ttk.Entry(scrollable_frame, width=15)
        self.entry_dias.grid(row=23, column=1, sticky="w", padx=5)
        self.entry_dias.insert(0, "31")

        # Botón Evaluar
        ttk.Button(scrollable_frame, text="Evaluar Proyecto", command=self.evaluar, width=20).grid(row=24, column=0, columnspan=2, pady=20)

    def crear_widgets_resultados(self):
        # Frame para resultados de texto
        frame_texto = ttk.LabelFrame(self.frame_resultados, text="Resultados de la Evaluación")
        frame_texto.pack(fill="both", expand=True, padx=10, pady=5)

        self.text_resultados = tk.Text(frame_texto, wrap="word", height=15, font=("Consolas", 10))
        scroll_texto = ttk.Scrollbar(frame_texto, orient="vertical", command=self.text_resultados.yview)
        self.text_resultados.configure(yscrollcommand=scroll_texto.set)
        self.text_resultados.pack(side="left", fill="both", expand=True)
        scroll_texto.pack(side="right", fill="y")

        # Frame para gráficos
        frame_grafico = ttk.LabelFrame(self.frame_resultados, text="Flujo de Caja Acumulado")
        frame_grafico.pack(fill="both", expand=True, padx=10, pady=5)
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=frame_grafico)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def evaluar(self):
        try:
            # Obtener datos del formulario
            cliente = Cliente(
                razon_social=self.entry_razon.get(),
                ubicacion=self.entry_ubicacion.get(),
                modelo_operacion=self.combo_modelo.get(),
                demanda_electrica_kw=float(self.entry_demanda.get()),
                capacidad_transformador_kva=float(self.entry_transf.get()),
                tarifa_cfe=self.combo_tarifa.get(),
                porcentaje_demanda_cubrir=self.combo_porcentaje.get(),
                demanda_termica=self.var_termica.get(),
                suministro_combustible=self.combo_combustible.get(),
                area_techo_m2=float(self.entry_techo.get()),
                area_suelo_m2=float(self.entry_suelo.get()),
                recurso_solar_hse=self.combo_solar.get(),
                acceso_ducto_gas=self.var_gas.get(),
                enfoque_ambiental=self.combo_ambiental.get()
            )

            recibo = ReciboCFE(
                kwh_base=float(self.entry_kwh_base.get()),
                kwh_intermedio=float(self.entry_kwh_int.get()),
                kwh_punta=float(self.entry_kwh_punta.get()),
                kw_base=float(self.entry_kw_base.get()),
                kw_intermedio=float(self.entry_kw_int.get()),
                kw_punta=float(self.entry_kw_punta.get()),
                factor_potencia=float(self.entry_fp.get()),
                dias_periodo=int(self.entry_dias.get())
            )

            # Evaluar
            self.resultado = evaluar_proyecto(cliente, recibo, self.config)

            # Mostrar resultados en el área de texto
            self.mostrar_resultados_texto()
            # Graficar flujo de caja acumulado
            self.graficar_flujo()

            # Cambiar a pestaña de resultados
            self.notebook.select(self.frame_resultados)

        except Exception as e:
            messagebox.showerror("Error", f"Error en la evaluación: {str(e)}")

    def mostrar_resultados_texto(self):
        self.text_resultados.delete(1.0, tk.END)
        r = self.resultado
        texto = f"""
==================== REPORTE DE EVALUACIÓN ENERGÉTICA ====================

Cliente: {r['cliente']['razon_social']}
Ubicación: {r['cliente']['ubicacion']}

>>> RECOMENDACIÓN: {r['viabilidad']['recomendacion']}
Escenario: {r['viabilidad']['escenario']}
Justificación: {r['viabilidad']['justificacion']}

--- Resultados Técnicos ---
Potencia Fotovoltaica instalada: {r['tecnologias']['potencia_fv_kwp']:.1f} kWp
Generación FV anual: {r['tecnologias']['generacion_fv_anual_kwh']:,.0f} kWh
Potencia Cogeneración instalada: {r['tecnologias']['potencia_cogen_kw']:.0f} kW
Generación Cogeneración anual: {r['tecnologias']['generacion_cogen_anual_kwh']:,.0f} kWh
Energía gestionada por BESS anual: {r['tecnologias']['generacion_bess_anual_kwh']:,.0f} kWh

--- Resultados Financieros ---
Inversión Total: ${r['financiero']['inversion_total_mxn']:,.2f} MXN
OPEX anual: ${r['financiero']['opex_anual_mxn']:,.2f} MXN
Ahorro anual en CFE: ${r['financiero']['ahorro_anual_mxn']:,.2f} MXN
VAN (10%): ${r['financiero']['VAN_mxn']:,.2f} MXN
TIR: {r['financiero']['TIR']*100:.1f}%
Payback: {r['financiero']['payback_anios']:.2f} años

--- Impacto Ambiental ---
Reducción neta de CO2: {r['ambiental']['reduccion_neta_tco2e']:.2f} tCO2e/año
Reducción porcentual: {r['ambiental']['reduccion_porcentual']:.1f}%

===========================================================================
"""
        self.text_resultados.insert(tk.END, texto)

    def graficar_flujo(self):
        self.ax.clear()
        flujo = self.resultado['financiero']['flujo_caja_anual_mxn']
        años = list(range(len(flujo)))
        acumulado = np.cumsum(flujo)
        self.ax.plot(años, acumulado, marker='o', linestyle='-', color='green')
        self.ax.axhline(y=0, color='red', linestyle='--')
        self.ax.set_title("Flujo de Caja Acumulado (MXN)")
        self.ax.set_xlabel("Año")
        self.ax.set_ylabel("MXN")
        self.ax.grid(True)
        self.canvas.draw()

# ============================================================================
# EJECUCIÓN
# ============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = EvaluadorEnergiaApp(root)
    root.mainloop()