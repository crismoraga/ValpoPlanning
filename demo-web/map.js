// ============================================================================
// UWSN Demo - Mapas Interactivos con Leaflet
// ============================================================================
(function() {
    'use strict';
    
    // Wait for data
    if (!window.uwsnData) {
        console.warn('Map: Datos no disponibles');
        return;
    }
    
    const { configuration, nodes, pois, thorp } = window.uwsnData;
    
    let topoMap = null;
    let miniMap = null;
    let layers = {};
    let animationLayers = {};
    let signalAnimationId = null;
    
    // POI type colors
    const POI_COLORS = {
        industrial_discharge: { color: '#ef4444', name: 'Descargas Industriales', icon: '🏭' },
        anchorage: { color: '#3b82f6', name: 'Zonas de Fondeo', icon: '⚓' },
        sensitive_areas: { color: '#22c55e', name: 'Áreas Sensibles', icon: '🌊' },
        bay_entrances: { color: '#f59e0b', name: 'Entradas Bahía', icon: '🚢' },
        critical_monitoring: { color: '#a855f7', name: 'Monitoreo Crítico', icon: '⚠️' }
    };
    
    // Custom icons
    const createSensorIcon = (index) => L.divIcon({
        className: 'custom-sensor-icon',
        html: `<div class="sensor-marker" style="animation-delay: ${index * 0.2}s">
            <div class="sensor-dot"></div>
            <div class="sensor-pulse"></div>
            <div class="sensor-label">SN${index + 1}</div>
        </div>`,
        iconSize: [40, 40],
        iconAnchor: [20, 20]
    });
    
    const createGatewayIcon = () => L.divIcon({
        className: 'custom-gateway-icon',
        html: `<div class="gateway-marker">
            <div class="gateway-body">📡</div>
            <div class="gateway-signal"></div>
            <div class="gateway-signal delay-1"></div>
            <div class="gateway-signal delay-2"></div>
        </div>`,
        iconSize: [50, 50],
        iconAnchor: [25, 25]
    });
    
    const createPOIIcon = (type) => {
        const info = POI_COLORS[type] || { color: '#00d1ff', icon: '📍' };
        return L.divIcon({
            className: 'custom-poi-icon',
            html: `<div class="poi-marker" style="--poi-color: ${info.color}">
                <span class="poi-emoji">${info.icon}</span>
            </div>`,
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });
    };
    
    function createBaseMap(elementId, zoom = 14, options = {}) {
        const container = document.getElementById(elementId);
        if (!container) return null;
        
        // Clear existing map
        if (container._leaflet_id) {
            container._leaflet_id = null;
            container.innerHTML = '';
        }
        
        const map = L.map(elementId, {
            zoomControl: true,
            scrollWheelZoom: true,
            attributionControl: false,
            ...options
        }).setView([configuration.center.lat, configuration.center.lon], zoom);
        
        // Dark ocean style tiles
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            maxZoom: 19,
            subdomains: 'abcd'
        }).addTo(map);
        
        // Add attribution
        L.control.attribution({
            prefix: '🌊 UWSN Demo | ',
            position: 'bottomright'
        }).addTo(map).addAttribution('© CartoDB | © OpenStreetMap');
        
        return map;
    }
    
    function buildMiniMap() {
        const container = document.getElementById('config-map');
        if (!container) return;
        
        miniMap = createBaseMap('config-map', 13);
        if (!miniMap) return;
        
        const radius = (configuration.area_radius_km || 1) * 1000;
        
        // Study area circle
        L.circle([configuration.center.lat, configuration.center.lon], {
            radius,
            color: '#00d1ff',
            weight: 2,
            fillColor: '#00d1ff',
            fillOpacity: 0.1,
            dashArray: '10, 5'
        }).addTo(miniMap);
        
        // Center marker
        L.marker([configuration.center.lat, configuration.center.lon], {
            icon: L.divIcon({
                className: 'center-marker',
                html: '<div class="center-point">📍</div>',
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            })
        }).bindPopup('<strong>Centro del Estudio</strong><br>Puerto de Valparaíso').addTo(miniMap);
    }
    
    function buildTopologyMap() {
        const container = document.getElementById('topology-map');
        if (!container) return;
        
        topoMap = createBaseMap('topology-map', 15);
        if (!topoMap) return;
        
        // Initialize layers
        layers = {
            sensors: L.layerGroup(),
            buoys: L.layerGroup(),
            pois: L.layerGroup(),
            links: L.layerGroup(),
            coverage: L.layerGroup(),
            acousticRange: L.layerGroup()
        };
        
        animationLayers = {
            signals: L.layerGroup()
        };
        
        // Add POIs
        if (pois && pois.length > 0) {
            pois.forEach((poi, index) => {
                const info = POI_COLORS[poi.type] || { color: '#00d1ff', name: 'POI', icon: '📍' };
                
                // POI marker
                const marker = L.marker([poi.lat, poi.lon], {
                    icon: createPOIIcon(poi.type)
                }).bindPopup(`
                    <div class="poi-popup">
                        <h4>${info.icon} ${poi.name}</h4>
                        <p><strong>Tipo:</strong> ${info.name}</p>
                        <p><strong>Prioridad:</strong> ${poi.priority}</p>
                        <p><strong>Radio Cobertura:</strong> ${poi.coverage_radius_m}m</p>
                        <p><strong>Coordenadas:</strong> ${poi.lat.toFixed(4)}°, ${poi.lon.toFixed(4)}°</p>
                    </div>
                `);
                marker.addTo(layers.pois);
                
                // Coverage circle
                L.circle([poi.lat, poi.lon], {
                    radius: poi.coverage_radius_m,
                    color: info.color,
                    weight: 1,
                    fillColor: info.color,
                    fillOpacity: 0.08,
                    className: 'coverage-circle'
                }).addTo(layers.coverage);
            });
        }
        
        // Add sensors
        if (nodes && nodes.sensor_nodes) {
            nodes.sensor_nodes.forEach((sn, index) => {
                const marker = L.marker([sn.lat, sn.lon], {
                    icon: createSensorIcon(index)
                }).bindPopup(`
                    <div class="sensor-popup">
                        <h4>📶 ${sn.id}</h4>
                        <p><strong>Profundidad:</strong> ${sn.depth_m.toFixed(1)} m</p>
                        <p><strong>Coordenadas:</strong> ${sn.lat.toFixed(4)}°, ${sn.lon.toFixed(4)}°</p>
                        <p><strong>Estado:</strong> <span class="status-active">Activo</span></p>
                    </div>
                `);
                marker.addTo(layers.sensors);
                
                // Sensor coverage
                L.circle([sn.lat, sn.lon], {
                    radius: 200,
                    color: '#22c55e',
                    weight: 1,
                    fillColor: '#22c55e',
                    fillOpacity: 0.05
                }).addTo(layers.coverage);
            });
        }
        
        // Add gateway buoys
        if (nodes && nodes.gateway_buoys) {
            nodes.gateway_buoys.forEach(bg => {
                const marker = L.marker([bg.lat, bg.lon], {
                    icon: createGatewayIcon()
                }).bindPopup(`
                    <div class="gateway-popup">
                        <h4>📡 ${bg.id}</h4>
                        <p><strong>Tipo:</strong> Boya Gateway</p>
                        <p><strong>Profundidad:</strong> Superficie (0m)</p>
                        <p><strong>Coordenadas:</strong> ${bg.lat.toFixed(4)}°, ${bg.lon.toFixed(4)}°</p>
                        <p><strong>Enlace:</strong> LoRaWAN / 4G</p>
                    </div>
                `);
                marker.addTo(layers.buoys);
                
                // Acoustic communication range
                const maxRange = thorp ? thorp.max_range_m : 5934;
                L.circle([bg.lat, bg.lon], {
                    radius: maxRange,
                    color: '#00d1ff',
                    weight: 2,
                    fillColor: '#00d1ff',
                    fillOpacity: 0.03,
                    dashArray: '5, 10'
                }).addTo(layers.acousticRange);
            });
        }
        
        // Build links between sensors and gateway
        if (nodes && nodes.sensor_nodes && nodes.gateway_buoys && nodes.gateway_buoys.length > 0) {
            const gateway = nodes.gateway_buoys[0];
            
            nodes.sensor_nodes.forEach((sn, i) => {
                // Link to gateway
                const latlngs = [[sn.lat, sn.lon], [gateway.lat, gateway.lon]];
                
                // Calculate distance
                const from = L.latLng(sn.lat, sn.lon);
                const to = L.latLng(gateway.lat, gateway.lon);
                const distance = from.distanceTo(to);
                
                const link = L.polyline(latlngs, {
                    color: '#00d1ff',
                    weight: 2,
                    opacity: 0.6,
                    className: 'acoustic-link'
                }).bindPopup(`
                    <div class="link-popup">
                        <h4>🔗 Enlace Acústico</h4>
                        <p><strong>De:</strong> ${sn.id}</p>
                        <p><strong>A:</strong> ${gateway.id}</p>
                        <p><strong>Distancia:</strong> ${distance.toFixed(0)} m</p>
                        <p><strong>Tipo:</strong> Acústico 20 kHz</p>
                    </div>
                `);
                link.addTo(layers.links);
                
                // Also add mesh links between nearby sensors
                nodes.sensor_nodes.forEach((other, j) => {
                    if (j > i) {
                        const fromSensor = L.latLng(sn.lat, sn.lon);
                        const toSensor = L.latLng(other.lat, other.lon);
                        const meshDistance = fromSensor.distanceTo(toSensor);
                        
                        if (meshDistance < 1500) { // Within mesh range
                            const meshLink = L.polyline([[sn.lat, sn.lon], [other.lat, other.lon]], {
                                color: '#22c55e',
                                weight: 1,
                                opacity: 0.3,
                                dashArray: '3, 6'
                            });
                            meshLink.addTo(layers.links);
                        }
                    }
                });
            });
        }
        
        // Add all layers to map
        Object.values(layers).forEach(layer => layer.addTo(topoMap));
        
        // Populate sidebar lists
        populateNodesList();
        populatePOIsList();
    }
    
    function populateNodesList() {
        const container = document.getElementById('nodes-list');
        if (!container || !nodes) return;
        
        let html = '';
        
        // Gateway buoys
        if (nodes.gateway_buoys) {
            nodes.gateway_buoys.forEach(bg => {
                html += `
                    <div class="node-item gateway" onclick="UWSNMap.focusNode(${bg.lat}, ${bg.lon})">
                        <span class="node-icon">📡</span>
                        <div class="node-info">
                            <span class="node-name">${bg.id}</span>
                            <span class="node-type">Gateway | Superficie</span>
                        </div>
                        <span class="node-status active"></span>
                    </div>
                `;
            });
        }
        
        // Sensor nodes
        if (nodes.sensor_nodes) {
            nodes.sensor_nodes.forEach(sn => {
                html += `
                    <div class="node-item sensor" onclick="UWSNMap.focusNode(${sn.lat}, ${sn.lon})">
                        <span class="node-icon">📶</span>
                        <div class="node-info">
                            <span class="node-name">${sn.id}</span>
                            <span class="node-type">Sensor | ${sn.depth_m.toFixed(1)}m</span>
                        </div>
                        <span class="node-status active"></span>
                    </div>
                `;
            });
        }
        
        container.innerHTML = html;
    }
    
    function populatePOIsList() {
        const container = document.getElementById('pois-list');
        if (!container || !pois) return;
        
        // Group by type
        const grouped = {};
        pois.forEach(poi => {
            if (!grouped[poi.type]) grouped[poi.type] = [];
            grouped[poi.type].push(poi);
        });
        
        let html = '';
        Object.entries(grouped).forEach(([type, items]) => {
            const info = POI_COLORS[type] || { name: type, icon: '📍', color: '#00d1ff' };
            html += `<div class="poi-group">
                <div class="poi-group-header" style="--color: ${info.color}">
                    <span>${info.icon} ${info.name} (${items.length})</span>
                </div>
                <div class="poi-group-items">`;
            
            items.forEach(poi => {
                html += `
                    <div class="poi-item" onclick="UWSNMap.focusNode(${poi.lat}, ${poi.lon})">
                        <span class="poi-name">${poi.name}</span>
                        <span class="poi-priority">${poi.priority}</span>
                    </div>
                `;
            });
            
            html += '</div></div>';
        });
        
        container.innerHTML = html;
    }
    
    function toggleLayer(layerKey) {
        if (!topoMap || !layers[layerKey]) return false;
        
        const isActive = topoMap.hasLayer(layers[layerKey]);
        if (isActive) {
            topoMap.removeLayer(layers[layerKey]);
        } else {
            layers[layerKey].addTo(topoMap);
        }
        return !isActive;
    }
    
    function attachToggles() {
        const mapBtns = [
            { id: 'toggle-sensors', key: 'sensors' },
            { id: 'toggle-buoys', key: 'buoys' },
            { id: 'toggle-pois', key: 'pois' },
            { id: 'toggle-links', key: 'links' },
            { id: 'toggle-coverage', key: 'coverage' }
        ];
        
        mapBtns.forEach(({ id, key }) => {
            const btn = document.getElementById(id);
            if (!btn) return;
            
            btn.classList.add('active');
            btn.addEventListener('click', () => {
                const nowActive = toggleLayer(key);
                btn.classList.toggle('active', nowActive);
            });
        });
        
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                btn.classList.add('active');
                const content = document.getElementById('tab-' + tab);
                if (content) content.classList.add('active');
            });
        });
    }
    
    function focusNode(lat, lon) {
        if (!topoMap) return;
        topoMap.setView([lat, lon], 17, { animate: true });
    }
    
    function refreshMap() {
        if (topoMap) topoMap.invalidateSize();
        if (miniMap) miniMap.invalidateSize();
    }
    
    function initMap() {
        try {
            buildMiniMap();
            buildTopologyMap();
            attachToggles();
            
            // Refresh after a delay for proper sizing
            setTimeout(refreshMap, 300);
            setTimeout(refreshMap, 1000);
            
            console.log('✅ Map module initialized');
        } catch (error) {
            console.error('Error initializing maps:', error);
        }
    }
    
    // Expose API
    window.UWSNMap = {
        initMap,
        refreshMap,
        focusNode,
        toggleLayer,
        getMap: () => topoMap
    };
    
})();
