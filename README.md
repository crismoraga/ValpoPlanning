# Red de Sensores Submarinos - Puerto de Valparaíso

Planificación y dimensionamiento de red de sensores submarinos usando optimización multi-objetivo NSGA-II.

## 📋 Descripción

Este proyecto implementa una metodología completa para planificar y dimensionar una red de sensores submarinos híbrida en el Puerto de Valparaíso, Chile. Utiliza el algoritmo genético NSGA-II para optimizar simultáneamente dos objetivos en conflicto:
- Minimizar el costo de implementación
- Maximizar la cobertura de Puntos de Interés (POIs)

## 🗂️ Estructura del Proyecto

```
uwsn-planning/
├── config.py           # Configuración global del proyecto
├── models.py           # Modelos matemáticos (Thorp, Shannon, etc.)
├── optimizer.py        # Implementación de NSGA-II
├── visualizer.py       # Funciones de visualización
├── data_export.py      # Exportación de resultados
├── main.py             # Script principal de ejecución
├── analyze_results.py  # Script de análisis de resultados
├── requirements.txt    # Dependencias del proyecto
├── README.md           # Este archivo
├── figures/            # Gráficos generados
├── data/               # Datos intermedios
└── results/            # Resultados finales
```

## 🚀 Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/crismoraga/valpo-uwsn-planning.git
cd valpo-uwsn-planning
```

2. Crear entorno virtual (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## 💻 Uso

### Ejecución básica

```bash
python main.py
```

Este comando:
1. Genera el modelo batimétrico del Puerto de Valparaíso
2. Crea 20 Puntos de Interés (POIs) estratégicos
3. Ejecuta NSGA-II con 100 individuos por 150 generaciones
4. Genera visualizaciones de resultados
5. Exporta datos en múltiples formatos

### Análisis de resultados

```bash
python analyze_results.py
```

## 📊 Resultados

El proyecto genera:

### Figuras
- `bathymetry_3d.png`: Modelo batimétrico 3D
- `pois_distribution.png`: Distribución de POIs
- `pareto_front.png`: Frente de Pareto (costo vs cobertura)
- `network_topology.png`: Topología final georeferenciada
- `convergence.png`: Gráficos de convergencia del algoritmo

### Datos
- `bathymetry.npy`: Matriz batimétrica
- `pois.json`: Puntos de Interés
- `solution_balanced.json`: Solución equilibrada seleccionada
- `solution_balanced.csv`: Coordenadas de nodos
- `pareto_front.csv`: Todas las soluciones del frente de Pareto
- `validation_report.txt`: Reporte completo de validación

## 🔧 Configuración

Edita `config.py` para personalizar:
- Coordenadas del área de estudio
- Parámetros batimétricos
- Número y tipos de POIs
- Parámetros del modelo acústico de Thorp
- Costos de equipamiento
- Parámetros de NSGA-II

## 📐 Metodología

### Modelo de Propagación Acústica

Implementa el **modelo de Thorp (1967)** para calcular la absorción acústica submarina:

```python
α(f) = (0.11f²)/(1+f²) + (44f²)/(4100+f²) + 0.000275f² + 0.003
```

### Capacidad del Canal

Usa la **ecuación de Shannon** para estimar capacidad:

```python
C = B log₂(1 + SNR)
```

### Algoritmo NSGA-II

- Población: 100 individuos
- Generaciones: 150
- Mutación: 15%
- Crossover: 80%
- Restricción: Conectividad 100% (verificada por BFS)

## 📈 Resultados Típicos

**Configuración Equilibrada:**
- 9 Nodos Sensores (SN)
- 2 Boyas Gateway (BG)
- 1 Estación Costera (EC)
- Cobertura: 35% de POIs
- CAPEX: $286,500 USD
- TCO (5 años): $638,875 USD
- ROI: 3.5 años

## 🧪 Validación

Todos los resultados son verificados:
- ✅ Cálculos económicos (diferencia $0)
- ✅ Modelo de Thorp (α = 4.13 dB/km @ 20 kHz)
- ✅ Rango de comunicación (4,999 m)
- ✅ Conectividad de red (BFS)
- ✅ Coordenadas geográficas (SHOA)

## 👥 Autores

**Equipo PlaniGüinos**
- Clemente Mujica
- Cristóbal Moraga
- Iván Weber

Universidad Técnica Federico Santa María
Valparaíso, Chile

## 📄 Licencia

MIT License

## 🙏 Agradecimientos

- SHOA (Servicio Hidrográfico y Oceanográfico de la Armada de Chile)
- Autoridad Portuaria de Valparaíso
- UTFSM (Universidad Técnica Federico Santa María)

## 📚 Referencias

1. K. Deb et al., "A fast and elitist multiobjective genetic algorithm: NSGA-II", IEEE Trans. Evolutionary Computation, 2002.
2. I. F. Akyildiz et al., "Underwater Acoustic Sensor Networks: Research Challenges", Ad Hoc Networks, 2005.
3. W. H. Thorp, "Analytic Description of the Low-Frequency Attenuation Coefficient", J. Acoustical Society of America, 1967.
