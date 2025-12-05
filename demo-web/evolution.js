// ============================================================================
// UWSN Demo - Simulación Interactiva de Evolución NSGA-II
// ============================================================================
(function() {
    'use strict';
    
    // Wait for data to be available
    if (!window.uwsnData || !window.uwsnData.snapshots) {
        console.warn('Evolution: Datos no disponibles aún');
        return;
    }
    
    const { snapshots, solutionBalanced, paretoFront } = window.uwsnData;
    
    // State
    let currentIndex = 0;
    let isPlaying = false;
    let timer = null;
    let speed = 5; // 1-10
    let isInitialized = false;
    
    // Constants
    const CIRCUMFERENCE = 2 * Math.PI * 54;
    
    // DOM Element cache
    let els = {};
    
    function cacheElements() {
        els = {
            // Controls
            playBtn: document.getElementById('btn-evo-play'),
            pauseBtn: document.getElementById('btn-evo-pause'),
            backBtn: document.getElementById('btn-evo-step-back'),
            fwdBtn: document.getElementById('btn-evo-step-fwd'),
            slider: document.getElementById('evo-slider'),
            speedInput: document.getElementById('evo-speed'),
            
            // Stats
            genDisplay: document.getElementById('evo-generation'),
            costDisplay: document.getElementById('evo-best-cost'),
            covDisplay: document.getElementById('evo-best-coverage'),
            paretoSizeDisplay: document.getElementById('evo-pareto-size'),
            percentDisplay: document.getElementById('evolution-percent'),
            ring: document.getElementById('evolution-ring'),
            
            // Additional
            log: document.getElementById('evolution-log'),
            snapshotsTimeline: document.getElementById('snapshots-timeline'),
            btnSeeResults: document.getElementById('btn-see-results'),
            currentGenLabel: document.getElementById('current-gen')
        };
    }
    
    // Logging helper
    function addLogEntry(message, type = 'info') {
        if (!els.log) return;
        
        const now = new Date();
        const time = now.toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        
        const icons = {
            info: 'ℹ️',
            success: '✅',
            warning: '⚠️',
            evolution: '🧬',
            pareto: '📊'
        };
        
        const entry = document.createElement('div');
        entry.className = `log-entry log-${type} animate__animated animate__fadeIn`;
        entry.innerHTML = `
            <span class="log-icon">${icons[type] || '📝'}</span>
            <span class="log-time">${time}</span>
            <span class="log-msg">${message}</span>
        `;
        
        els.log.insertBefore(entry, els.log.firstChild);
        
        // Keep only last 50 entries
        while (els.log.children.length > 50) {
            els.log.removeChild(els.log.lastChild);
        }
    }
    
    function updateStats(snap) {
        if (!snap) return;
        
        // Update text displays
        if (els.genDisplay) els.genDisplay.textContent = snap.gen;
        if (els.costDisplay) els.costDisplay.textContent = snap.best_cost.toLocaleString();
        if (els.covDisplay) els.covDisplay.textContent = snap.best_coverage + '%';
        if (els.paretoSizeDisplay) els.paretoSizeDisplay.textContent = snap.pareto.length;
        if (els.currentGenLabel) els.currentGenLabel.textContent = snap.gen;
        
        // Calculate percentage
        const pct = snapshots.length > 1 
            ? Math.round((currentIndex / (snapshots.length - 1)) * 100) 
            : 0;
        
        if (els.percentDisplay) els.percentDisplay.textContent = pct + '%';
        
        // Update progress ring
        if (els.ring) {
            const offset = CIRCUMFERENCE - (pct / 100) * CIRCUMFERENCE;
            els.ring.style.strokeDashoffset = offset;
            els.ring.style.transition = 'stroke-dashoffset 0.3s ease';
        }
    }
    
    function updateParetoChart(snap) {
        const chart = window.UWSNCharts?.charts?.['pareto-chart'];
        if (!chart || !snap) return;
        
        // Prepare data
        const popData = snap.population.map(p => ({ x: p[0], y: p[1] }));
        const paretoData = snap.pareto.map(p => ({ x: p[0], y: p[1] })).sort((a, b) => a.x - b.x);
        const bestData = [{ x: snap.best_cost, y: snap.best_coverage }];
        
        // Create gradient effect
        chart.data.datasets = [
            {
                label: 'Población (Gen ' + snap.gen + ')',
                data: popData,
                backgroundColor: 'rgba(255, 255, 255, 0.15)',
                borderColor: 'rgba(255, 255, 255, 0.3)',
                pointRadius: 3,
                pointHoverRadius: 5,
                showLine: false
            },
            {
                label: 'Frente de Pareto',
                data: paretoData,
                borderColor: '#00d1ff',
                backgroundColor: 'rgba(0, 209, 255, 0.25)',
                borderWidth: 2,
                showLine: true,
                tension: 0.2,
                pointRadius: 5,
                pointHoverRadius: 8,
                pointBackgroundColor: '#00d1ff',
                fill: false
            },
            {
                label: 'Mejor Solución',
                data: bestData,
                backgroundColor: '#f59e0b',
                borderColor: '#ffffff',
                borderWidth: 2,
                pointRadius: 10,
                pointHoverRadius: 14,
                pointStyle: 'star'
            }
        ];
        
        chart.update('none');
    }
    
    function updateConvergenceChart(snap) {
        const chart = window.UWSNCharts?.charts?.['convergence-chart'];
        if (!chart) return;
        
        // Build data up to current snapshot
        const gens = [];
        const costs = [];
        const coverages = [];
        const paretoSizes = [];
        
        for (let i = 0; i <= currentIndex; i++) {
            const s = snapshots[i];
            gens.push(s.gen);
            costs.push(s.best_cost);
            coverages.push(s.best_coverage);
            paretoSizes.push(s.pareto.length);
        }
        
        chart.data.labels = gens;
        chart.data.datasets[0].data = costs;
        chart.data.datasets[1].data = coverages;
        
        chart.update('none');
    }
    
    function updateTimeline() {
        if (!els.snapshotsTimeline || !snapshots) return;
        
        // Create timeline markers if not exists
        if (els.snapshotsTimeline.children.length === 0) {
            // Create key snapshots (every 10th or significant ones)
            const keyIndices = [];
            for (let i = 0; i < snapshots.length; i++) {
                if (i === 0 || i === snapshots.length - 1 || i % 10 === 0) {
                    keyIndices.push(i);
                }
            }
            
            keyIndices.forEach(idx => {
                const snap = snapshots[idx];
                const marker = document.createElement('div');
                marker.className = 'snapshot-marker';
                marker.dataset.index = idx;
                marker.innerHTML = `
                    <div class="marker-dot"></div>
                    <div class="marker-label">Gen ${snap.gen}</div>
                    <div class="marker-info">${snap.best_coverage}%</div>
                `;
                marker.addEventListener('click', () => {
                    pause();
                    setIndex(idx);
                });
                els.snapshotsTimeline.appendChild(marker);
            });
        }
        
        // Update active state
        els.snapshotsTimeline.querySelectorAll('.snapshot-marker').forEach(m => {
            const idx = parseInt(m.dataset.index);
            m.classList.toggle('active', idx === currentIndex);
            m.classList.toggle('passed', idx < currentIndex);
        });
    }
    
    function setIndex(index) {
        if (!snapshots || snapshots.length === 0) return;
        
        index = Math.max(0, Math.min(index, snapshots.length - 1));
        
        const prevIndex = currentIndex;
        currentIndex = index;
        
        if (els.slider) els.slider.value = index;
        
        const snap = snapshots[currentIndex];
        
        updateStats(snap);
        updateParetoChart(snap);
        updateConvergenceChart(snap);
        updateTimeline();
        
        // Log significant events
        if (currentIndex > prevIndex) {
            if (currentIndex % 10 === 0 || currentIndex === snapshots.length - 1) {
                addLogEntry(`Generación ${snap.gen}: Mejor costo ${snap.best_cost.toLocaleString()}, Cobertura ${snap.best_coverage}%`, 'evolution');
            }
            
            // Check for Pareto improvement
            if (prevIndex >= 0 && snapshots[prevIndex].pareto.length < snap.pareto.length) {
                addLogEntry(`Frente Pareto expandido a ${snap.pareto.length} soluciones`, 'pareto');
            }
        }
        
        // Enable results button when complete
        if (currentIndex === snapshots.length - 1) {
            if (els.btnSeeResults) {
                els.btnSeeResults.disabled = false;
                els.btnSeeResults.classList.add('animate__animated', 'animate__pulse');
            }
            addLogEntry('✨ Optimización completada. Solución óptima encontrada.', 'success');
        }
        
        // Auto-pause at end
        if (currentIndex === snapshots.length - 1 && isPlaying) {
            pause();
        }
    }
    
    function play() {
        if (isPlaying || !snapshots) return;
        
        isPlaying = true;
        
        if (els.playBtn) {
            els.playBtn.classList.add('active');
            els.playBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        }
        if (els.pauseBtn) els.pauseBtn.classList.remove('active');
        
        // Reset if at end
        if (currentIndex >= snapshots.length - 1) {
            currentIndex = 0;
            addLogEntry('🔄 Reiniciando simulación...', 'info');
        }
        
        addLogEntry('▶️ Simulación iniciada', 'info');
        
        const getInterval = () => Math.max(30, 800 - (speed * 70));
        
        const step = () => {
            if (!isPlaying) return;
            
            setIndex(currentIndex + 1);
            
            if (currentIndex < snapshots.length - 1) {
                timer = setTimeout(step, getInterval());
            }
        };
        
        timer = setTimeout(step, getInterval());
    }
    
    function pause() {
        if (!isPlaying) return;
        
        isPlaying = false;
        
        if (els.playBtn) {
            els.playBtn.classList.remove('active');
            els.playBtn.innerHTML = '<i class="fas fa-play"></i>';
        }
        if (els.pauseBtn) els.pauseBtn.classList.add('active');
        
        if (timer) {
            clearTimeout(timer);
            timer = null;
        }
        
        addLogEntry('⏸️ Simulación pausada en generación ' + snapshots[currentIndex].gen, 'info');
    }
    
    function reset() {
        pause();
        setIndex(0);
        addLogEntry('🔄 Simulación reiniciada', 'info');
    }
    
    function skipToEnd() {
        pause();
        setIndex(snapshots.length - 1);
        addLogEntry('⏭️ Saltado al final de la optimización', 'info');
    }
    
    function initEvolution() {
        if (isInitialized) return;
        if (!snapshots || snapshots.length === 0) {
            console.warn('Evolution: No hay snapshots disponibles');
            return;
        }
        
        cacheElements();
        
        // Setup slider
        if (els.slider) {
            els.slider.max = snapshots.length - 1;
            els.slider.value = 0;
            els.slider.addEventListener('input', (e) => {
                pause();
                setIndex(parseInt(e.target.value));
            });
        }
        
        // Bind control buttons
        if (els.playBtn) {
            els.playBtn.addEventListener('click', () => {
                if (isPlaying) pause();
                else play();
            });
        }
        
        if (els.pauseBtn) {
            els.pauseBtn.addEventListener('click', pause);
        }
        
        if (els.backBtn) {
            els.backBtn.addEventListener('click', () => {
                pause();
                setIndex(currentIndex - 1);
            });
        }
        
        if (els.fwdBtn) {
            els.fwdBtn.addEventListener('click', () => {
                pause();
                setIndex(currentIndex + 1);
            });
        }
        
        if (els.speedInput) {
            els.speedInput.addEventListener('input', (e) => {
                speed = parseInt(e.target.value);
            });
        }
        
        // Initialize to first snapshot
        setIndex(0);
        updateTimeline();
        
        addLogEntry(`Sistema inicializado. ${snapshots.length} snapshots disponibles.`, 'success');
        addLogEntry(`Población: 160 | Generaciones: 320 | Mutación: 22% | Crossover: 88%`, 'info');
        
        isInitialized = true;
        
        console.log('✅ Evolution module initialized with', snapshots.length, 'snapshots');
    }
    
    // Expose API
    window.UWSNEvolution = {
        init: initEvolution,
        play: play,
        pause: pause,
        reset: reset,
        skipToEnd: skipToEnd,
        setIndex: setIndex,
        getState: () => ({ currentIndex, isPlaying, total: snapshots?.length || 0 })
    };
    
    // Auto-init when DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initEvolution);
    } else {
        // Delay to ensure charts are ready
        setTimeout(initEvolution, 500);
    }
    
})();
