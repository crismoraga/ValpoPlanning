"""
Implementación del algoritmo NSGA-II para optimización multi-objetivo
de la topología de red de sensores submarinos
"""

import numpy as np
import random
from typing import List, Tuple, Dict
from deap import base, creator, tools, algorithms
import networkx as nx

import config
import models

# ============================================================================
# DEFINICIÓN DEL PROBLEMA DE OPTIMIZACIÓN
# ============================================================================

# Crear tipos DEAP (solo si no existen)
if not hasattr(creator, "FitnessMulti"):
    creator.create("FitnessMulti", base.Fitness, weights=(-1.0, 1.0))  # Min costo, Max cobertura

if not hasattr(creator, "Individual"):
    creator.create("Individual", list, fitness=creator.FitnessMulti)


class NetworkOptimizer:
    """Clase para optimizar la topología de red usando NSGA-II"""

    def __init__(self, pois: List[Dict], bathymetry: np.ndarray,
                 center_lat: float, center_lon: float, area_radius_km: float = 1.0):
        """
        Inicializa el optimizador

        Args:
            pois: Lista de Puntos de Interés
            bathymetry: Matriz batimétrica
            center_lat: Latitud del centro
            center_lon: Longitud del centro
            area_radius_km: Radio del área en km
        """
        self.pois = pois
        self.bathymetry = bathymetry
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.area_radius_km = area_radius_km

        # Parámetros NSGA-II
        self.pop_size = config.NSGA2_PARAMS['population_size']
        self.n_gen = config.NSGA2_PARAMS['generations']
        self.mut_rate = config.NSGA2_PARAMS['mutation_rate']
        self.cx_rate = config.NSGA2_PARAMS['crossover_rate']
        self.max_sns = config.NSGA2_PARAMS['max_sensor_nodes']
        self.max_bgs = config.NSGA2_PARAMS['max_gateway_buoys']

        # Calcular rango máximo de comunicación
        self.max_range_m = models.max_communication_range(
            min_snr_db=config.ACOUSTIC_MODEL['min_snr_db'],
            source_level_db=config.ACOUSTIC_MODEL['source_level_db'],
            noise_level_db=config.ACOUSTIC_MODEL['noise_level_db'],
            frequency_khz=config.ACOUSTIC_MODEL['frequency_khz']
        )

        print(f"Rango máximo de comunicación: {self.max_range_m:.2f} m")

        # Setup DEAP
        self.toolbox = base.Toolbox()
        self._setup_deap()

    def _setup_deap(self):
        """Configura los operadores de DEAP"""

        # Función para crear un individuo
        self.toolbox.register("individual", self._create_individual)

        # Población
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)

        # Operadores genéticos
        self.toolbox.register("evaluate", self._evaluate)
        self.toolbox.register("mate", self._crossover)
        self.toolbox.register("mutate", self._mutate)
        self.toolbox.register("select", tools.selNSGA2)

    def _create_individual(self) -> creator.Individual:
        """
        Crea un individuo (solución) aleatoria

        Representación: Lista de nodos, cada nodo = [lat, lon, depth, active, type]
        - type: 0=SN, 1=BG
        """
        individual = []

        # Convertir km a grados
        lat_range = self.area_radius_km / config.LAT_KM_PER_DEGREE
        lon_range = self.area_radius_km / (config.LAT_KM_PER_DEGREE * 
                                           np.cos(np.radians(abs(self.center_lat))))

        # Generar nodos sensores
        for _ in range(self.max_sns):
            angle = random.uniform(0, 2 * np.pi)
            r = random.uniform(0.1, 0.9)  # Evitar centro y bordes

            lat = self.center_lat + r * lat_range * np.sin(angle)
            lon = self.center_lon + r * lon_range * np.cos(angle)
            depth = random.uniform(config.BATHYMETRY['depth_min'], 
                                  config.BATHYMETRY['depth_max'])
            active = random.choice([0, 1])  # Bit de activación
            node_type = 0  # SN

            individual.append([lat, lon, depth, active, node_type])

        # Generar boyas gateway
        for _ in range(self.max_bgs):
            angle = random.uniform(0, 2 * np.pi)
            r = random.uniform(0.3, 0.8)

            lat = self.center_lat + r * lat_range * np.sin(angle)
            lon = self.center_lon + r * lon_range * np.cos(angle)
            depth = 0  # Superficie
            active = random.choice([0, 1])
            node_type = 1  # BG

            individual.append([lat, lon, depth, active, node_type])

        return creator.Individual(individual)

    def _evaluate(self, individual: creator.Individual) -> Tuple[float, float]:
        """
        Evalúa un individuo según los dos objetivos

        Args:
            individual: Solución a evaluar

        Returns:
            Tupla (costo, cobertura)
        """
        # Extraer nodos activos
        active_sns = [node for node in individual if node[4] == 0 and node[3] == 1]
        active_bgs = [node for node in individual if node[4] == 1 and node[3] == 1]

        num_sns = len(active_sns)
        num_bgs = len(active_bgs)

        # Si no hay nodos activos, penalizar
        if num_sns == 0 or num_bgs == 0:
            return (1e6, 0.0)

        # Objetivo 1: Minimizar costo (unidades relativas)
        cost = num_sns * config.RELATIVE_COSTS['sensor_node'] + \
               num_bgs * config.RELATIVE_COSTS['gateway_buoy']

        # Objetivo 2: Maximizar cobertura de POIs
        covered_pois = set()

        for poi in self.pois:
            for node in active_sns:
                distance = models.haversine_distance(
                    poi['lat'], poi['lon'],
                    node[0], node[1]
                )

                if distance <= poi['coverage_radius_m']:
                    covered_pois.add(poi['id'])
                    break

        coverage_pct = (len(covered_pois) / len(self.pois)) * 100

        # Verificar conectividad
        if not self._check_connectivity(active_sns, active_bgs):
            # Penalizar soluciones no conectadas
            return (cost * 10, coverage_pct * 0.1)

        return (cost, coverage_pct)

    def _check_connectivity(self, active_sns: List, active_bgs: List) -> bool:
        """
        Verifica que todos los nodos tengan camino a una BG usando BFS

        Args:
            active_sns: Lista de SNs activos
            active_bgs: Lista de BGs activos

        Returns:
            True si hay conectividad total, False en caso contrario
        """
        if not active_bgs:
            return False

        # Crear grafo
        G = nx.Graph()

        all_nodes = active_sns + active_bgs

        # Agregar nodos
        for i, node in enumerate(all_nodes):
            G.add_node(i, pos=(node[0], node[1]), type=node[4])

        # Agregar aristas basadas en rango de comunicación
        for i in range(len(all_nodes)):
            for j in range(i + 1, len(all_nodes)):
                distance = models.haversine_distance(
                    all_nodes[i][0], all_nodes[i][1],
                    all_nodes[j][0], all_nodes[j][1]
                )

                if distance <= self.max_range_m:
                    G.add_edge(i, j, weight=distance)

        # Verificar que cada SN tenga camino a al menos una BG
        bg_indices = [i for i, node in enumerate(all_nodes) if node[4] == 1]

        if not bg_indices:
            return False

        for sn_idx in range(len(active_sns)):
            has_path = False
            for bg_idx in bg_indices:
                if nx.has_path(G, sn_idx, bg_idx):
                    has_path = True
                    break

            if not has_path:
                return False

        return True

    def _crossover(self, ind1: creator.Individual, 
                   ind2: creator.Individual) -> Tuple[creator.Individual, creator.Individual]:
        """Operador de crossover de dos puntos"""
        size = len(ind1)
        cx_point1 = random.randint(1, size - 1)
        cx_point2 = random.randint(1, size - 1)

        if cx_point1 > cx_point2:
            cx_point1, cx_point2 = cx_point2, cx_point1

        ind1[cx_point1:cx_point2], ind2[cx_point1:cx_point2] = \
            ind2[cx_point1:cx_point2], ind1[cx_point1:cx_point2]

        return ind1, ind2

    def _mutate(self, individual: creator.Individual) -> Tuple[creator.Individual]:
        """Operador de mutación"""
        for i in range(len(individual)):
            if random.random() < self.mut_rate:
                # Mutar posición o activación
                mutation_type = random.choice(['position', 'activation'])

                if mutation_type == 'position':
                    # Mutar coordenadas ligeramente
                    lat_range = self.area_radius_km / config.LAT_KM_PER_DEGREE
                    lon_range = self.area_radius_km / (config.LAT_KM_PER_DEGREE * 
                                                       np.cos(np.radians(abs(self.center_lat))))

                    individual[i][0] += random.gauss(0, lat_range * 0.1)
                    individual[i][1] += random.gauss(0, lon_range * 0.1)

                    # Clip a área válida
                    individual[i][0] = np.clip(individual[i][0],
                                               self.center_lat - lat_range,
                                               self.center_lat + lat_range)
                    individual[i][1] = np.clip(individual[i][1],
                                               self.center_lon - lon_range,
                                               self.center_lon + lon_range)
                else:
                    # Flip bit de activación
                    individual[i][3] = 1 - individual[i][3]

        return (individual,)

    def run(self, verbose: bool = True) -> Tuple[List, Dict]:
        """
        Ejecuta el algoritmo NSGA-II

        Args:
            verbose: Si True, imprime progreso

        Returns:
            Tupla (población final, estadísticas)
        """
        print(f"\nIniciando NSGA-II...")
        print(f"Población: {self.pop_size}, Generaciones: {self.n_gen}")
        print(f"Mutación: {self.mut_rate}, Crossover: {self.cx_rate}")

        # Crear población inicial
        pop = self.toolbox.population(n=self.pop_size)

        # Estadísticas
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean, axis=0)
        stats.register("std", np.std, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)

        # Hall of Fame para guardar mejores soluciones
        hof = tools.ParetoFront()

        # Ejecutar algoritmo
        pop, logbook = algorithms.eaMuPlusLambda(
            pop, self.toolbox,
            mu=self.pop_size,
            lambda_=self.pop_size,
            cxpb=self.cx_rate,
            mutpb=self.mut_rate,
            ngen=self.n_gen,
            stats=stats,
            halloffame=hof,
            verbose=verbose
        )

        print(f"\nOptimización completada!")
        print(f"Soluciones en frente de Pareto: {len(hof)}")

        return hof, logbook


def extract_solution(individual: creator.Individual) -> Dict:
    """
    Extrae información de una solución

    Args:
        individual: Solución de DEAP

    Returns:
        Diccionario con nodos activos y métricas
    """
    active_sns = [node for node in individual if node[4] == 0 and node[3] == 1]
    active_bgs = [node for node in individual if node[4] == 1 and node[3] == 1]

    num_sns = len(active_sns)
    num_bgs = len(active_bgs)

    cost, coverage = individual.fitness.values

    capex_info = models.calculate_capex(num_sns, num_bgs)
    tco_info = models.calculate_tco(num_sns, num_bgs, years=5)

    return {
        'num_sns': num_sns,
        'num_bgs': num_bgs,
        'sensor_nodes': active_sns,
        'gateway_buoys': active_bgs,
        'relative_cost': cost,
        'coverage_pct': coverage,
        'capex_usd': capex_info['total_capex'],
        'tco_5y_usd': tco_info['tco'],
        'cost_per_coverage': capex_info['total_capex'] / coverage if coverage > 0 else float('inf')
    }
