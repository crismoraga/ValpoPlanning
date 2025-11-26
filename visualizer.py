"""
Funciones de visualización para mapas, topologías y gráficos
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import networkx as nx
from typing import List, Dict, Tuple
import os

import config
import models

# Configurar estilo
plt.style.use('seaborn-v0_8-darkgrid')

def create_output_dirs():
    """Crea directorios de salida si no existen"""
    for dir_name in [config.OUTPUT_CONFIG['figures_dir'], 
                     config.OUTPUT_CONFIG['data_dir'],
                     config.OUTPUT_CONFIG['results_dir']]:
        os.makedirs(dir_name, exist_ok=True)


def plot_bathymetry_3d(bathymetry: np.ndarray, filename: str = None):
    """Gráfico 3D del modelo batimétrico"""
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    x = np.arange(bathymetry.shape[0])
    y = np.arange(bathymetry.shape[1])
    X, Y = np.meshgrid(x, y)

    surf = ax.plot_surface(X, Y, bathymetry, cmap=cm.ocean_r, alpha=0.8)
    ax.set_xlabel('X (100m)')
    ax.set_ylabel('Y (100m)')
    ax.set_zlabel('Profundidad (m)')
    ax.set_title('Modelo Batimétrico 3D - Puerto de Valparaíso')
    fig.colorbar(surf, shrink=0.5, aspect=5, label='Profundidad (m)')

    if filename:
        plt.savefig(os.path.join(config.OUTPUT_CONFIG['figures_dir'], filename), 
                   dpi=config.OUTPUT_CONFIG['dpi'], bbox_inches='tight')
    plt.show()


def plot_pois_distribution(pois: List[Dict], filename: str = None):
    """Gráfico de distribución de POIs"""
    fig, ax = plt.subplots(figsize=(12, 10))

    types_colors = {
        'industrial_discharge': 'red',
        'anchorage': 'blue',
        'sensitive_areas': 'green',
        'bay_entrances': 'orange',
        'critical_monitoring': 'purple'
    }

    for poi in pois:
        poi_type = poi['type']
        color = types_colors.get(poi_type, 'gray')
        radius_deg = poi['coverage_radius_m'] / (config.LAT_KM_PER_DEGREE * 1000)

        circle = plt.Circle((poi['lon'], poi['lat']), radius_deg, 
                           color=color, alpha=0.3, label=poi_type)
        ax.add_patch(circle)
        ax.plot(poi['lon'], poi['lat'], 'o', color=color, markersize=8)

    # Remover duplicados de leyenda
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right')

    ax.set_xlabel('Longitud')
    ax.set_ylabel('Latitud')
    ax.set_title('Distribución de 20 POIs - Puerto de Valparaíso')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    if filename:
        plt.savefig(os.path.join(config.OUTPUT_CONFIG['figures_dir'], filename), 
                   dpi=config.OUTPUT_CONFIG['dpi'], bbox_inches='tight')
    plt.show()


def plot_pareto_front(pareto_solutions: List[Dict], filename: str = None):
    """Gráfico del frente de Pareto"""
    costs = [sol['relative_cost'] for sol in pareto_solutions]
    coverages = [sol['coverage_pct'] for sol in pareto_solutions]

    fig, ax = plt.subplots(figsize=(12, 8))

    ax.scatter(costs, coverages, c='blue', s=100, alpha=0.6, edgecolors='black', linewidth=2)

    for i, sol in enumerate(pareto_solutions):
        ax.annotate(f"{sol['num_sns']}SN+{sol['num_bgs']}BG", 
                   (costs[i], coverages[i]), 
                   xytext=(5, 5), textcoords='offset points', fontsize=9)

    ax.set_xlabel('Costo (unidades relativas)', fontsize=12)
    ax.set_ylabel('Cobertura POIs (%)', fontsize=12)
    ax.set_title('Frente de Pareto: Trade-off Costo vs Cobertura', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    if filename:
        plt.savefig(os.path.join(config.OUTPUT_CONFIG['figures_dir'], filename), 
                   dpi=config.OUTPUT_CONFIG['dpi'], bbox_inches='tight')
    plt.show()


def plot_network_topology(solution: Dict, pois: List[Dict], filename: str = None):
    """Gráfico de topología de red georeferenciada"""
    fig, ax = plt.subplots(figsize=(14, 12))

    # Plot POIs
    for poi in pois:
        radius_deg = poi['coverage_radius_m'] / (config.LAT_KM_PER_DEGREE * 1000)
        circle = plt.Circle((poi['lon'], poi['lat']), radius_deg, 
                           color='yellow', alpha=0.2)
        ax.add_patch(circle)
        ax.plot(poi['lon'], poi['lat'], 'x', color='orange', markersize=6)

    # Plot Sensor Nodes
    sns = solution['sensor_nodes']
    for sn in sns:
        ax.plot(sn[1], sn[0], 'o', color='cyan', markersize=12, 
               markeredgecolor='black', markeredgewidth=1.5, label='SN')

    # Plot Gateway Buoys
    bgs = solution['gateway_buoys']
    for bg in bgs:
        ax.plot(bg[1], bg[0], 's', color='red', markersize=14, 
               markeredgecolor='black', markeredgewidth=1.5, label='BG')

    # Plot Coastal Station
    ax.plot(config.VALPARAISO_CENTER['lon'] - 0.01, 
           config.VALPARAISO_CENTER['lat'] - 0.01, 
           '^', color='green', markersize=16, 
           markeredgecolor='black', markeredgewidth=2, label='EC')

    # Plot Links
    max_range = models.max_communication_range()
    all_nodes = sns + bgs

    for i, node1 in enumerate(all_nodes):
        for node2 in all_nodes[i+1:]:
            dist = models.haversine_distance(node1[0], node1[1], node2[0], node2[1])
            if dist <= max_range:
                ax.plot([node1[1], node2[1]], [node1[0], node2[0]], 
                       'c--', alpha=0.3, linewidth=0.8)

    # Links BG-EC
    ec_lat = config.VALPARAISO_CENTER['lat'] - 0.01
    ec_lon = config.VALPARAISO_CENTER['lon'] - 0.01
    for bg in bgs:
        ax.plot([bg[1], ec_lon], [bg[0], ec_lat], 
               'orange', alpha=0.6, linewidth=2)

    # Remover duplicados de leyenda
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=10)

    ax.set_xlabel('Longitud', fontsize=12)
    ax.set_ylabel('Latitud', fontsize=12)
    ax.set_title(f'Topología Final: {solution["num_sns"]} SNs + {solution["num_bgs"]} BGs\n' +
                f'Cobertura: {solution["coverage_pct"]:.1f}% | CAPEX: ${solution["capex_usd"]:,}', 
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    if filename:
        plt.savefig(os.path.join(config.OUTPUT_CONFIG['figures_dir'], filename), 
                   dpi=config.OUTPUT_CONFIG['dpi'], bbox_inches='tight')
    plt.show()


def plot_convergence(logbook, filename: str = None):
    """Gráfico de convergencia del algoritmo"""
    gen = logbook.select("gen")
    min_costs = [entry[0] for entry in logbook.select("min")]
    max_coverages = [entry[1] for entry in logbook.select("max")]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    ax1.plot(gen, min_costs, 'b-', linewidth=2)
    ax1.set_xlabel('Generación')
    ax1.set_ylabel('Costo Mínimo')
    ax1.set_title('Convergencia: Minimización de Costo')
    ax1.grid(True, alpha=0.3)

    ax2.plot(gen, max_coverages, 'g-', linewidth=2)
    ax2.set_xlabel('Generación')
    ax2.set_ylabel('Cobertura Máxima (%)')
    ax2.set_title('Convergencia: Maximización de Cobertura')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if filename:
        plt.savefig(os.path.join(config.OUTPUT_CONFIG['figures_dir'], filename), 
                   dpi=config.OUTPUT_CONFIG['dpi'], bbox_inches='tight')
    plt.show()
