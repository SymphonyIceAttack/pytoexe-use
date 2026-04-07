"""
Software de Evaluación de Soluciones Energéticas
Basado en el modelo técnico-económico del archivo Excel proporcionado.
Autor: Asistente de IA
Versión: 1.0
"""

import math
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# ============================================================================
# CONSTANTES Y PARÁMETROS GLOBALES
# ============================================================================

TIPO_CAMBIO_MXN_USD = 18.57  # Ejemplo, se puede actualizar
IVA = 0.16
INFLACION_ANUAL = 0.05
INCREMENTO_TARIFA_CFE = 0.04
TASA_DESCUENTO = 0.10  # Para VAN

# Factores de emisión (tCO2e/kWh)
FEC = 0.000435  # Factor de emisión de la red CFE
FECOGEN = 0.0002  # Factor de emisión cogeneración con gas natural

# Horas de operación anual estimadas
HORAS_SOLARES_POR_DIA = 5.5  # Promedio >5 HSE
HORAS_OPERACION_COGEN = 24 * 365 * 0.95  # 95% disponibilidad

# ============================================================================
# ESTRUCTURAS DE DATOS
# ============================================================================

@dataclass
class Cliente:
    """Datos del cliente y su instalación."""
    razon_social: str
    ubicacion: str
    # Modelo de operación: "24/7", "24/6", "24/7 CON STAND-BY PARA EVITAR PUNTA", etc.
    modelo_operacion: str
    demanda_electrica_kw: float  # Demanda contratada o máxima
    capacidad_transformador_kva: float
    tarifa_cfe: str  # "GDMTH", "GDMTO", etc.
    # Horarios de operación (horas por período, por tipo de día)
    horas_base_verano: int = 4
    horas_intermedio_verano: int = 16
    horas_punta_verano: int = 2
    horas_base_invierno: int = 4
    horas_intermedio_invierno: int = 14
    horas_punta_invierno: int = 4
    porcentaje_demanda_cubrir: str = "PARCIAL"  # "PARCIAL", "TOTAL"
    demanda_termica: bool = False  # Si requiere calor para procesos
    suministro_combustible: str = "N/A"  # "GND", "GNC", "GND y GNC", "N/A"
    temperatura_requerida_c: Optional[float] = None
    giro_sector: str = ""
    area_suelo_m2: float = 0.0
    area_techo_m2: float = 0.0
    plan_expansion: str = "NULO"
    recurso_solar_hse: str = ">5 HSE"  # ">5 HSE", "<5 HSE", "N/A"
    recurso_eolico: bool = False
    acceso_ducto_gas: bool = False
    suministro_energia_actual: str = "CFE"
    enfoque_ambiental: str = "MEDIO"  # "NULO", "BAJO", "MEDIO", "ALTO"
    tipo_inversion: str = "Venta del proyecto al cliente"  # o "Venta de energía - GNU"
    modo_operacion_red: str = "Interconectado a la red eléctrica de CFE"

@dataclass
class ReciboCFE:
    """Datos extraídos del recibo de luz."""
    periodo: str
    kwh_base: float
    kwh_intermedio: float
    kwh_punta: float
    kw_base: float
    kw_intermedio: float
    kw_punta: float
    factor_carga: float
    dias_periodo: int
    kvArh: float
    factor_potencia: float  # %
    tarifa: str
    multiplicador: int = 80
    # Precios unitarios (estimados del recibo)
    precio_base: float = 0.9624
    precio_intermedio: float = 1.8859
    precio_punta: float = 2.1515
    cargo_fijo: float = 245.25

@dataclass
class ConfiguracionTecnologia:
    """Parámetros de costos y rendimiento de las tecnologías."""
    # Fotovoltaica
    costo_panel_mxn: float = 2472.4
    costo_inversor_mxn: float = 116600
    costo_mantenimiento_anual_por_kwp_usd: float = 10.0
    eficiencia_sistema: float = 0.85
    degradacion_anual_pv: float = 0.005
    # Cogeneración
    costo_turbina_por_kw_usd: float = 3000.0  # Estimado
    costo_mantenimiento_anual_por_kw_usd: float = 50.0
    eficiencia_electrica_turbina: float = 0.77
    precio_gas_natural_usd_por_mmbtu: float = 3.5  # Ajustable
    # Baterías
    costo_bateria_por_kwh_usd: float = 250.0
    costo_bateria_por_kw_usd: float = 300.0
    eficiencia_bateria: float = 0.9
    ciclos_vida: int = 10000
    degradacion_anual_bess: float = 0.02
    # Generales
    tipo_cambio: float = TIPO_CAMBIO_MXN_USD

# ============================================================================
# FUNCIONES DE CÁLCULO TÉCNICO
# ============================================================================

def calcular_generacion_fotovoltaica(area_m2: float, irradiancia_hse: float = 5.5,
                                     eficiencia_panel: float = 0.213,
                                     densidad_potencia_kwp_por_m2: float = 0.2) -> Dict:
    """
    Calcula la capacidad instalable y generación anual de FV.
    area_m2: superficie disponible (techo o suelo)
    irradiancia_hse: horas solar equivalente promedio diario
    Retorna: potencia_kwp, generacion_anual_kwh
    """
    # Suponiendo paneles de 620 Wp con área aprox 2.7 m2
    potencia_por_panel_kwp = 0.620
    area_por_panel_m2 = 2.382 * 1.134  # ~2.70 m2
    num_paneles = int(area_m2 / area_por_panel_m2)
    potencia_instalada_kwp = num_paneles * potencia_por_panel_kwp
    # Generación anual = potencia * HSE * 365 * PR (performance ratio)
    generacion_anual_kwh = potencia_instalada_kwp * irradiancia_hse * 365 * 0.85
    return {
        "potencia_kwp": potencia_instalada_kwp,
        "num_paneles": num_paneles,
        "generacion_anual_kwh": generacion_anual_kwh,
        "area_utilizada_m2": num_paneles * area_por_panel_m2
    }

def calcular_cogeneracion(demanda_electrica_kw: float, demanda_termica: bool,
                          horas_operacion_dia: int = 24, dias_anio: int = 365,
                          eficiencia: float = 0.77) -> Dict:
    """
    Dimensiona turbina de cogeneración para cubrir demanda eléctrica base.
    Retorna: potencia_turbina_kw, generacion_anual_kwh, consumo_gas_mmbtu_anual
    """
    # Se dimensiona para cubrir la demanda eléctrica máxima o un porcentaje
    potencia_turbina_kw = demanda_electrica_kw
    horas_operacion_anual = horas_operacion_dia * dias_anio * 0.95  # disponibilidad
    generacion_anual_kwh = potencia_turbina_kw * horas_operacion_anual
    # Consumo de gas: 1 kWh eléctrico ~ 3412 BTU / eficiencia
    consumo_energia_primaria_kwh = generacion_anual_kwh / eficiencia
    consumo_mmbtu_anual = consumo_energia_primaria_kwh * 3412 / 1e6
    return {
        "potencia_turbina_kw": potencia_turbina_kw,
        "generacion_anual_kwh": generacion_anual_kwh,
        "consumo_mmbtu_anual": consumo_mmbtu_anual,
        "horas_operacion_anual": horas_operacion_anual
    }

def calcular_baterias(energia_requerida_kwh: float, potencia_requerida_kw: float) -> Dict:
    """
    Dimensiona sistema de baterías para peak shaving o arbitraje.
    """
    capacidad_kwh = energia_requerida_kwh
    potencia_kw = potencia_requerida_kw
    return {
        "capacidad_kwh": capacidad_kwh,
        "potencia_kw": potencia_kw,
        "energia_util_anual_kwh": capacidad_kwh * 365 * 0.9  # 1 ciclo por día
    }

# ============================================================================
# CÁLCULOS ECONÓMICOS
# ============================================================================

def calcular_inversion_pv(potencia_kwp: float, config: ConfiguracionTecnologia) -> float:
    """Costo total de inversión fotovoltaica en MXN."""
    num_paneles = math.ceil(potencia_kwp / 0.620)
    costo_paneles = num_paneles * config.costo_panel_mxn
    # Se asume 1 inversor por cada 100 kWp
    num_inversores = max(1, math.ceil(potencia_kwp / 100))
    costo_inversores = num_inversores * config.costo_inversor_mxn
    estructura = 40000  # Estimado
    componentes = 50000  # Estimado
    total = costo_paneles + costo_inversores + estructura + componentes
    return total * (1 + IVA)

def calcular_opex_pv(potencia_kwp: float, config: ConfiguracionTecnologia) -> float:
    """Costo anual de O&M fotovoltaico en MXN."""
    return potencia_kwp * config.costo_mantenimiento_anual_por_kwp_usd * config.tipo_cambio

def calcular_inversion_cogen(potencia_kw: float, config: ConfiguracionTecnologia) -> float:
    """Costo de inversión cogeneración en MXN."""
    costo_usd = potencia_kw * config.costo_turbina_por_kw_usd
    return costo_usd * config.tipo_cambio * (1 + IVA)

def calcular_opex_cogen(potencia_kw: float, config: ConfiguracionTecnologia,
                        consumo_mmbtu_anual: float) -> float:
    """Costo anual de O&M + combustible para cogeneración en MXN."""
    oym_usd = potencia_kw * config.costo_mantenimiento_anual_por_kw_usd
    combustible_usd = consumo_mmbtu_anual * config.precio_gas_natural_usd_por_mmbtu
    total_usd = oym_usd + combustible_usd
    return total_usd * config.tipo_cambio

def calcular_inversion_bess(capacidad_kwh: float, potencia_kw: float, config: ConfiguracionTecnologia) -> float:
    """Inversión en BESS en MXN."""
    costo_usd = capacidad_kwh * config.costo_bateria_por_kwh_usd + potencia_kw * config.costo_bateria_por_kw_usd
    return costo_usd * config.tipo_cambio * (1 + IVA)

def calcular_ahorro_cfe(recibo: ReciboCFE, generacion_kwh: float,
                        generacion_kw_demanda: float = 0) -> float:
    """
    Calcula el ahorro mensual por generación propia.
    Considera reducción de consumo de energía y posible reducción de demanda.
    """
    # Simplificación: ahorro = generación_kwh * precio_promedio
    # Se puede refinar con distribución por horarios
    precio_promedio = (recibo.precio_base + recibo.precio_intermedio + recibo.precio_punta) / 3
    ahorro_energia = generacion_kwh * precio_promedio
    # Reducción de demanda (solo si se cubre punta)
    ahorro_demanda = generacion_kw_demanda * recibo.precio_punta * 30  # Aprox mensual
    return ahorro_energia + ahorro_demanda

def flujo_caja_anual(inversion_inicial: float, opex_anual: float, ahorro_anual: float,
                     años: int = 10, inflacion: float = INFLACION_ANUAL,
                     incremento_tarifa: float = INCREMENTO_TARIFA_CFE) -> List[float]:
    """
    Genera flujo de caja neto por año (incluyendo año 0 como inversión negativa).
    """
    flujo = [-inversion_inicial]
    for año in range(1, años+1):
        opex_actual = opex_anual * (1 + inflacion) ** (año-1)
        ahorro_actual = ahorro_anual * (1 + incremento_tarifa) ** (año-1)
        flujo.append(ahorro_actual - opex_actual)
    return flujo

def calcular_vna(flujo: List[float], tasa: float = TASA_DESCUENTO) -> float:
    """Valor neto actualizado."""
    vna = 0
    for i, cf in enumerate(flujo):
        vna += cf / (1 + tasa) ** i
    return vna

def calcular_tir(flujo: List[float]) -> float:
    """Tasa interna de retorno (aproximación por búsqueda)."""
    def vna_tasa(tasa):
        return sum(cf / (1 + tasa)**i for i, cf in enumerate(flujo))
    # Búsqueda simple
    if vna_tasa(0) <= 0:
        return 0
    tir = 0.01
    while vna_tasa(tir) > 0 and tir < 1:
        tir += 0.01
    return tir

def calcular_payback(flujo: List[float]) -> float:
    """Período de recuperación en años."""
    acumulado = 0
    for i, cf in enumerate(flujo):
        acumulado += cf
        if acumulado >= 0:
            # Interpolación simple
            if i == 0:
                return 0
            prev_acum = acumulado - cf
            fraccion = -prev_acum / cf if cf != 0 else 0
            return i - 1 + fraccion
    return float('inf')

# ============================================================================
# LÓGICA DE VIABILIDAD (RCT - Recomendación de Tecnología)
# ============================================================================

def evaluar_viabilidad(cliente: Cliente, recibo: ReciboCFE) -> Dict:
    """
    Evalúa según reglas similares a las hojas RCT y RCT 2.
    Retorna: escenario recomendado y justificación.
    """
    # Escenario 1: Cogeneración pura (24/7, demanda térmica SI, acceso a gas)
    if (cliente.modelo_operacion in ["24/7", "24/6"] and
        cliente.tarifa_cfe == "GDMTH" and
        cliente.demanda_termica and
        cliente.suministro_combustible in ["GND", "GNC", "GND y GNC"] and
        cliente.porcentaje_demanda_cubrir == "TOTAL" and
        cliente.recurso_solar_hse != ">5 HSE"):  # Sin suficiente sol
        return {
            "recomendacion": "Cogeneración",
            "escenario": "Cogeneración a gas natural para autoconsumo total",
            "justificacion": "El sitio opera 24/7, tiene demanda térmica y acceso a gas natural. La cogeneración es la solución más eficiente."
        }
    # Escenario 2: Cogeneración + FV
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
            "justificacion": "La cogeneración cubre la base, la FV reduce consumo en horario intermedio, aprovechando buena irradiación."
        }
    # Escenario 3: Fotovoltaica + Baterías
    elif (cliente.modelo_operacion in ["24/7", "24/6"] and
          cliente.tarifa_cfe == "GDMTH" and
          not cliente.demanda_termica and
          cliente.recurso_solar_hse == ">5 HSE" and
          cliente.area_techo_m2 + cliente.area_suelo_m2 >= 100):
        return {
            "recomendacion": "Fotovoltaica + Almacenamiento (BESS)",
            "escenario": "FV para autoconsumo y BESS para gestión de punta",
            "justificacion": "Alta irradiación y operación continua. Las baterías permiten desplazar consumo a horario punta."
        }
    # Escenario 4: Solo Baterías (arbitraje)
    elif (cliente.modelo_operacion in ["24/7", "24/6"] and
          cliente.tarifa_cfe == "GDMTH" and
          cliente.recurso_solar_hse != ">5 HSE" and
          not cliente.demanda_termica and
          cliente.porcentaje_demanda_cubrir in ["PARCIAL", "TOTAL"]):
        return {
            "recomendacion": "Sistema de Almacenamiento con Baterías",
            "escenario": "BESS para carga en horario base y descarga en punta",
            "justificacion": "Aprovecha diferencia tarifaria sin necesidad de generación propia."
        }
    # Escenario 5: Solo Fotovoltaica (si área suficiente y >5 HSE)
    elif (cliente.recurso_solar_hse == ">5 HSE" and
          cliente.area_techo_m2 + cliente.area_suelo_m2 >= 50 and
          not cliente.demanda_termica):
        return {
            "recomendacion": "Fotovoltaica",
            "escenario": "Generación solar para autoconsumo en horario intermedio",
            "justificacion": "Recurso solar adecuado y área disponible. Reduce consumo de CFE sin necesidad de baterías."
        }
    else:
        return {
            "recomendacion": "No viable",
            "escenario": "Ninguna tecnología es claramente beneficiosa",
            "justificacion": "Las condiciones del sitio no favorecen ninguna solución técnico-económica. Se sugiere mejorar eficiencia energética o reevaluar."
        }

# ============================================================================
# CÁLCULO DE EMISIONES CO2
# ============================================================================

def calcular_emisiones(recibo: ReciboCFE, generacion_pv_kwh: float, generacion_cogen_kwh: float) -> Dict:
    """
    Calcula emisiones evitadas netas.
    """
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

# ============================================================================
# FUNCIÓN PRINCIPAL DE EVALUACIÓN
# ============================================================================

def evaluar_proyecto(cliente: Cliente, recibo: ReciboCFE, config: ConfiguracionTecnologia) -> Dict:
    """
    Ejecuta toda la evaluación y retorna resultados detallados.
    """
    # 1. Determinar escenario viable
    viabilidad = evaluar_viabilidad(cliente, recibo)

    # 2. Calcular generación según recomendación
    generacion_pv_kwh = 0
    generacion_cogen_kwh = 0
    generacion_bess_kwh = 0
    inversion_total = 0
    opex_anual = 0
    ahorro_anual = 0

    recomendacion = viabilidad["recomendacion"]

    if "Fotovoltaica" in recomendacion or "FV" in recomendacion:
        area_total = cliente.area_techo_m2 + cliente.area_suelo_m2
        pv = calcular_generacion_fotovoltaica(area_total, irradiancia_hse=5.5)
        generacion_pv_kwh = pv["generacion_anual_kwh"]
        inversion_pv = calcular_inversion_pv(pv["potencia_kwp"], config)
        opex_pv = calcular_opex_pv(pv["potencia_kwp"], config)
        inversion_total += inversion_pv
        opex_anual += opex_pv
        ahorro_anual += calcular_ahorro_cfe(recibo, generacion_pv_kwh / 12) * 12  # anual

    if "Cogeneración" in recomendacion:
        cogen = calcular_cogeneracion(cliente.demanda_electrica_kw, cliente.demanda_termica)
        generacion_cogen_kwh = cogen["generacion_anual_kwh"]
        inversion_cogen = calcular_inversion_cogen(cogen["potencia_turbina_kw"], config)
        opex_cogen = calcular_opex_cogen(cogen["potencia_turbina_kw"], config, cogen["consumo_mmbtu_anual"])
        inversion_total += inversion_cogen
        opex_anual += opex_cogen
        ahorro_anual += calcular_ahorro_cfe(recibo, generacion_cogen_kwh / 12) * 12

    if "Almacenamiento" in recomendacion or "BESS" in recomendacion:
        # Dimensionamiento simple: 2 horas de demanda pico
        potencia_bess = recibo.kw_punta
        energia_bess = potencia_bess * 2  # 2 horas
        bess = calcular_baterias(energia_bess, potencia_bess)
        generacion_bess_kwh = bess["energia_util_anual_kwh"]
        inversion_bess = calcular_inversion_bess(bess["capacidad_kwh"], bess["potencia_kw"], config)
        opex_bess = inversion_bess * 0.02  # 2% de OPEX anual estimado
        inversion_total += inversion_bess
        opex_anual += opex_bess
        # El ahorro de BESS se calcula como el costo evitado de energía en punta
        ahorro_bess = generacion_bess_kwh * recibo.precio_punta
        ahorro_anual += ahorro_bess

    # 3. Flujo de caja y métricas financieras
    flujo = flujo_caja_anual(inversion_total, opex_anual, ahorro_anual, años=10)
    vna = calcular_vna(flujo)
    tir = calcular_tir(flujo)
    payback = calcular_payback(flujo)

    # 4. Emisiones
    emisiones = calcular_emisiones(recibo, generacion_pv_kwh, generacion_cogen_kwh)

    # 5. Resultado consolidado
    resultado = {
        "cliente": asdict(cliente),
        "recibo": asdict(recibo),
        "viabilidad": viabilidad,
        "tecnologias": {
            "potencia_fv_kwp": generacion_pv_kwh / (HORAS_SOLARES_POR_DIA * 365) if generacion_pv_kwh > 0 else 0,
            "generacion_fv_anual_kwh": generacion_pv_kwh,
            "potencia_cogen_kw": generacion_cogen_kwh / (HORAS_OPERACION_COGEN) if generacion_cogen_kwh > 0 else 0,
            "generacion_cogen_anual_kwh": generacion_cogen_kwh,
            "capacidad_bess_kwh": 0,  # Se puede agregar
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
# EJEMPLO DE USO
# ============================================================================

def ejemplo_uso():
    # Crear datos de cliente (similar al levantamiento del archivo Hoja2)
    cliente = Cliente(
        razon_social="ARTIFIBRAS S.A. DE C.V.",
        ubicacion="BLVD. INDUSTRIAL #445, URUAPAN MICHOACÁN",
        modelo_operacion="24/7",
        demanda_electrica_kw=500,  # 0.5 MW
        capacidad_transformador_kva=1500,
        tarifa_cfe="GDMTH",
        porcentaje_demanda_cubrir="PARCIAL",
        demanda_termica=True,
        suministro_combustible="GND",
        giro_sector="Industria de plástico y automotriz",
        area_suelo_m2=30,
        area_techo_m2=72,
        recurso_solar_hse=">5 HSE",
        acceso_ducto_gas=True,
        enfoque_ambiental="MEDIO",
        tipo_inversion="Venta del proyecto al cliente"
    )

    # Datos de recibo (ejemplo del archivo)
    recibo = ReciboCFE(
        periodo="ENE 25",
        kwh_base=66765,
        kwh_intermedio=113555,
        kwh_punta=29349,
        kw_base=587,
        kw_intermedio=583,
        kw_punta=509,
        factor_carga=0.57,
        dias_periodo=31,
        kvArh=75037,
        factor_potencia=94.15,
        tarifa="GDMTH"
    )

    config = ConfiguracionTecnologia()

    # Evaluar
    resultado = evaluar_proyecto(cliente, recibo, config)

    # Imprimir reporte
    print("=" * 80)
    print("REPORTE DE EVALUACIÓN DE PROYECTO ENERGÉTICO")
    print("=" * 80)
    print(f"Cliente: {cliente.razon_social}")
    print(f"Ubicación: {cliente.ubicacion}")
    print(f"Recomendación: {resultado['viabilidad']['recomendacion']}")
    print(f"Escenario: {resultado['viabilidad']['escenario']}")
    print(f"Justificación: {resultado['viabilidad']['justificacion']}")
    print("\n--- Resultados Técnicos ---")
    print(f"Generación FV anual: {resultado['tecnologias']['generacion_fv_anual_kwh']:.0f} kWh")
    print(f"Generación Cogeneración anual: {resultado['tecnologias']['generacion_cogen_anual_kwh']:.0f} kWh")
    print("\n--- Resultados Financieros ---")
    print(f"Inversión total: ${resultado['financiero']['inversion_total_mxn']:,.2f} MXN")
    print(f"OPEX anual: ${resultado['financiero']['opex_anual_mxn']:,.2f} MXN")
    print(f"Ahorro anual: ${resultado['financiero']['ahorro_anual_mxn']:,.2f} MXN")
    print(f"VAN (10%): ${resultado['financiero']['VAN_mxn']:,.2f} MXN")
    print(f"TIR: {resultado['financiero']['TIR']*100:.1f}%")
    print(f"Payback: {resultado['financiero']['payback_anios']:.2f} años")
    print("\n--- Impacto Ambiental ---")
    print(f"Reducción neta de CO2: {resultado['ambiental']['reduccion_neta_tco2e']:.2f} tCO2e/año")
    print(f"Reducción porcentual: {resultado['ambiental']['reduccion_porcentual']:.1f}%")
    print("=" * 80)

    # Opcional: guardar en JSON
    with open("resultado_proyecto.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=4, default=str)
    print("\nResultado guardado en 'resultado_proyecto.json'")

if __name__ == "__main__":
    ejemplo_uso()