"""
Modelos matemáticos y físicos para la planificación de red
Incluye: Modelo de Thorp, Shannon, batimetría, etc.
"""

import numpy as np
from typing import Tuple, Dict, List
import config

# ============================================================================
# MODELO DE THORP PARA ABSORCIÓN ACÚSTICA
# ============================================================================

def thorp_absorption_coefficient(frequency_khz: float) -> float:
    """
    Calcula el coeficiente de absorción según el modelo de Thorp (1967)

    Args:
        frequency_khz: Frecuencia en kHz

    Returns:
        Coeficiente de absorción en dB/km
    """
    f = frequency_khz

    alpha = (0.11 * f**2) / (1 + f**2) + \
            (44 * f**2) / (4100 + f**2) + \
            0.000275 * f**2 + \
            0.003

    return alpha


def path_loss_acoustic(distance_m: float, frequency_khz: float = 20.0) -> float:
    """
    Calcula la pérdida total del enlace acústico submarino

    Args:
        distance_m: Distancia en metros
        frequency_khz: Frecuencia en kHz

    Returns:
        Pérdida total en dB
    """
    distance_km = distance_m / 1000.0

    # Spreading loss (esférico)
    spreading_loss = 20 * np.log10(distance_m)

    # Absorption loss
    alpha = thorp_absorption_coefficient(frequency_khz)
    absorption_loss = alpha * distance_km

    total_loss = spreading_loss + absorption_loss

    return total_loss


def calculate_snr(distance_m: float, 
                  source_level_db: float = 170,
                  noise_level_db: float = 60,
                  frequency_khz: float = 20.0) -> float:
    """
    Calcula el SNR para una distancia dada

    Args:
        distance_m: Distancia en metros
        source_level_db: Nivel de fuente en dB re 1 μPa @ 1m
        noise_level_db: Nivel de ruido en dB re 1 μPa
        frequency_khz: Frecuencia en kHz

    Returns:
        SNR en dB
    """
    loss = path_loss_acoustic(distance_m, frequency_khz)
    received_level = source_level_db - loss
    snr = received_level - noise_level_db

    return snr


def max_communication_range(min_snr_db: float = 10,
                            source_level_db: float = 170,
                            noise_level_db: float = 60,
                            frequency_khz: float = 20.0) -> float:
    """
    Calcula el rango máximo de comunicación para un SNR mínimo

    Args:
        min_snr_db: SNR mínimo requerido en dB
        source_level_db: Nivel de fuente en dB re 1 μPa @ 1m
        noise_level_db: Nivel de ruido en dB re 1 μPa
        frequency_khz: Frecuencia en kHz

    Returns:
        Rango máximo en metros
    """
    # Búsqueda binaria para encontrar rango máximo
    low, high = 1.0, 10000.0
    tolerance = 0.1

    while high - low > tolerance:
        mid = (low + high) / 2
        snr = calculate_snr(mid, source_level_db, noise_level_db, frequency_khz)

        if snr >= min_snr_db:
            low = mid
        else:
            high = mid

    return low


# ============================================================================
# CAPACIDAD DEL CANAL (SHANNON)
# ============================================================================

def shannon_capacity(bandwidth_hz: float, snr_linear: float) -> float:
    """
    Calcula la capacidad del canal según la ecuación de Shannon

    Args:
        bandwidth_hz: Ancho de banda en Hz
        snr_linear: SNR en escala lineal (no dB)

    Returns:
        Capacidad en bps
    """
    capacity = bandwidth_hz * np.log2(1 + snr_linear)
    return capacity


def db_to_linear(db: float) -> float:
    """Convierte dB a escala lineal"""
    return 10 ** (db / 10)


def linear_to_db(linear: float) -> float:
    """Convierte escala lineal a dB"""
    return 10 * np.log10(linear)


# ============================================================================
# MODELO BATIMÉTRICO
# ============================================================================

def generate_bathymetry(grid_size: int = 20,
                       depth_min: float = 8.0,
                       depth_max: float = 25.0,
                       depth_mean: float = 20.15,
                       depth_std: float = 4.20) -> np.ndarray:
    """
    Genera un modelo batimétrico sintético realista

    Args:
        grid_size: Tamaño de la grilla (NxN)
        depth_min: Profundidad mínima en metros
        depth_max: Profundidad máxima en metros
        depth_mean: Profundidad promedio
        depth_std: Desviación estándar

    Returns:
        Matriz NxN con profundidades
    """
    np.random.seed(42)  # Reproducibilidad

    # Generar campo gaussiano
    depths = np.random.normal(depth_mean, depth_std, (grid_size, grid_size))

    # Clip a rango válido
    depths = np.clip(depths, depth_min, depth_max)

    # Suavizar con filtro gaussiano
    from scipy.ndimage import gaussian_filter
    depths = gaussian_filter(depths, sigma=1.5)

    # Añadir gradiente (más profundo hacia el centro)
    x, y = np.meshgrid(np.linspace(-1, 1, grid_size), np.linspace(-1, 1, grid_size))
    gradient = 3.0 * (x**2 + y**2)
    depths += gradient

    # Clip nuevamente
    depths = np.clip(depths, depth_min, depth_max)

    return depths


# ============================================================================
# GENERACIÓN DE POIs
# ============================================================================

def generate_pois(num_pois: int = 20,
                  area_radius_km: float = 1.0,
                  center_lat: float = -33.047237,
                  center_lon: float = -71.612686,
                  poi_types: Dict = None) -> List[Dict]:
    """
    Genera Puntos de Interés distribuidos en el área

    Args:
        num_pois: Número total de POIs
        area_radius_km: Radio del área en km
        center_lat: Latitud del centro
        center_lon: Longitud del centro
        poi_types: Diccionario con tipos de POIs y cantidades

    Returns:
        Lista de diccionarios con POIs
    """
    np.random.seed(42)

    if poi_types is None:
        poi_types = config.POI_CONFIG['types']

    pois = []
    poi_id = 1

    # Convertir km a grados aproximadamente
    lat_range = area_radius_km / config.LAT_KM_PER_DEGREE
    lon_range = area_radius_km / (config.LAT_KM_PER_DEGREE * np.cos(np.radians(abs(center_lat))))

    for poi_type, params in poi_types.items():
        count = params['count']
        priority = params['priority']
        radius = params['radius']

        for i in range(count):
            # Generar posición aleatoria dentro del círculo
            angle = np.random.uniform(0, 2 * np.pi)
            r = np.random.uniform(0, 0.8)  # Hasta 80% del radio para evitar bordes

            lat = center_lat + r * lat_range * np.sin(angle)
            lon = center_lon + r * lon_range * np.cos(angle)

            poi = {
                'id': poi_id,
                'type': poi_type,
                'lat': lat,
                'lon': lon,
                'priority': priority,
                'coverage_radius_m': radius,
                'name': f'{poi_type}_{i+1}'
            }

            pois.append(poi)
            poi_id += 1

    return pois


# ============================================================================
# CÁLCULO DE DISTANCIAS GEOGRÁFICAS
# ============================================================================

def haversine_distance(lat1: float, lon1: float, 
                      lat2: float, lon2: float) -> float:
    """
    Calcula la distancia entre dos puntos geográficos usando fórmula de Haversine

    Args:
        lat1, lon1: Coordenadas del punto 1 en grados
        lat2, lon2: Coordenadas del punto 2 en grados

    Returns:
        Distancia en metros
    """
    # Radio de la Tierra en metros
    R = 6371000

    # Convertir a radianes
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)

    # Fórmula de Haversine
    a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    distance = R * c

    return distance


# ============================================================================
# CÁLCULOS DE TRÁFICO
# ============================================================================

def calculate_traffic_per_node(num_sensors: int = 5,
                               bytes_per_sample: int = 8,
                               samples_per_minute: int = 1,
                               protocol_overhead: float = 1.3) -> Dict[str, float]:
    """
    Calcula el tráfico generado por un nodo sensor

    Args:
        num_sensors: Número de sensores por nodo
        bytes_per_sample: Bytes por muestra
        samples_per_minute: Muestras por minuto
        protocol_overhead: Factor de overhead del protocolo

    Returns:
        Diccionario con tráfico en diferentes unidades
    """
    bytes_per_minute = num_sensors * bytes_per_sample * samples_per_minute * protocol_overhead
    bytes_per_second = bytes_per_minute / 60
    bits_per_second = bytes_per_second * 8

    return {
        'bytes_per_minute': bytes_per_minute,
        'bytes_per_second': bytes_per_second,
        'bits_per_second': bits_per_second,
        'kbps': bits_per_second / 1000
    }


# ============================================================================
# COSTOS
# ============================================================================

def calculate_capex(num_sns: int, num_bgs: int, num_ecs: int = 1) -> Dict[str, float]:
    """
    Calcula el CAPEX (Capital Expenditure)

    Args:
        num_sns: Número de nodos sensores
        num_bgs: Número de boyas gateway
        num_ecs: Número de estaciones costeras

    Returns:
        Diccionario con desglose de costos
    """
    cost_sns = num_sns * config.EQUIPMENT_COSTS['sensor_node']
    cost_bgs = num_bgs * config.EQUIPMENT_COSTS['gateway_buoy']
    cost_ecs = num_ecs * config.EQUIPMENT_COSTS['coastal_station']

    total_capex = cost_sns + cost_bgs + cost_ecs

    return {
        'sensor_nodes': cost_sns,
        'gateway_buoys': cost_bgs,
        'coastal_stations': cost_ecs,
        'total_capex': total_capex
    }


def calculate_opex_annual(num_sns: int, num_bgs: int) -> Dict[str, float]:
    """
    Calcula el OPEX anual (Operational Expenditure)

    Args:
        num_sns: Número de nodos sensores
        num_bgs: Número de boyas gateway

    Returns:
        Diccionario con desglose de costos anuales
    """
    opex_sns = num_sns * config.EQUIPMENT_COSTS['sensor_node'] * config.OPEX_RATES['sensor_node']
    opex_bgs = num_bgs * config.EQUIPMENT_COSTS['gateway_buoy'] * config.OPEX_RATES['gateway_buoy']
    opex_ec = config.OPEX_RATES['coastal_station_annual']

    total_opex = opex_sns + opex_bgs + opex_ec

    return {
        'sensor_nodes': opex_sns,
        'gateway_buoys': opex_bgs,
        'coastal_station': opex_ec,
        'total_opex_annual': total_opex
    }


def calculate_tco(num_sns: int, num_bgs: int, years: int = 5) -> Dict[str, float]:
    """
    Calcula el TCO (Total Cost of Ownership)

    Args:
        num_sns: Número de nodos sensores
        num_bgs: Número de boyas gateway
        years: Número de años

    Returns:
        Diccionario con TCO y componentes
    """
    capex = calculate_capex(num_sns, num_bgs)
    opex_annual = calculate_opex_annual(num_sns, num_bgs)

    tco = capex['total_capex'] + opex_annual['total_opex_annual'] * years

    return {
        'capex': capex['total_capex'],
        'opex_total': opex_annual['total_opex_annual'] * years,
        'tco': tco,
        'years': years
    }
