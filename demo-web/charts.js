// ============================================================================
// UWSN Demo - Gráficos Interactivos con Chart.js
// ============================================================================
(function() {
    'use strict';
    
    const data = window.uwsnData;
    const { configuration, thorp, convergenceSeries, paretoFront, economics, solutionBalanced } = data;
    
    // Registrar plugin de datalabels
    if (typeof ChartDataLabels !== 'undefined') {
        Chart.register(ChartDataLabels);
    }
    
    // Configuración global de Chart.js
    Chart.defaults.color = '#e5e7eb';
    Chart.defaults.font.family = "'Roboto', 'Segoe UI', system-ui, sans-serif";
    Chart.defaults.plugins.legend.labels.color = '#e5e7eb';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    
    const charts = {};
    
    // Paleta de colores moderna
    const COLORS = {
        primary: '#00d1ff',
        secondary: '#7c3aed',
        success: '#22c55e',
        warning: '#f59e0b',
        danger: '#ef4444',
        info: '#3b82f6',
        gradient1: 'rgba(0, 209, 255, 0.2)',
        gradient2: 'rgba(124, 58, 237, 0.2)'
    };

    // ========================================================================
    // GRÁFICO 1: Modelo de Thorp - Absorción vs Frecuencia
    // ========================================================================
    function createThorpAbsorptionChart() {
        const ctx = document.getElementById('thorp-absorption-chart')?.getContext('2d');
        if (!ctx || !thorp) return;
        
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(0, 209, 255, 0.4)');
        gradient.addColorStop(1, 'rgba(0, 209, 255, 0.02)');
        
        charts.thorpAbsorption = new Chart(ctx, {
            type: 'line',
            data: {
                labels: thorp.frequencies.map(f => f + ' kHz'),
                datasets: [
                    {
                        label: 'Coeficiente α (dB/km)',
                        data: thorp.absorptions,
                        borderColor: COLORS.primary,
                        backgroundColor: gradient,
                        borderWidth: 3,
                        tension: 0.4,
                        fill: true,
                        pointRadius: 0,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'Frecuencia de Operación (' + thorp.frequency_khz + ' kHz)',
                        data: thorp.frequencies.map(f => f === thorp.frequency_khz ? thorp.absorption_coefficient : null),
                        borderColor: COLORS.warning,
                        backgroundColor: COLORS.warning,
                        pointRadius: 10,
                        pointHoverRadius: 12,
                        showLine: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { position: 'bottom', labels: { padding: 20 } },
                    title: { 
                        display: true, 
                        text: 'Modelo de Thorp: α(f) - Absorción Acústica Submarina',
                        font: { size: 16, weight: 'bold' },
                        padding: { bottom: 20 }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) { return ctx.dataset.label + ': ' + (ctx.parsed.y?.toFixed(4) || 'N/A') + ' dB/km'; }
                        }
                    },
                    datalabels: { display: false }
                },
                scales: {
                    x: { 
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        title: { display: true, text: 'Frecuencia (kHz)', font: { size: 12 } },
                        ticks: { maxTicksLimit: 20 }
                    },
                    y: { 
                        grid: { color: 'rgba(255,255,255,0.08)' },
                        title: { display: true, text: 'α (dB/km)', font: { size: 12 } },
                        min: 0
                    }
                }
            }
        });
    }

    // ========================================================================
    // GRÁFICO 2: SNR vs Distancia
    // ========================================================================
    function createSNRChart() {
        const ctx = document.getElementById('snr-distance-chart')?.getContext('2d');
        if (!ctx || !thorp) return;
        
        charts.snrDistance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: thorp.distances.map(function(d) { return d + ' m'; }),
                datasets: [
                    {
                        label: 'SNR (dB)',
                        data: thorp.snr_by_distance,
                        borderColor: COLORS.success,
                        backgroundColor: 'rgba(34, 197, 94, 0.15)',
                        borderWidth: 3,
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'SNR Mínimo (' + thorp.min_snr_db + ' dB)',
                        data: thorp.distances.map(function() { return thorp.min_snr_db; }),
                        borderColor: COLORS.danger,
                        borderWidth: 2,
                        borderDash: [10, 5],
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { 
                        display: true, 
                        text: 'Relación Señal-Ruido vs Distancia',
                        font: { size: 16, weight: 'bold' }
                    },
                    datalabels: { display: false }
                },
                scales: {
                    x: { 
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        title: { display: true, text: 'Distancia (m)' },
                        ticks: { maxTicksLimit: 12 }
                    },
                    y: { 
                        grid: { color: 'rgba(255,255,255,0.08)' },
                        title: { display: true, text: 'SNR (dB)' }
                    }
                }
            }
        });
    }

    // ========================================================================
    // GRÁFICO 3: Convergencia del Algoritmo (Dual Axis)
    // ========================================================================
    function createConvergenceChart() {
        const ctx = document.getElementById('convergence-chart')?.getContext('2d');
        if (!ctx || !convergenceSeries?.length) return;
        
        charts.convergence = new Chart(ctx, {
            type: 'line',
            data: {
                labels: convergenceSeries.map(function(p) { return 'G' + p.generation; }),
                datasets: [
                    {
                        label: 'Mejor Cobertura (%)',
                        data: convergenceSeries.map(function(p) { return p.bestCoverage; }),
                        borderColor: COLORS.success,
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        yAxisID: 'y',
                        fill: true
                    },
                    {
                        label: 'Mejor Costo (Unidades)',
                        data: convergenceSeries.map(function(p) { return p.bestCost; }),
                        borderColor: COLORS.warning,
                        backgroundColor: 'rgba(249, 115, 22, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        yAxisID: 'y1',
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { position: 'bottom' },
                    title: { 
                        display: true, 
                        text: 'Convergencia del Algoritmo NSGA-II',
                        font: { size: 16, weight: 'bold' }
                    },
                    datalabels: { display: false }
                },
                scales: {
                    x: { 
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        title: { display: true, text: 'Generación' },
                        ticks: { maxTicksLimit: 15 }
                    },
                    y: {
                        type: 'linear',
                        position: 'left',
                        min: 0,
                        max: 110,
                        grid: { color: 'rgba(34, 197, 94, 0.1)' },
                        title: { display: true, text: 'Cobertura (%)', color: COLORS.success }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        min: 5,
                        max: 30,
                        grid: { drawOnChartArea: false },
                        title: { display: true, text: 'Costo Relativo', color: COLORS.warning }
                    }
                }
            }
        });
    }

    // ========================================================================
    // GRÁFICO 4: Frente de Pareto (Scatter)
    // ========================================================================
    function createParetoChart(canvasId, highlightSolution) {
        var ctx = document.getElementById(canvasId)?.getContext('2d');
        if (!ctx || !paretoFront?.length) return;
        
        var points = paretoFront.map(function(p) { return { x: p.cost_relative, y: p.coverage_pct }; });
        
        var datasets = [
            {
                label: 'Frente de Pareto',
                data: points,
                borderColor: COLORS.primary,
                backgroundColor: 'rgba(0, 209, 255, 0.6)',
                pointRadius: 8,
                pointHoverRadius: 12,
                pointStyle: 'circle'
            }
        ];
        
        if (highlightSolution && solutionBalanced) {
            datasets.push({
                label: 'Solución Seleccionada',
                data: [{ x: solutionBalanced.cost_relative, y: solutionBalanced.coverage_pct }],
                borderColor: COLORS.warning,
                backgroundColor: COLORS.warning,
                pointRadius: 14,
                pointHoverRadius: 18,
                pointStyle: 'star'
            });
        }
        
        charts[canvasId] = new Chart(ctx, {
            type: 'scatter',
            data: { datasets: datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { 
                        display: true, 
                        text: 'Frente de Pareto: Costo vs Cobertura',
                        font: { size: 16, weight: 'bold' }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) { return 'Costo: ' + ctx.parsed.x + ', Cobertura: ' + ctx.parsed.y + '%'; }
                        }
                    },
                    datalabels: {
                        display: highlightSolution,
                        formatter: function(_, ctx) { return ctx.dataset.label === 'Solución Seleccionada' ? '★ Óptima' : ''; },
                        color: '#fff',
                        font: { weight: 'bold', size: 11 },
                        anchor: 'end',
                        align: 'top',
                        offset: 5
                    }
                },
                scales: {
                    x: { 
                        grid: { color: 'rgba(255,255,255,0.08)' },
                        title: { display: true, text: 'Costo Relativo (Unidades)' },
                        min: 5,
                        max: 15
                    },
                    y: { 
                        grid: { color: 'rgba(255,255,255,0.08)' },
                        title: { display: true, text: 'Cobertura (%)' },
                        min: 0,
                        max: 110
                    }
                }
            }
        });
    }

    // ========================================================================
    // GRÁFICO 5: Desglose de CAPEX (Pie)
    // ========================================================================
    function createCapexChart() {
        var ctx = document.getElementById('capex-chart')?.getContext('2d');
        if (!ctx || !economics) return;
        
        var labels = Object.keys(economics.capex_breakdown).map(function(k) {
            return k.replace(/_/g, ' ').replace(/\b\w/g, function(l) { return l.toUpperCase(); });
        });
        var values = Object.values(economics.capex_breakdown);
        
        charts.capex = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        COLORS.success,
                        COLORS.info,
                        COLORS.secondary,
                        COLORS.warning,
                        '#06b6d4',
                        '#ec4899',
                        COLORS.danger
                    ],
                    borderColor: '#0a0f1a',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.5,
                cutout: '55%',
                resizeDelay: 100,
                plugins: {
                    legend: { position: 'right', labels: { padding: 15 } },
                    title: { 
                        display: true, 
                        text: 'CAPEX Total: $' + (economics.capex_usd / 1000).toFixed(0) + 'k USD',
                        font: { size: 16, weight: 'bold' }
                    },
                    datalabels: {
                        color: '#fff',
                        font: { weight: 'bold', size: 10 },
                        formatter: function(v) { return '$' + (v/1000).toFixed(0) + 'k'; }
                    }
                }
            }
        });
    }

    // ========================================================================
    // GRÁFICO 6: Desglose de OPEX (Pie)
    // ========================================================================
    function createOpexChart() {
        var ctx = document.getElementById('opex-chart')?.getContext('2d');
        if (!ctx || !economics) return;
        
        var labels = Object.keys(economics.opex_breakdown).map(function(k) {
            return k.replace(/_/g, ' ').replace(/\b\w/g, function(l) { return l.toUpperCase(); });
        });
        var values = Object.values(economics.opex_breakdown);
        
        charts.opex = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        '#0ea5e9',
                        '#a855f7',
                        '#f97316',
                        COLORS.success,
                        '#facc15',
                        COLORS.danger,
                        '#c084fc'
                    ],
                    borderColor: '#0a0f1a',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.5,
                cutout: '55%',
                resizeDelay: 100,
                plugins: {
                    legend: { position: 'right', labels: { padding: 15 } },
                    title: { 
                        display: true, 
                        text: 'OPEX Anual: $' + (economics.opex_annual_usd / 1000).toFixed(0) + 'k USD',
                        font: { size: 16, weight: 'bold' }
                    },
                    datalabels: {
                        color: '#fff',
                        font: { weight: 'bold', size: 10 },
                        formatter: function(v) { return '$' + (v/1000).toFixed(0) + 'k'; }
                    }
                }
            }
        });
    }

    // ========================================================================
    // GRÁFICO 7: TCO Proyección (Bar)
    // ========================================================================
    function createTCOChart() {
        var ctx = document.getElementById('tco-chart')?.getContext('2d');
        if (!ctx || !economics) return;
        
        var years = [1, 2, 3, 5, 7, 10];
        
        charts.tco = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: years.map(function(y) { return y + (y === 1 ? ' año' : ' años'); }),
                datasets: [
                    {
                        label: 'CAPEX',
                        data: years.map(function() { return economics.capex_usd; }),
                        backgroundColor: COLORS.secondary,
                        stack: 'total'
                    },
                    {
                        label: 'OPEX Acumulado',
                        data: years.map(function(y) { return economics.opex_annual_usd * y; }),
                        backgroundColor: COLORS.success,
                        stack: 'total'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                resizeDelay: 100,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { 
                        display: true, 
                        text: 'Proyección de Costo Total de Propiedad (TCO)',
                        font: { size: 16, weight: 'bold' }
                    },
                    datalabels: {
                        display: true,
                        color: '#fff',
                        font: { weight: 'bold', size: 9 },
                        formatter: function(v, ctx) {
                            if (ctx.datasetIndex === 1) {
                                var total = economics.capex_usd + v;
                                return '$' + (total/1000).toFixed(0) + 'k';
                            }
                            return '';
                        },
                        anchor: 'end',
                        align: 'end'
                    }
                },
                scales: {
                    x: { grid: { display: false } },
                    y: { 
                        grid: { color: 'rgba(255,255,255,0.08)' },
                        title: { display: true, text: 'USD' },
                        ticks: { callback: function(v) { return '$' + (v/1000).toFixed(0) + 'k'; } }
                    }
                }
            }
        });
    }

    // ========================================================================
    // GRÁFICO 8: Path Loss Components (Stacked Area)
    // ========================================================================
    function createPathLossChart() {
        var ctx = document.getElementById('path-loss-chart')?.getContext('2d');
        if (!ctx || !thorp) return;
        
        // Calcular componentes
        var spreadingLoss = thorp.distances.map(function(d) { return 20 * Math.log10(d); });
        var absorptionLoss = thorp.distances.map(function(d) { return thorp.absorption_coefficient * (d / 1000); });
        
        charts.pathLoss = new Chart(ctx, {
            type: 'line',
            data: {
                labels: thorp.distances.map(function(d) { return d + 'm'; }),
                datasets: [
                    {
                        label: 'Pérdida Total',
                        data: thorp.path_loss_by_distance,
                        borderColor: COLORS.danger,
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        borderWidth: 3,
                        fill: true
                    },
                    {
                        label: 'Spreading Loss (20·log₁₀d)',
                        data: spreadingLoss,
                        borderColor: COLORS.info,
                        borderWidth: 2,
                        borderDash: [5, 5]
                    },
                    {
                        label: 'Absorption Loss (α·d)',
                        data: absorptionLoss,
                        borderColor: COLORS.success,
                        borderWidth: 2,
                        borderDash: [5, 5]
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { 
                        display: true, 
                        text: 'Componentes de Pérdida del Enlace Acústico',
                        font: { size: 16, weight: 'bold' }
                    },
                    datalabels: { display: false }
                },
                scales: {
                    x: { 
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        title: { display: true, text: 'Distancia' },
                        ticks: { maxTicksLimit: 12 }
                    },
                    y: { 
                        grid: { color: 'rgba(255,255,255,0.08)' },
                        title: { display: true, text: 'Pérdida (dB)' }
                    }
                }
            }
        });
    }

    // ========================================================================
    // INICIALIZACIÓN PRINCIPAL
    // ========================================================================
    function initCharts() {
        console.log('📊 Inicializando gráficos...');
        
        try {
            createThorpAbsorptionChart();
            createSNRChart();
            createConvergenceChart();
            createParetoChart('pareto-chart', false);
            createParetoChart('final-pareto-chart', true);
            createCapexChart();
            createOpexChart();
            createTCOChart();
            createPathLossChart();
            
            console.log('✅ Gráficos inicializados');
        } catch (error) {
            console.error('❌ Error inicializando gráficos:', error);
        }
    }

    // Exponer API
    window.UWSNCharts = { 
        initCharts: initCharts, 
        charts: charts,
        createParetoChart: createParetoChart
    };

})();
