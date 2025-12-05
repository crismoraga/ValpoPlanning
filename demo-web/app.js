// ============================================================================
// UWSN Demo - Orquestación Principal
// ============================================================================
(function() {
    'use strict';
    
    // Estado de la aplicación
    const state = {
        currentSection: 'intro',
        initialized: false,
        modulesReady: {
            charts: false,
            map: false,
            evolution: false,
            particles: false
        }
    };
    
    // Cache de elementos DOM
    let els = {};
    
    function cacheDom() {
        els = {
            loadingScreen: document.getElementById('loading-screen'),
            loadingProgress: document.getElementById('loading-progress'),
            loadingStatus: document.getElementById('loading-status'),
            appContainer: document.getElementById('app'),
            sections: document.querySelectorAll('.section'),
            navItems: document.querySelectorAll('.nav-item'),
            counters: document.querySelectorAll('[data-count]'),
            toastContainer: document.getElementById('toast-container')
        };
    }
    
    // ========================================================================
    // Sistema de notificaciones
    // ========================================================================
    function showToast(message, type = 'info', duration = 3500) {
        if (!els.toastContainer) return;
        
        const icons = {
            info: 'ℹ️',
            success: '✅',
            warning: '⚠️',
            error: '❌'
        };
        
        const toast = document.createElement('div');
        toast.className = `toast ${type} animate__animated animate__fadeInUp`;
        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || '📢'}</span>
            <span class="toast-message">${message}</span>
        `;
        
        els.toastContainer.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.remove('animate__fadeInUp');
            toast.classList.add('animate__fadeOutDown');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
    
    // ========================================================================
    // Loader y transiciones
    // ========================================================================
    function updateLoadingProgress(percent, status) {
        if (els.loadingProgress) {
            els.loadingProgress.style.width = `${Math.min(100, percent)}%`;
        }
        if (els.loadingStatus && status) {
            els.loadingStatus.textContent = status;
        }
    }
    
    function hideLoader() {
        if (els.loadingScreen) {
            els.loadingScreen.classList.add('fade-out');
            setTimeout(() => {
                els.loadingScreen.style.display = 'none';
            }, 500);
        }
        
        if (els.appContainer) {
            els.appContainer.classList.remove('hidden');
            els.appContainer.style.display = 'grid';
            els.appContainer.classList.add('animate__animated', 'animate__fadeIn');
        }
    }
    
    async function runLoadingSequence() {
        const stages = [
            { percent: 10, status: 'Inicializando módulos...', delay: 100 },
            { percent: 25, status: 'Cargando datos de simulación...', delay: 150 },
            { percent: 40, status: 'Configurando modelo acústico Thorp...', delay: 120 },
            { percent: 55, status: 'Preparando visualizaciones interactivas...', delay: 140 },
            { percent: 70, status: 'Inicializando mapas y gráficos...', delay: 180 },
            { percent: 85, status: 'Cargando frente de Pareto...', delay: 130 },
            { percent: 95, status: 'Finalizando configuración...', delay: 100 },
            { percent: 100, status: '¡Sistema listo!', delay: 200 }
        ];
        
        for (const stage of stages) {
            updateLoadingProgress(stage.percent, stage.status);
            await new Promise(resolve => setTimeout(resolve, stage.delay));
        }
        
        // Pequeña pausa antes de ocultar
        await new Promise(resolve => setTimeout(resolve, 300));
        hideLoader();
        
        // Animar contadores después de mostrar la app
        setTimeout(animateCounters, 100);
    }
    
    // ========================================================================
    // Navegación SPA
    // ========================================================================
    function setActiveSection(sectionId) {
        if (!sectionId) return;
        
        state.currentSection = sectionId;
        
        els.sections.forEach(section => {
            if (section.id === sectionId) {
                section.classList.add('active');
                section.style.display = 'block';
            } else {
                section.classList.remove('active');
                section.style.display = 'none';
            }
        });
        
        els.navItems.forEach(item => {
            item.classList.toggle('active', item.dataset.section === sectionId);
        });
        
        // Acciones específicas por sección
        if (sectionId === 'topology' && window.UWSNMap) {
            setTimeout(() => window.UWSNMap.refreshMap(), 250);
        }
        
        if (sectionId === 'evolution' && window.UWSNEvolution) {
            window.UWSNEvolution.init();
        }
        
        // Reiniciar AOS para la nueva sección
        if (window.AOS) {
            window.AOS.refresh();
        }
    }
    
    function navigateTo(sectionId) {
        setActiveSection(sectionId);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    function bindNavigation() {
        els.navItems.forEach(item => {
            item.addEventListener('click', () => {
                navigateTo(item.dataset.section);
            });
        });
    }
    
    // ========================================================================
    // Animaciones de contadores
    // ========================================================================
    function animateCounters() {
        els.counters.forEach(el => {
            const target = parseInt(el.dataset.count, 10) || 0;
            let current = 0;
            const step = Math.max(1, Math.floor(target / 40));
            const duration = 1000;
            const stepTime = duration / (target / step);
            
            const timer = setInterval(() => {
                current += step;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                el.textContent = current;
            }, stepTime);
        });
    }
    
    // ========================================================================
    // Bindings de controles
    // ========================================================================
    function bindSliders() {
        const sliderConfigs = [
            { id: 'area-radius', suffix: ' km', multiplier: 1, decimals: 1 },
            { id: 'frequency', suffix: ' kHz', multiplier: 1, decimals: 0 },
            { id: 'mutation-rate', suffix: '%', multiplier: 100, decimals: 0 },
            { id: 'crossover-rate', suffix: '%', multiplier: 100, decimals: 0 }
        ];
        
        sliderConfigs.forEach(config => {
            const input = document.getElementById(config.id);
            if (!input) return;
            
            const valueEl = input.parentElement?.querySelector('.slider-value');
            if (!valueEl) return;
            
            const updateValue = () => {
                const val = (parseFloat(input.value) * config.multiplier).toFixed(config.decimals);
                valueEl.textContent = val + config.suffix;
                
                // Actualizar modelo Thorp si es frecuencia
                if (config.id === 'frequency') {
                    updateThorpDisplay(parseFloat(input.value));
                }
            };
            
            input.addEventListener('input', updateValue);
            updateValue();
        });
    }
    
    function updateThorpDisplay(frequency) {
        // Fórmula de Thorp
        const f2 = frequency * frequency;
        const alpha = (0.11 * f2 / (1 + f2)) + 
                      (44 * f2 / (4100 + f2)) + 
                      (2.75e-4 * f2) + 0.003;
        
        const attenuationEl = document.getElementById('attenuation-value');
        const rangeEl = document.getElementById('max-range-value');
        
        if (attenuationEl) {
            attenuationEl.textContent = alpha.toFixed(2);
        }
        
        if (rangeEl) {
            // Rango aproximado basado en SNR threshold
            const maxRange = Math.round(40 / alpha * 1000); // Aproximación
            rangeEl.textContent = maxRange.toLocaleString();
        }
    }
    
    function bindTabs() {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tabId = btn.dataset.tab;
                
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => {
                    c.classList.remove('active');
                    c.style.display = 'none';
                });
                
                btn.classList.add('active');
                const target = document.getElementById('tab-' + tabId);
                if (target) {
                    target.classList.add('active');
                    target.style.display = 'block';
                }
            });
        });
    }
    
    // ========================================================================
    // Inicialización de módulos
    // ========================================================================
    function initModules() {
        // Charts
        try {
            if (window.UWSNCharts?.initCharts) {
                window.UWSNCharts.initCharts();
                state.modulesReady.charts = true;
            }
        } catch (e) {
            console.error('Error inicializando charts:', e);
        }
        
        // Maps
        try {
            if (window.UWSNMap?.initMap) {
                window.UWSNMap.initMap();
                state.modulesReady.map = true;
            }
        } catch (e) {
            console.error('Error inicializando map:', e);
        }
        
        // Evolution
        try {
            if (window.UWSNEvolution?.init) {
                window.UWSNEvolution.init();
                state.modulesReady.evolution = true;
            }
        } catch (e) {
            console.error('Error inicializando evolution:', e);
        }
        
        // Particles
        try {
            if (window.UWSNParticles?.init) {
                window.UWSNParticles.init();
                state.modulesReady.particles = true;
            }
        } catch (e) {
            console.error('Error inicializando particles:', e);
        }
        
        // AOS
        try {
            if (window.AOS?.init) {
                window.AOS.init({
                    once: false,
                    duration: 700,
                    easing: 'ease-out-cubic',
                    offset: 50
                });
            }
        } catch (e) {
            console.error('Error inicializando AOS:', e);
        }
    }
    
    // ========================================================================
    // Funciones globales de la demo
    // ========================================================================
    function startEvolution() {
        navigateTo('evolution');
        setTimeout(() => {
            if (window.UWSNEvolution?.play) {
                window.UWSNEvolution.play();
                showToast('Simulación NSGA-II iniciada', 'success');
            }
        }, 500);
    }
    
    function downloadReport() {
        showToast('Generando informe PDF...', 'info');
        
        // Simular descarga
        setTimeout(() => {
            // En producción, esto generaría un PDF real
            showToast('Informe generado correctamente (demo)', 'success');
        }, 1500);
    }
    
    // ========================================================================
    // Inicialización principal
    // ========================================================================
    async function init() {
        console.log('🌊 UWSN Demo: Iniciando...');
        
        // Verificar datos
        if (!window.uwsnData) {
            console.error('❌ Error: Datos no disponibles (window.uwsnData)');
            const loadingStatus = document.getElementById('loading-status');
            if (loadingStatus) {
                loadingStatus.textContent = 'Error: No se pudieron cargar los datos';
                loadingStatus.style.color = '#ef4444';
            }
            return;
        }
        
        cacheDom();
        
        // Ejecutar secuencia de carga
        await runLoadingSequence();
        
        // Configurar bindings
        bindNavigation();
        bindSliders();
        bindTabs();
        
        // Inicializar módulos
        setTimeout(() => {
            initModules();
            setActiveSection('intro');
            state.initialized = true;
            console.log('✅ UWSN Demo: Inicialización completa');
            console.log('📊 Módulos:', state.modulesReady);
        }, 100);
    }
    
    // Exponer API global
    window.navigateTo = navigateTo;
    window.showToast = showToast;
    window.startEvolution = startEvolution;
    window.downloadReport = downloadReport;
    window.UWSNApp = {
        getState: () => state,
        navigateTo,
        showToast
    };
    
    // Ejecutar cuando DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Fallback de seguridad
    setTimeout(() => {
        if (!state.initialized) {
            console.warn('⚠️ Forzando inicialización después de timeout');
            hideLoader();
        }
    }, 6000);
    
})();
