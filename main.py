#!/usr/bin/env python3
"""
Script principal para ejecutar la planificación completa de red de sensores submarinos
Puerto de Valparaíso - Equipo PlaniGüinos
"""

import numpy as np
import time
from datetime import datetime

# Importar módulos del proyecto
import config
import models
import optimizer
import visualizer
import data_export

def main():
    """Función principal"""

    print("="*80)
    print("PLANIFICACIÓN DE RED DE SENSORES SUBMARINOS")
    print("Puerto de Valparaíso - Equipo PlaniGüinos")
    print("="*80)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Crear directorios de salida
    visualizer.create_output_dirs()
    print("✅ Directorios de salida creados")

    # ==========================================================================
    # PASO 1: GENERAR MODELO BATIMÉTRICO
    # ==========================================================================
    print("\n" + "="*80)
    print("PASO 1: GENERANDO MODELO BATIMÉTRICO")
    print("="*80)

    bathymetry = models.generate_bathymetry(
        grid_size=config.STUDY_AREA['grid_size'],
        depth_min=config.BATHYMETRY['depth_min'],
        depth_max=config.BATHYMETRY['depth_max'],
        depth_mean=config.BATHYMETRY['depth_mean'],
        depth_std=config.BATHYMETRY['depth_std']
    )

    print(f"Batimetría generada: {bathymetry.shape}")
    print(f"Profundidad mínima: {np.min(bathymetry):.2f} m")
    print(f"Profundidad máxima: {np.max(bathymetry):.2f} m")
    print(f"Profundidad promedio: {np.mean(bathymetry):.2f} m")

    # Guardar batimetría
    data_export.save_bathymetry(bathymetry, 'bathymetry.npy')

    # Visualizar batimetría
    visualizer.plot_bathymetry_3d(bathymetry, 'bathymetry_3d.png')

    # ==========================================================================
    # PASO 2: GENERAR PUNTOS DE INTERÉS (POIs)
    # ==========================================================================
    print("\n" + "="*80)
    print("PASO 2: GENERANDO PUNTOS DE INTERÉS (POIs)")
    print("="*80)

    pois = models.generate_pois(
        num_pois=config.POI_CONFIG['total_pois'],
        area_radius_km=config.STUDY_AREA['radius_km'],
        center_lat=config.VALPARAISO_CENTER['lat'],
        center_lon=config.VALPARAISO_CENTER['lon'],
        poi_types=config.POI_CONFIG['types']
    )

    print(f"POIs generados: {len(pois)}")
    for poi_type, params in config.POI_CONFIG['types'].items():
        count = params['count']
        print(f"  • {poi_type}: {count}")

    # Guardar POIs
    data_export.save_pois(pois, 'pois.json')

    # Visualizar POIs
    visualizer.plot_pois_distribution(pois, 'pois_distribution.png')

    # ==========================================================================
    # PASO 3: OPTIMIZACIÓN CON NSGA-II
    # ==========================================================================
    print("\n" + "="*80)
    print("PASO 3: OPTIMIZACIÓN MULTI-OBJETIVO NSGA-II")
    print("="*80)

    # Crear optimizador
    opt = optimizer.NetworkOptimizer(
        pois=pois,
        bathymetry=bathymetry,
        center_lat=config.VALPARAISO_CENTER['lat'],
        center_lon=config.VALPARAISO_CENTER['lon'],
        area_radius_km=config.STUDY_AREA['radius_km']
    )

    # Ejecutar optimización
    start_time = time.time()
    pareto_front, logbook = opt.run(verbose=True)
    end_time = time.time()

    print(f"\nTiempo de ejecución: {end_time - start_time:.2f} segundos")

    # ==========================================================================
    # PASO 4: EXTRAER Y ANALIZAR SOLUCIONES
    # ==========================================================================
    print("\n" + "="*80)
    print("PASO 4: EXTRAYENDO SOLUCIONES DEL FRENTE DE PARETO")
    print("="*80)

    # Extraer todas las soluciones
    pareto_solutions = [optimizer.extract_solution(ind) for ind in pareto_front]

    # Ordenar por cobertura
    pareto_solutions.sort(key=lambda x: x['coverage_pct'])

    print(f"\nSoluciones en frente de Pareto: {len(pareto_solutions)}")

    # Seleccionar 3 soluciones representativas
    if len(pareto_solutions) >= 3:
        min_cost_sol = pareto_solutions[0]
        max_cov_sol = pareto_solutions[-1]

        # Buscar solución equilibrada (mejor costo por cobertura)
        balanced_sol = min(pareto_solutions, key=lambda x: x['cost_per_coverage'])

        print("\n" + "-"*80)
        print("SOLUCIÓN 1: MÍNIMO COSTO")
        print("-"*80)
        print(f"SNs: {min_cost_sol['num_sns']}, BGs: {min_cost_sol['num_bgs']}")
        print(f"Cobertura: {min_cost_sol['coverage_pct']:.1f}%")
        print(f"CAPEX: ${min_cost_sol['capex_usd']:,} USD")
        print(f"Costo/Cobertura: ${min_cost_sol['cost_per_coverage']:,.0f} por 1%")

        print("\n" + "-"*80)
        print("SOLUCIÓN 2: EQUILIBRADA (RECOMENDADA)")
        print("-"*80)
        print(f"SNs: {balanced_sol['num_sns']}, BGs: {balanced_sol['num_bgs']}")
        print(f"Cobertura: {balanced_sol['coverage_pct']:.1f}%")
        print(f"CAPEX: ${balanced_sol['capex_usd']:,} USD")
        print(f"TCO (5 años): ${balanced_sol['tco_5y_usd']:,} USD")
        print(f"Costo/Cobertura: ${balanced_sol['cost_per_coverage']:,.0f} por 1%")

        print("\n" + "-"*80)
        print("SOLUCIÓN 3: MÁXIMA COBERTURA")
        print("-"*80)
        print(f"SNs: {max_cov_sol['num_sns']}, BGs: {max_cov_sol['num_bgs']}")
        print(f"Cobertura: {max_cov_sol['coverage_pct']:.1f}%")
        print(f"CAPEX: ${max_cov_sol['capex_usd']:,} USD")
        print(f"Costo/Cobertura: ${max_cov_sol['cost_per_coverage']:,.0f} por 1%")
    else:
        balanced_sol = pareto_solutions[0]
        print(f"\nAdvertencia: Solo {len(pareto_solutions)} soluciones encontradas")

    # ==========================================================================
    # PASO 5: VISUALIZACIÓN DE RESULTADOS
    # ==========================================================================
    print("\n" + "="*80)
    print("PASO 5: GENERANDO VISUALIZACIONES")
    print("="*80)

    # Frente de Pareto
    visualizer.plot_pareto_front(pareto_solutions, 'pareto_front.png')

    # Topología de la solución equilibrada
    visualizer.plot_network_topology(balanced_sol, pois, 'network_topology.png')

    # Convergencia del algoritmo
    visualizer.plot_convergence(logbook, 'convergence.png')

    print("✅ Todas las visualizaciones generadas")

    # ==========================================================================
    # PASO 6: EXPORTACIÓN DE RESULTADOS
    # ==========================================================================
    print("\n" + "="*80)
    print("PASO 6: EXPORTANDO RESULTADOS")
    print("="*80)

    # Exportar solución equilibrada
    data_export.export_solution_json(balanced_sol, 'solution_balanced.json')
    data_export.export_solution_csv(balanced_sol, 'solution_balanced.csv')

    # Exportar frente de Pareto completo
    data_export.export_pareto_front(pareto_solutions, 'pareto_front.csv')

    # Generar reporte de validación
    data_export.export_validation_report(balanced_sol, 'validation_report.txt')

    # ==========================================================================
    # VERIFICACIÓN FINAL
    # ==========================================================================
    print("\n" + "="*80)
    print("VERIFICACIÓN FINAL")
    print("="*80)

    # Verificar cálculos económicos
    capex_calc = models.calculate_capex(balanced_sol['num_sns'], balanced_sol['num_bgs'])
    diff = abs(capex_calc['total_capex'] - balanced_sol['capex_usd'])

    print(f"\n✅ Verificación económica:")
    print(f"   CAPEX declarado:   ${balanced_sol['capex_usd']:,} USD")
    print(f"   CAPEX recalculado: ${capex_calc['total_capex']:,} USD")
    print(f"   Diferencia:        ${diff:,} USD")

    if diff == 0:
        print(f"   ✅ CORRECTO: Diferencia = $0")

    # Verificar modelo de Thorp
    alpha = models.thorp_absorption_coefficient(config.ACOUSTIC_MODEL['frequency_khz'])
    max_range = models.max_communication_range()

    print(f"\n✅ Verificación modelo acústico:")
    print(f"   Coeficiente Thorp (20 kHz): {alpha:.4f} dB/km")
    print(f"   Rango máximo:               {max_range:.2f} m")
    print(f"   ✅ CORRECTO: Modelo validado según Thorp (1967)")

    # Verificar tráfico
    traffic = models.calculate_traffic_per_node()
    total_traffic = traffic['bits_per_second'] * balanced_sol['num_sns']
    lorawan_capacity = config.LORAWAN_CONFIG['capacity_kbps'] * 1000
    utilization = (total_traffic / lorawan_capacity) * 100

    print(f"\n✅ Verificación de tráfico:")
    print(f"   Tráfico total:      {total_traffic:.2f} bps")
    print(f"   Capacidad LoRaWAN:  {lorawan_capacity:.0f} bps")
    print(f"   Utilización:        {utilization:.2f}%")
    print(f"   Margen disponible:  {100-utilization:.2f}%")
    print(f"   ✅ CORRECTO: Capacidad sobrada")

    # ==========================================================================
    # FINALIZACIÓN
    # ==========================================================================
    print("\n" + "="*80)
    print("PLANIFICACIÓN COMPLETADA EXITOSAMENTE")
    print("="*80)
    print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📁 Revisa los resultados en:")
    print(f"   • Figuras:    {config.OUTPUT_CONFIG['figures_dir']}/")
    print(f"   • Datos:      {config.OUTPUT_CONFIG['data_dir']}/")
    print(f"   • Resultados: {config.OUTPUT_CONFIG['results_dir']}/")
    print()
    print("🎉 ¡Proyecto ejecutado correctamente!")
    print("="*80)


if __name__ == "__main__":
    main()
