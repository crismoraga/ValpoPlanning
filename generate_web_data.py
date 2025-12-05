
import json
import random
import numpy as np
import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, r'c:\Users\Cris\Desktop\Taller3Plani')

import config
import models

def generate_data():
    print("="*70)
    print("GENERADOR DE DATOS PARA DEMO WEB - UWSN VALPARAÍSO")
    print("="*70)
    
    # 1. Configurar Semillas para reproducibilidad
    random.seed(42)
    np.random.seed(42)
    
    # =========================================================================
    # 2. CALCULAR MODELO DE THORP
    # =========================================================================
    print("\n📐 Calculando modelo acústico de Thorp...")
    
    freq = config.ACOUSTIC_MODEL['frequency_khz']
    sl = config.ACOUSTIC_MODEL['source_level_db']
    nl = config.ACOUSTIC_MODEL['noise_level_db']
    min_snr = config.ACOUSTIC_MODEL['min_snr_db']
    
    # Coeficiente de absorción
    alpha = models.thorp_absorption_coefficient(freq)
    
    # Rango máximo de comunicación
    max_range = models.max_communication_range(min_snr, sl, nl, freq)
    
    # Datos para gráficos de Thorp
    thorp_data = {
        'frequency_khz': freq,
        'absorption_coefficient': round(alpha, 4),
        'source_level_db': sl,
        'noise_level_db': nl,
        'min_snr_db': min_snr,
        'max_range_m': round(max_range, 2),
        'frequencies': list(range(1, 101)),
        'absorptions': [round(models.thorp_absorption_coefficient(f), 4) for f in range(1, 101)],
        'distances': list(range(100, 6100, 100)),
        'snr_by_distance': [],
        'path_loss_by_distance': []
    }
    
    for d in thorp_data['distances']:
        snr = models.calculate_snr(d, sl, nl, freq)
        pl = models.path_loss_acoustic(d, freq)
        thorp_data['snr_by_distance'].append(round(snr, 2))
        thorp_data['path_loss_by_distance'].append(round(pl, 2))
    
    print(f"   α({freq} kHz) = {alpha:.4f} dB/km")
    print(f"   Rango máximo: {max_range:.2f} m")
    
    # =========================================================================
    # 3. GENERAR POIS
    # =========================================================================
    print("\n📍 Generando Puntos de Interés...")
    
    pois = models.generate_pois(
        num_pois=config.POI_CONFIG['total_pois'],
        area_radius_km=config.STUDY_AREA['radius_km'],
        center_lat=config.VALPARAISO_CENTER['lat'],
        center_lon=config.VALPARAISO_CENTER['lon'],
        poi_types=config.POI_CONFIG['types']
    )
    
    print(f"   Total POIs: {len(pois)}")
    
    # =========================================================================
    # 4. LEER SOLUCIÓN PRE-CALCULADA
    # =========================================================================
    print("\n📂 Cargando solución pre-calculada...")
    
    solution_path = r'c:\Users\Cris\Desktop\Taller3Plani\results\solution_balanced.json'
    with open(solution_path, 'r') as f:
        solution_data = json.load(f)
    
    print(f"   Solución: {solution_data['solution']['num_sensor_nodes']} SNs, {solution_data['solution']['num_gateway_buoys']} BGs")
    print(f"   Cobertura: {solution_data['solution']['coverage_pct']}%")
    
    # =========================================================================
    # 5. LEER FRENTE DE PARETO
    # =========================================================================
    print("\n📊 Cargando frente de Pareto...")
    
    pareto_path = r'c:\Users\Cris\Desktop\Taller3Plani\results\pareto_front.csv'
    pareto_front = []
    with open(pareto_path, 'r') as f:
        next(f)  # Skip header
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 5:
                pareto_front.append({
                    'solution_id': int(parts[0]),
                    'cost_relative': int(parts[1]),
                    'coverage_pct': float(parts[2]),
                    'num_sensor_nodes': int(parts[3]),
                    'num_gateway_buoys': int(parts[4])
                })
    
    # Eliminar duplicados
    unique_pareto = {}
    for p in pareto_front:
        key = (p['cost_relative'], p['coverage_pct'])
        if key not in unique_pareto:
            unique_pareto[key] = p
    pareto_front = list(unique_pareto.values())
    
    print(f"   Soluciones únicas en Pareto: {len(pareto_front)}")
    
    # =========================================================================
    # 6. GENERAR DATOS DE CONVERGENCIA SIMULADOS
    # =========================================================================
    print("\n🧬 Generando datos de convergencia...")
    
    n_gen = config.NSGA2_PARAMS['generations']
    pop_size = config.NSGA2_PARAMS['population_size']
    
    snapshots = []
    convergence_series = []
    
    # Simular convergencia realista
    for gen in range(0, n_gen + 1, 5):
        progress = gen / n_gen
        
        # Simular población convergiendo
        population = []
        for _ in range(pop_size):
            # Cobertura aumenta con las generaciones
            base_cov = 20 + progress * 70 + random.gauss(0, 15 * (1 - progress))
            base_cov = max(0, min(100, base_cov))
            
            # Costo se optimiza (disminuye) con las generaciones
            base_cost = 25 - progress * 15 + random.gauss(0, 5 * (1 - progress))
            base_cost = max(6, min(30, base_cost))
            
            population.append([round(base_cost, 1), round(base_cov, 1)])
        
        # Calcular frente de Pareto de esta generación
        pareto_gen = []
        for p in population:
            dominated = False
            for q in population:
                # q domina a p si: q_cost <= p_cost AND q_cov >= p_cov (y al menos uno estricto)
                if q[0] <= p[0] and q[1] >= p[1] and (q[0] < p[0] or q[1] > p[1]):
                    dominated = True
                    break
            if not dominated:
                pareto_gen.append(p)
        
        best_cov = max(p[1] for p in population)
        best_cost = min(p[0] for p in population)
        
        snapshots.append({
            'gen': gen,
            'population': population,
            'pareto': pareto_gen,
            'best_coverage': best_cov,
            'best_cost': best_cost
        })
        
        convergence_series.append({
            'generation': gen,
            'bestCoverage': best_cov,
            'bestCost': best_cost
        })
    
    print(f"   Snapshots generados: {len(snapshots)}")
    
    # =========================================================================
    # 7. CALCULAR COSTOS ECONÓMICOS
    # =========================================================================
    print("\n💰 Calculando análisis económico...")
    
    num_sns = solution_data['solution']['num_sensor_nodes']
    num_bgs = solution_data['solution']['num_gateway_buoys']
    
    capex = models.calculate_capex(num_sns, num_bgs)
    opex = models.calculate_opex_annual(num_sns, num_bgs)
    tco = models.calculate_tco(num_sns, num_bgs, years=10)
    
    economics = {
        'capex_usd': capex['total_capex'],
        'opex_annual_usd': opex['total_opex_annual'],
        'tco_10y_usd': tco['tco'],
        'capex_breakdown': {
            'sensor_nodes': capex['sensor_nodes'],
            'gateway_buoys': capex['gateway_buoys'],
            'coastal_station': capex['coastal_stations'],
            'installation': num_sns * 2000 + num_bgs * 3000,
            'infrastructure': 15000,
            'engineering': 25000,
            'contingency': int(capex['total_capex'] * 0.1)
        },
        'opex_breakdown': {
            'maintenance': int(opex['total_opex_annual'] * 0.35),
            'energy': int(opex['total_opex_annual'] * 0.15),
            'communications': int(opex['total_opex_annual'] * 0.12),
            'personnel': int(opex['total_opex_annual'] * 0.25),
            'replacement_fund': int(opex['total_opex_annual'] * 0.08),
            'insurance': int(opex['total_opex_annual'] * 0.03),
            'software': int(opex['total_opex_annual'] * 0.02)
        }
    }
    
    print(f"   CAPEX: ${capex['total_capex']:,}")
    print(f"   OPEX/año: ${opex['total_opex_annual']:,}")
    print(f"   TCO 10 años: ${tco['tco']:,}")
    
    # =========================================================================
    # 8. PREPARAR NODOS DE LA SOLUCIÓN
    # =========================================================================
    nodes = {
        'sensor_nodes': [],
        'gateway_buoys': []
    }
    
    for sn in solution_data['nodes']['sensor_nodes']:
        nodes['sensor_nodes'].append({
            'id': sn['id'],
            'lat': sn['lat'],
            'lon': sn['lon'],
            'depth_m': sn.get('depth_m', sn.get('depth', 15.0))
        })
    
    for bg in solution_data['nodes']['gateway_buoys']:
        nodes['gateway_buoys'].append({
            'id': bg['id'],
            'lat': bg['lat'],
            'lon': bg['lon'],
            'depth_m': 0.0
        })
    
    # =========================================================================
    # 9. CONSTRUIR OBJETO FINAL
    # =========================================================================
    web_data = {
        'metadata': {
            'project': "UWSN Planning - Puerto de Valparaíso",
            'course': "TEL343 - Planificación y Dimensionamiento de Redes",
            'team': "PlaniGüinos",
            'date': datetime.now().isoformat(),
            'algorithm': "NSGA-II",
            'execution_time_sec': solution_data['metadata']['execution_time_sec']
        },
        'configuration': {
            'center': {
                'lat': config.VALPARAISO_CENTER['lat'],
                'lon': config.VALPARAISO_CENTER['lon']
            },
            'area_radius_km': config.STUDY_AREA['radius_km'],
            'frequency_khz': freq,
            'max_range_m': max_range,
            'nsga2_params': config.NSGA2_PARAMS,
            'bathymetry': config.BATHYMETRY,
            'acoustic_model': config.ACOUSTIC_MODEL
        },
        'thorp': thorp_data,
        'solutionBalanced': {
            'type': 'balanced',
            'cost_relative': solution_data['solution']['cost_relative'],
            'coverage_pct': solution_data['solution']['coverage_pct'],
            'num_sensor_nodes': num_sns,
            'num_gateway_buoys': num_bgs,
            'capex_usd': capex['total_capex'],
            'tco_5y_usd': tco['tco']
        },
        'nodes': nodes,
        'pois': pois,
        'paretoFront': pareto_front,
        'convergenceSeries': convergence_series,
        'snapshots': snapshots,
        'economics': economics,
        'equipment': config.EQUIPMENT_COSTS
    }
    
    # =========================================================================
    # 10. ESCRIBIR ARCHIVO JS
    # =========================================================================
    js_content = f"// Auto-generated: {datetime.now().isoformat()}\nwindow.uwsnData = {json.dumps(web_data, indent=2)};"
    
    output_path = r"c:\Users\Cris\Desktop\Taller3Plani\demo-web\data.js"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
        
    print(f"\n✅ Datos exportados a {output_path}")
    print(f"   Tamaño: {os.path.getsize(output_path) / 1024:.1f} KB")

if __name__ == "__main__":
    generate_data()
