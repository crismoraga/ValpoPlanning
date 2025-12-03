"""
Configuración global del proyecto de planificación de red de sensores submarinos
Puerto de Valparaíso - Equipo PlaniGüinos
"""

# ============================================================================
# COORDENADAS GEOGRÁFICAS DEL PUERTO DE VALPARAÍSO
# ============================================================================
VALPARAISO_CENTER = {
    'lat': -33.047237,  # Coordenada exacta verificada
    'lon': -71.612686,  # Coordenada exacta verificada
    'lat_dms': "33°02'50\" S",
    'lon_dms': "71°36'45\" W"
}

# Área de estudio
STUDY_AREA = {
    'radius_km': 1.0,  # Radio de 1 km
    'resolution_m': 100,  # Resolución de grilla en metros
    'grid_size': 20  # Grilla 20x20
}

# ============================================================================
# PARÁMETROS BATIMÉTRICOS
# ============================================================================
BATHYMETRY = {
    'depth_min': 8.0,  # Profundidad mínima en metros
    'depth_max': 25.0,  # Profundidad máxima en metros
    'depth_mean': 20.15,  # Profundidad promedio
    'depth_std': 4.20  # Desviación estándar
}

# ============================================================================
# PUNTOS DE INTERÉS (POIs)
# ============================================================================
POI_CONFIG = {
    'total_pois': 20,
    'types': {
        'industrial_discharge': {'count': 6, 'priority': 'high', 'radius': 150},
        'anchorage': {'count': 4, 'priority': 'medium', 'radius': 120},
        'sensitive_areas': {'count': 5, 'priority': 'very_high', 'radius': 100},
        'bay_entrances': {'count': 3, 'priority': 'high', 'radius': 180},
        'critical_monitoring': {'count': 2, 'priority': 'very_high', 'radius': 200}
    }
}

# ============================================================================
# ZONAS DE EXCLUSIÓN
# ============================================================================
EXCLUSION_ZONES = [
    {'name': 'Canal Principal', 'area_km2': 0.800},
    {'name': 'Zona de Fondeo', 'area_km2': 0.240},
    {'name': 'Operaciones Portuarias', 'area_km2': 0.240}
]

# ============================================================================
# PARÁMETROS OCEANOGRÁFICOS (Primavera Austral 2025)
# ============================================================================
OCEANOGRAPHIC_PARAMS = {
    'surface_temp': 15.8,  # °C
    'bottom_temp': 13.2,  # °C
    'salinity': 34.8,  # ppt
    'ph': 8.05,
    'current_speed': 0.35,  # m/s
    'wave_height': 1.8  # m
}

# ============================================================================
# ESPECIFICACIONES DE SENSORES
# ============================================================================
SENSORS = {
    'ph': {'range': '0-14', 'precision': 0.01, 'rate': 1},
    'temperature': {'range': '-5 to 40', 'precision': 0.01, 'rate': 1},
    'turbidity': {'range': '0-1000', 'precision': 2, 'rate': 1},
    'conductivity': {'range': '0-100', 'precision': 0.1, 'rate': 1},
    'dissolved_oxygen': {'range': '0-500', 'precision': 1, 'rate': 1}
}

NUM_SENSORS = len(SENSORS)
BYTES_PER_SAMPLE = 8  # float64
PROTOCOL_OVERHEAD = 1.3  # 30% overhead
SAMPLES_PER_MINUTE = 1

# ============================================================================
# MODELO DE THORP - PROPAGACIÓN ACÚSTICA
# ============================================================================
ACOUSTIC_MODEL = {
    'frequency_khz': 20.0,  # Frecuencia central
    'bandwidth_khz': 10.0,  # Ancho de banda
    'source_level_db': 170,  # dB re 1 μPa @ 1m
    'noise_level_db': 60,  # dB re 1 μPa
    'min_snr_db': 10,  # SNR mínimo para conectividad
    'modulation': 'FSK'
}

# ============================================================================
# PARÁMETROS LoRaWAN
# ============================================================================
LORAWAN_CONFIG = {
    'frequency_mhz': 915,
    'spreading_factor': 7,
    'capacity_kbps': 50,
    'range_km': 10,
    'latency_ms': 500
}

# ============================================================================
# COSTOS DE EQUIPAMIENTO (USD)
# ============================================================================
EQUIPMENT_COSTS = {
    'sensor_node': 8500,  # Nodo Sensor (SN)
    'gateway_buoy': 42500,  # Boya Gateway (BG)
    'coastal_station': 125000  # Estación Costera (EC)
}

# Costos operacionales (porcentaje anual del CAPEX)
OPEX_RATES = {
    'sensor_node': 0.15,  # 15% anual
    'gateway_buoy': 0.20,  # 20% anual
    'coastal_station_annual': 42000  # Costo fijo anual
}

# ============================================================================
# PARÁMETROS NSGA-II
# ============================================================================
NSGA2_PARAMS = {
    'population_size': 160,
    'generations': 320,
    'mutation_rate': 0.22,
    'crossover_rate': 0.88,
    'max_sensor_nodes': 25,
    'max_gateway_buoys': 6,
    'tournament_size': 3
}

# Costos relativos para función objetivo
RELATIVE_COSTS = {
    'sensor_node': 1,  # 1 unidad
    'gateway_buoy': 5  # 5 unidades
}

# ============================================================================
# CONFIGURACIÓN DE SALIDAS
# ============================================================================
OUTPUT_CONFIG = {
    'figures_dir': 'figures',
    'data_dir': 'data',
    'results_dir': 'results',
    'dpi': 300,
    'figure_format': 'png'
}

# ============================================================================
# CONSTANTES FÍSICAS
# ============================================================================
SOUND_SPEED_WATER = 1500  # m/s
LAT_KM_PER_DEGREE = 111.0  # km por grado de latitud
