#!/usr/bin/env python3
"""
Script para analizar resultados generados por main.py
"""

import json
import csv
import numpy as np
import os

import config
import models

def load_solution(filename: str = 'solution_balanced.json'):
    """Carga una solución desde JSON"""
    filepath = os.path.join(config.OUTPUT_CONFIG['results_dir'], filename)

    with open(filepath, 'r') as f:
        return json.load(f)


def load_pareto_front(filename: str = 'pareto_front.csv'):
    """Carga frente de Pareto desde CSV"""
    filepath = os.path.join(config.OUTPUT_CONFIG['results_dir'], filename)

    solutions = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            solutions.append({
                'solution_id': int(row['Solution_ID']),
                'num_sns': int(row['Num_SNs']),
                'num_bgs': int(row['Num_BGs']),
                'relative_cost': float(row['Relative_Cost']),
                'coverage_pct': float(row['Coverage_Pct']),
                'capex_usd': float(row['CAPEX_USD']),
                'tco_5y_usd': float(row['TCO_5Y_USD']),
                'cost_per_coverage': float(row['Cost_per_Coverage'])
            })

    return solutions


def analyze_solution(solution: dict):
    """Analiza en detalle una solución"""

    print("="*80)
    print("ANÁLISIS DETALLADO DE SOLUCIÓN")
    print("="*80)

    print(f"\n📊 COMPOSICIÓN DE RED")
    print(f"   Nodos Sensores:  {solution['num_sns']}")
    print(f"   Boyas Gateway:   {solution['num_bgs']}")
    print(f"   Estación Costera: 1")
    print(f"   TOTAL NODOS:     {solution['num_sns'] + solution['num_bgs'] + 1}")

    print(f"\n💰 ANÁLISIS ECONÓMICO DETALLADO")
    capex = models.calculate_capex(solution['num_sns'], solution['num_bgs'])
    opex = models.calculate_opex_annual(solution['num_sns'], solution['num_bgs'])
    tco = models.calculate_tco(solution['num_sns'], solution['num_bgs'], years=5)

    print(f"   CAPEX:")
    print(f"      • Nodos Sensores:   ${capex['sensor_nodes']:,}")
    print(f"      • Boyas Gateway:    ${capex['gateway_buoys']:,}")
    print(f"      • Est. Costera:     ${capex['coastal_stations']:,}")
    print(f"      • TOTAL:            ${capex['total_capex']:,}")

    print(f"\n   OPEX ANUAL:")
    print(f"      • Mant. SNs (15%):  ${opex['sensor_nodes']:,}")
    print(f"      • Mant. BGs (20%):  ${opex['gateway_buoys']:,}")
    print(f"      • Operación EC:     ${opex['coastal_station']:,}")
    print(f"      • TOTAL:            ${opex['total_opex_annual']:,}")

    print(f"\n   TCO (5 AÑOS):")
    print(f"      • CAPEX:            ${tco['capex']:,}")
    print(f"      • OPEX (5 años):    ${tco['opex_total']:,}")
    print(f"      • TCO TOTAL:        ${tco['tco']:,}")

    roi_years = tco['capex'] / opex['total_opex_annual']
    print(f"\n   ROI: {roi_years:.1f} años")

    print(f"\n📡 ANÁLISIS DE TRÁFICO")
    traffic = models.calculate_traffic_per_node()

    print(f"   Por Nodo Sensor:")
    print(f"      • {traffic['bytes_per_minute']:.2f} bytes/min")
    print(f"      • {traffic['bits_per_second']:.2f} bps")

    total_traffic = traffic['bits_per_second'] * solution['num_sns']
    print(f"\n   Tráfico Total ({solution['num_sns']} SNs):")
    print(f"      • {total_traffic:.2f} bps")

    lorawan_cap = config.LORAWAN_CONFIG['capacity_kbps'] * 1000
    utilization = (total_traffic / lorawan_cap) * 100

    print(f"\n   Canal LoRaWAN:")
    print(f"      • Capacidad:    {lorawan_cap:,} bps")
    print(f"      • Utilización:  {utilization:.2f}%")
    print(f"      • Margen:       {100-utilization:.2f}%")

    print(f"\n📏 MODELO ACÚSTICO")
    alpha = models.thorp_absorption_coefficient(20.0)
    max_range = models.max_communication_range()

    print(f"   Frecuencia:           20 kHz")
    print(f"   Coef. Absorción:      {alpha:.4f} dB/km")
    print(f"   Rango Máximo:         {max_range:.2f} m")
    print(f"   SNR Mínimo:           {config.ACOUSTIC_MODEL['min_snr_db']} dB")

    print(f"\n🎯 COBERTURA")
    print(f"   POIs Cubiertos:       {solution['coverage_pct']:.1f}%")
    print(f"   Costo por 1% Cob.:    ${solution['cost_per_coverage']:,.0f}")


def compare_solutions(solutions: list):
    """Compara múltiples soluciones"""

    print("\n" + "="*80)
    print("COMPARACIÓN DE SOLUCIONES DEL FRENTE DE PARETO")
    print("="*80)

    print(f"\nNúmero de soluciones: {len(solutions)}")

    # Encontrar extremos
    min_cost = min(solutions, key=lambda x: x['capex_usd'])
    max_cov = max(solutions, key=lambda x: x['coverage_pct'])
    best_efficiency = min(solutions, key=lambda x: x['cost_per_coverage'])

    print(f"\n📉 SOLUCIÓN MÍN. COSTO:")
    print(f"   Config:      {min_cost['num_sns']} SNs + {min_cost['num_bgs']} BGs")
    print(f"   CAPEX:       ${min_cost['capex_usd']:,}")
    print(f"   Cobertura:   {min_cost['coverage_pct']:.1f}%")

    print(f"\n📈 SOLUCIÓN MÁX. COBERTURA:")
    print(f"   Config:      {max_cov['num_sns']} SNs + {max_cov['num_bgs']} BGs")
    print(f"   CAPEX:       ${max_cov['capex_usd']:,}")
    print(f"   Cobertura:   {max_cov['coverage_pct']:.1f}%")

    print(f"\n⭐ SOLUCIÓN MÁS EFICIENTE:")
    print(f"   Config:      {best_efficiency['num_sns']} SNs + {best_efficiency['num_bgs']} BGs")
    print(f"   CAPEX:       ${best_efficiency['capex_usd']:,}")
    print(f"   Cobertura:   {best_efficiency['coverage_pct']:.1f}%")
    print(f"   $/1% Cob.:   ${best_efficiency['cost_per_coverage']:,.0f}")


def main():
    """Función principal"""

    print("="*80)
    print("ANÁLISIS DE RESULTADOS")
    print("Puerto de Valparaíso - Equipo PlaniGüinos")
    print("="*80)

    try:
        # Cargar solución equilibrada
        solution = load_solution()
        analyze_solution(solution)

        # Cargar y comparar frente de Pareto
        pareto_solutions = load_pareto_front()
        compare_solutions(pareto_solutions)

        print("\n" + "="*80)
        print("✅ ANÁLISIS COMPLETADO")
        print("="*80)

    except FileNotFoundError as e:
        print(f"\n❌ Error: No se encontraron archivos de resultados.")
        print(f"   Primero ejecuta: python main.py")
        print(f"\n   Detalles: {e}")


if __name__ == "__main__":
    main()
