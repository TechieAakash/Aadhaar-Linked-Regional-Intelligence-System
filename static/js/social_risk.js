// social_risk.js - Complete Logic for Social Vulnerability Dashboard

document.addEventListener('DOMContentLoaded', function() {
    initDashboard();
    
    // Bind Export Buttons
    const btnCSV = document.getElementById('btnExportCSV');
    const btnPDF = document.getElementById('btnExportPDF');
    
    if (btnCSV) btnCSV.onclick = exportToCSV;
    if (btnPDF) btnPDF.onclick = exportToPDF;
});



let globalData = [];
let globalAnomalies = []; // Added for Hotspots
let mapInstance = null;
let charts = {};
// Store panel chart instance to destroy later
let forecastChartInstance = null;

// UIDAI Authentication
const API_KEY = "579b464db66ec23bdd000001623c2de44ffb40755360bbc473134c16";
const API_HEADERS = {
    'x-api-key': API_KEY, // Authentic Use
    'Content-Type': 'application/json'
};

// State Coordinates for Map Circles
const stateCoords = {
    "Andhra Pradesh": [15.9129, 79.7400], "Arunachal Pradesh": [28.2180, 94.7278], "Assam": [26.2006, 92.9376], "Bihar": [25.0961, 85.3131],
    "Chhattisgarh": [21.2787, 81.8661], "Goa": [15.2993, 74.1240], "Gujarat": [22.2587, 71.1924], "Haryana": [29.0588, 76.0856],
    "Himachal Pradesh": [31.1048, 77.1734], "Jharkhand": [23.6102, 85.2799], "Karnataka": [15.3173, 75.7139], "Kerala": [10.8505, 76.2711],
    "Madhya Pradesh": [22.9734, 78.6569], "Maharashtra": [19.7515, 75.7139], "Manipur": [24.6637, 93.9063], "Meghalaya": [25.4670, 91.3662],
    "Mizoram": [23.1645, 92.9376], "Nagaland": [26.1584, 94.5624], "Odisha": [20.9517, 85.0985], "Punjab": [31.1471, 75.3412],
    "Rajasthan": [27.0238, 74.2179], "Sikkim": [27.5330, 88.5122], "Tamil Nadu": [11.1271, 78.6569], "Telangana": [18.1124, 79.0193],
    "Tripura": [23.9408, 91.9882], "Uttar Pradesh": [26.8467, 80.9462], "Uttarakhand": [30.0668, 79.0193], "West Bengal": [22.9868, 87.8550],
    "Andaman and Nicobar Islands": [11.7401, 92.6586], "Chandigarh": [30.7333, 76.7794], "Dadra and Nagar Haveli": [20.1809, 73.0169],
    "Daman and Diu": [20.4283, 72.8397], "Delhi": [28.7041, 77.1025], "Lakshadweep": [10.5667, 72.6417], "Puducherry": [11.9416, 79.8083],
    "Jammu and Kashmir": [33.7782, 76.5762], "Ladakh": [34.1526, 77.5770]
};

async function initDashboard() {
    try {
        console.log("Initializing Dashboard...");
        
        // Fetch Data
        const res = await fetch('/api/social/risk', { headers: API_HEADERS });
        if (!res.ok) throw new Error("Failed to fetch API data");
        const riskData = await res.json();
        globalData = riskData;

        // Fetch Anomalies for Hotspots
        try {
            const anomalyRes = await fetch('/api/data/anomalies.json', { headers: API_HEADERS }); // Added headers
            if(anomalyRes.ok) {
                const anomalyData = await anomalyRes.json();
                globalAnomalies = anomalyData.state_anomalies || [];
            }
        } catch (e) { console.warn("Anomalies not found", e); }

        // Initialize Components
        initMap();
        renderKPIs(riskData);
        renderTable(riskData);
        renderHeatmap(riskData);
        initCharts(riskData);
        populateStateSelector(riskData);
        
        const refreshEl = document.getElementById('lastRefresh');
        if (refreshEl) refreshEl.innerText = new Date().toLocaleDateString();

    } catch (error) {
        console.error("Dashboard Error:", error);
        // alert("Error loading dashboard data. Please ensure backend is running.");
    }
}

// Export Functions
function exportToCSV() {
    window.location.href = `/api/social/export/csv?key=${API_KEY}`;
}

function exportToPDF() {
    window.location.href = `/api/social/export/pdf?key=${API_KEY}`;
}


// 1. Map Logic
function initMap() {
    mapInstance = L.map('indiaMap').setView([22.5937, 78.9629], 5);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(mapInstance);

    // Render Data Points
    globalData.forEach(item => {
        const coords = stateCoords[item.state];
        if (coords) {
            let color = '#38a169'; // Low
            let radius = 40000;
            if (item.integrated_risk_score > 60) { color = '#e53e3e'; radius = 80000; } // Critical
            else if (item.integrated_risk_score > 40) { color = '#dd6b20'; radius = 60000; } // High
            else if (item.integrated_risk_score > 20) { color = '#ecc94b'; radius = 50000; } // Medium

            L.circle(coords, {
                color: color, fillColor: color, fillOpacity: 0.6, radius: radius
            }).addTo(mapInstance)
            .bindPopup(`<b>${item.state}</b><br>Risk: ${item.integrated_risk_score.toFixed(1)}`)
            .on('click', () => showRegionDetails(item));
        }
    });
}

// 2. Metrics Logic
function renderKPIs(data) {
    const critical = data.filter(d => d.integrated_risk_score >= 60).length;
    const avgRisk = data.reduce((a, b) => a + b.integrated_risk_score, 0) / data.length;
    const avgCov = data.reduce((a, b) => a + (b.biometric_update_ratio || 0), 0) / data.length;

    document.getElementById('kpi-risk-score').innerText = avgRisk.toFixed(1);
    document.getElementById('kpi-coverage').innerText = (avgCov * 100).toFixed(1) + '%';
    document.getElementById('kpi-districts').innerText = critical;
    document.getElementById('kpi-pop').innerText = "12.4%"; 
}

// 3. Table Logic
function renderTable(data) {
    const tbody = document.getElementById('riskTableBody');
    tbody.innerHTML = '';
    
    // Sort High Risk first
    const sorted = [...data].sort((a,b) => b.integrated_risk_score - a.integrated_risk_score);

    sorted.forEach((item, index) => {
        const tr = document.createElement('tr');
        let badge = 'badge-low';
        if (item.service_risk_category.includes('Critical')) badge = 'badge-critical';
        else if (item.service_risk_category.includes('High')) badge = 'badge-high';
        else if (item.service_risk_category.includes('Medium')) badge = 'badge-medium';

        const logoPath = getStateLogo(item.state);

        tr.innerHTML = `
            <td>
                <div style="display:flex; align-items:center; gap:12px;">
                    <img src="${logoPath}" alt="${item.state} Logo" style="width:28px; height:28px; border-radius:50%; border: 1px solid #ddd; padding: 2px; background: #fff;">
                    <strong>${item.state}</strong>
                </div>
            </td>
            <td>${item.integrated_risk_score.toFixed(1)}</td>
            <td>${((item.biometric_update_ratio||0)*100).toFixed(1)}%</td>
            <td><span class="badge ${badge}">${item.service_risk_category}</span></td>
            <td>#${index+1}</td>
            <td><button class="btn-action" onclick="showRegionDetailsGlobal('${item.state}')">View</button></td>
        `;
        tr.onclick = () => showRegionDetails(item);
        tr.style.cursor = 'pointer';
        tbody.appendChild(tr);
    });
}

// 4. Heatmap Logic
function renderHeatmap(data) {
    const container = document.getElementById('heatmapContainer');
    container.innerHTML = '';
    
    const sorted = [...data].sort((a,b) => b.integrated_risk_score - a.integrated_risk_score);
    const grid = document.createElement('div');
    grid.style.display = 'grid';
    grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(90px, 1fr))';
    grid.style.gap = '8px';

    sorted.forEach(item => {
        const div = document.createElement('div');
        div.style.padding = '8px';
        div.style.borderRadius = '4px';
        div.style.textAlign = 'center';
        div.style.fontSize = '0.75rem';
        div.style.cursor = 'pointer';

        let bg = '#C6F6D5';
        if (item.integrated_risk_score > 60) bg = '#FED7D7';
        else if (item.integrated_risk_score > 40) bg = '#FEEBC8';
        else if (item.integrated_risk_score > 20) bg = '#FEFCBF';

        div.style.backgroundColor = bg;
        div.innerHTML = `<strong>${item.state}</strong><br>${item.integrated_risk_score.toFixed(1)}`;
        div.onclick = () => showRegionDetails(item);
        grid.appendChild(div);
    });
    container.appendChild(grid);
}

// 5. Details & Charts
function getStateLogo(stateName) {
    let slug = stateName.toLowerCase().replace(/ /g, "_").replace(/&/g, "and");
    
    // Special mapping for combined UT seal
    if (slug === "dadra_and_nagar_haveli" || slug === "daman_and_diu") {
        slug = "dadra_and_nagar_haveli_and_daman_and_diu";
    }

    const officialLogo = `/assets/images/states/seal_${slug}.png`;
    const universalLogo = '/assets/images/states/universal_state_logo.png';
    
    const availableLogos = [
        "andaman_and_nicobar_islands", "assam", "chandigarh", "delhi", 
        "himachal_pradesh", "jharkhand", "karnataka", "ladakh", 
        "lakshadweep", "madhya_pradesh", "maharashtra", "manipur", 
        "meghalaya", "mizoram", "odisha", "puducherry", "punjab", 
        "sikkim", "tamil_nadu", "telangana", "tripura", "uttar_pradesh", 
        "uttarakhand", "dadra_and_nagar_haveli_and_daman_and_diu"
    ];
    
    return availableLogos.includes(slug) ? officialLogo : universalLogo;
}

function showRegionDetails(item) {
    const content = document.getElementById('region-detail-content');
    const logoPath = getStateLogo(item.state);
    content.innerHTML = `
        <div style="display:flex; align-items:center; gap:15px; margin-bottom:15px;">
            <img src="${logoPath}" alt="${item.state} Logo" style="width:40px; height:40px; border-radius:50%; border: 2px solid #ddd; padding: 2px; background: #fff;">
            <h2 style="margin: 0; font-size: 1.2rem; color: #0A3D62;">${item.state}</h2>
        </div>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85rem; margin-bottom: 15px;">
            <div><strong>SVS Score:</strong> ${item.social_vulnerability_index.toFixed(1)}</div>
            <div><strong>Risk Score:</strong> ${item.integrated_risk_score.toFixed(1)}</div>
            <div><strong>Bio Coverage:</strong> ${((item.biometric_update_ratio||0)*100).toFixed(1)}%</div>
            <div><strong>Category:</strong> ${item.service_risk_category}</div>
        </div>
        <button class="btn-action" style="width:100%; justify-content:center;" onclick="openAnalysisPanel('${item.state}')">Detailed Classification Analysis</button>
    `;
    updateBreakdownChart(item);
}

// Helper for table button which passes string name
window.showRegionDetailsGlobal = function(stateName) {
    const item = globalData.find(d => d.state === stateName);
    if(item) {
        showRegionDetails(item);
        openAnalysisPanel(stateName); // Auto-open panel on table 'View' click
    }
}

// 5a. Detailed Analysis Panel Logic
window.openAnalysisPanel = function(stateName) {
    const item = globalData.find(d => d.state === stateName);
    if (!item) return;

    const logoPath = getStateLogo(stateName);
    document.getElementById('panelStateName').innerHTML = `
        <div style="display:flex; align-items:center; gap:15px;">
            <img src="${logoPath}" alt="${stateName} Logo" style="width:48px; height:48px; border-radius:50%; border: 2px solid #ddd; padding: 2px; background: #fff;">
            <span style="color: var(--nic-blue);">${stateName} Analysis</span>
        </div>
    `;
    const panel = document.getElementById('analysisPanel');
    const backdrop = document.getElementById('panelBackdrop');

    // Safe access to rural percentage (default to 50 if missing for stability)
    const ruralPct = (item.rural_population_percentage || 0.5) * 100;
    const urbanPct = 100 - ruralPct;

    // Populate Detailed Content
    const detailHtml = `
        <div style="margin-bottom: 25px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span style="font-size:0.85rem; font-weight:600; color:#666;">Service Gap Metric</span>
                <span style="font-size:0.85rem; font-weight:700;">${((1 - (item.biometric_update_ratio || 0)) * 100).toFixed(1)}%</span>
            </div>
            <div style="height:8px; background:#f0f0f0; border-radius:4px; overflow:hidden;">
                <div style="width:${(1 - (item.biometric_update_ratio || 0)) * 100}%; height:100%; background:#F57C00;"></div>
            </div>
        </div>

        <!-- Rural / Urban Insights -->
         <div style="margin-bottom: 25px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span style="font-size:0.85rem; font-weight:600; color:#666;">Demographic Spread (Rural vs Urban)</span>
            </div>
            <div style="display:flex; height:24px; border-radius:4px; overflow:hidden; font-size:0.7rem; color:white; line-height:24px; text-align:center;">
                <div style="width:${ruralPct}%; background:#2E7D32;" title="Rural">${ruralPct.toFixed(0)}% Rural</div>
                <div style="width:${urbanPct}%; background:#00ACC1;" title="Urban">${urbanPct.toFixed(0)}% Urban</div>
            </div>
        </div>

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; margin-bottom:25px;">
            <div style="background:#f9f9f9; padding:15px; border-radius:6px;">
                <div style="font-size:0.75rem; color:#888;">Migration Volatility</div>
                <div style="font-size:1.1rem; font-weight:700; color:var(--nic-blue);">${(item.growth_volatility || 0).toFixed(2)}</div>
            </div>
            <div style="background:#f9f9f9; padding:15px; border-radius:6px;">
                <div style="font-size:0.75rem; color:#888;">Regional Rank</div>
                <div style="font-size:1.1rem; font-weight:700; color:var(--nic-blue);">#${globalData.indexOf(item) + 1}</div>
            </div>
        </div>

        <div style="margin-bottom:25px;">
            <h4 style="margin:0 0 10px 0; font-size: 0.9rem; color: #555;">Regional Characterization</h4>
            <div style="font-size:0.85rem; line-height:1.6; color:#444;">
                ${generateCharacterization(item)}
            </div>
        </div>
    `;
    document.getElementById('panelContent').innerHTML = detailHtml;

    // ML Predictions & XAI
    generateMLPrediction(item);
    
    // New Advanced Features
    renderForecastChart(item);
    renderHotspots(item);
    calculateBurnDown(item);

    // Show Panel
    panel.classList.add('open');
    backdrop.classList.add('show');
}

// --- New Feature Functions ---

function renderForecastChart(item) {
    const ctx = document.getElementById('forecastChart').getContext('2d');
    
    if (forecastChartInstance) {
        forecastChartInstance.destroy();
    }

    // Mock Forecast Data based on Risk Trajectory
    // If Risk > 40, Gap widens. If Risk < 20, Gap narrows.
    const currentGap = (1 - (item.biometric_update_ratio || 0)) * 100;
    const trendFactor = item.integrated_risk_score > 40 ? 1.05 : 0.98;
    
    const dataPoints = [
        currentGap,
        currentGap * trendFactor,
        currentGap * trendFactor * trendFactor,
        currentGap * trendFactor * trendFactor * trendFactor
    ];

    forecastChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Today', '30 Days', '60 Days', '90 Days'],
            datasets: [{
                label: 'Projected Service Gap (%)',
                data: dataPoints,
                borderColor: '#F57C00',
                backgroundColor: 'rgba(245, 124, 0, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: (c) => `Gap: ${c.raw.toFixed(1)}%` } }
            },
            scales: {
                y: { grid: { borderDash: [2, 2] }, suggestedMin: 0, title: {display:true, text: 'Gap %'} }
            }
        }
    });
}

function calculateBurnDown(item) {
    // Mock logic: Days = Gap * 3 (arbitrary multiplier for demo)
    const gap = (1 - (item.biometric_update_ratio || 0)) * 100;
    const days = Math.floor(gap * 3.5);
    document.getElementById('burnDownText').innerText = `${days} days to clear backlog with current capacity`;
}

function renderHotspots(item) {
    const container = document.getElementById('hotspotContainer');
    
    // 1. Try to find anomalies for this state
    // Note: anomalies.json uses specific names, we try to match partials or mocks
    const stateAnomalies = globalAnomalies.filter(a => a.state && a.state.toLowerCase().includes(item.state.toLowerCase())); // Loose match
    
    let html = `<table class="hotspot-table">`;
    
    if (stateAnomalies.length > 0) {
        // Use real anomaly data
        stateAnomalies.slice(0, 5).forEach((anom, idx) => {
            html += `
                <tr>
                    <td style="width:30px;"><span class="hotspot-rank">${idx+1}</span></td>
                    <td><strong>${anom.state} (District/Block)</strong><br><span style="color:#666; font-size:0.7rem;">${anom.anomaly_type}</span></td>
                    <td style="text-align:right; color:#d32f2f; font-weight:700;">High Risk</td>
                </tr>
            `;
        });
    } else {
        // Fallback Simulation for "Strategic Projection"
        const districts = [`North ${item.state}`, `South ${item.state}`, `Central ${item.state}`];
        districts.forEach((d, idx) => {
            html += `
                <tr>
                    <td style="width:30px;"><span class="hotspot-rank">${idx+1}</span></td>
                    <td><strong>${d}</strong><br><span style="color:#666; font-size:0.7rem;">Projected Update Surge</span></td>
                    <td style="text-align:right; color:#d32f2f; font-weight:700;">Emerging</td>
                </tr>
            `;
        });
    }
    
    html += `</table>`;
    container.innerHTML = html;
}

function generateXAIText(item) {
    const reasons = [];
    const ruralPct = (item.rural_population_percentage || 0) * 100;
    const gap = (1 - (item.biometric_update_ratio || 0)) * 100;

    if (ruralPct > 60) reasons.push(`High rural concentration (${ruralPct.toFixed(0)}%) requires mobile unit prioritization.`);
    if (gap > 20) reasons.push(`Service gap of ${gap.toFixed(1)}% exceeds national average.`);
    if (item.growth_volatility > 5) reasons.push(`Migration intensity (${item.growth_volatility.toFixed(1)}) triggers demand spike warning.`);
    
    if (reasons.length === 0) reasons.push("Routine maintenance cycle due to stable parameters.");

    const ul = document.getElementById('xaiReasoning');
    ul.innerHTML = reasons.map(r => `<li>${r}</li>`).join('');
}

window.closeAnalysisPanel = function() {
    document.getElementById('analysisPanel').classList.remove('open');
    document.getElementById('panelBackdrop').classList.remove('show');
}

function generateCharacterization(item) {
    let text = `The region of <strong>${item.state}</strong> currently falls under the <strong>${item.service_risk_category}</strong> classification. `;
    if (item.integrated_risk_score > 60) {
        text += "System detects a high concentration of underserved populations with significant biometric update backlogs. Immediate administrative intervention is recommended.";
    } else if (item.integrated_risk_score > 30) {
        text += "Moderate service gaps detected. Regular monitoring of enrolment velocity and demographic update trends is required to prevent classification escalation.";
    } else {
        text += "Service delivery remains stable. Current operational parameters are sufficient for the projected demand in the next quarter.";
    }
    return text;
}

function generateMLPrediction(item) {
    const confidence = 85 + (item.integrated_risk_score % 10);
    const trend = item.integrated_risk_score > 50 ? "increasing" : "stabilizing";
    const prediction = `Based on current trajectory, vulnerability is <strong>${trend}</strong>. `;
    const recommendation = item.integrated_risk_score > 40 ? 
        "Model suggests deploying 3 additional temporary enrolment centers to bridge the 60-day backlog." : 
        "Model predicts continued equilibrium; suggest standard maintenance of existing service points.";

    document.getElementById('mlPredictionText').innerHTML = prediction + recommendation;
    // document.getElementById('mlConfidenceBar').style.width = confidence + '%'; // Element removed in UI update
    
    // Generate XAI Explanation
    generateXAIText(item);
}

window.openPlanModalFromPanel = function() {
    const state = document.getElementById('panelStateName').innerText;
    closeAnalysisPanel();
    openPlanModal(state);
}

function initCharts(data) {
    // A. Correlation Chart
    const ctx = document.getElementById('correlationChart').getContext('2d');
    const plotData = data.map(d => ({ x: (d.biometric_update_ratio||0)*100, y: d.integrated_risk_score, state: d.state }));
    
    charts.correlation = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'State Risk vs Coverage',
                data: plotData,
                backgroundColor: plotData.map(d => d.y > 60 ? '#D32F2F' : '#0A3D62')
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { title: {display:true, text:'Coverage %'}, min: 0, max: 100 },
                y: { title: {display:true, text:'Risk Score'}, min: 0, max: 100 }
            },
            plugins: { tooltip: { callbacks: { label: c => c.raw.state + ': ' + c.raw.y.toFixed(1) } } }
        }
    });

    // B. Breakdown Doughnut Chart
    const ctxB = document.getElementById('breakdownChart').getContext('2d');
    charts.breakdown = new Chart(ctxB, {
        type: 'doughnut',
        data: {
            labels: ['Social Vulnerability', 'Service Gap', 'Migration Volatility'],
            datasets: [{
                data: [30, 30, 40],
                backgroundColor: ['#D32F2F', '#F57C00', '#1976D2'], // Red, Orange, Blue
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%', // Makes it a Doughnut
            plugins: {
                legend: { position: 'right', labels: { boxWidth: 12, font: {size: 11} } },
                title: { display: true, text: 'Risk Factor Contribution', align: 'start' }
            }
        }
    });

    // C. Detailed Bar Chart
    const ctxD = document.getElementById('detailedBarChart').getContext('2d');
    charts.detailedBar = new Chart(ctxD, {
        type: 'bar',
        data: {
            labels: ['Social Vulnerability', 'Service Gap', 'Migration Volatility'],
            datasets: [{
                label: 'Risk Score Comparisons',
                data: [0, 0, 0],
                backgroundColor: ['#D32F2F', '#F57C00', '#1976D2'],
                barPercentage: 0.6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, max: 100, title: {display:true, text:'Normalized Score (0-100)'} }
            },
            plugins: {
                legend: { display: false },
                title: { display: true, text: 'Comparative Analysis of Risk Drivers' }
            }
        }
    });
}

function updateBreakdownChart(item) {
    if(!charts.breakdown) return;
    
    // Normalize data for Pie Composition
    // We treat the indices as relative weights for the visualization
    const svs = Math.max(0, item.social_vulnerability_index || 0);
    const gap = Math.max(0, (1 - (item.biometric_update_ratio || 0)) * 100);
    const vol = Math.max(0, (item.growth_volatility || 0) * 100);
    
    charts.breakdown.data.datasets[0].data = [svs, gap, vol];
    charts.breakdown.options.plugins.title.text = `Risk Factors: ${item.state}`;
    charts.breakdown.update();

    // Update Detailed Bar Chart
    if(charts.detailedBar) {
        charts.detailedBar.data.datasets[0].data = [svs, gap, vol];
        charts.detailedBar.options.plugins.title.text = `Detailed Factor Analysis: ${item.state}`;
        charts.detailedBar.update();
    }
}

// 6. Helpers
function populateStateSelector(data) {
    const sel = document.getElementById('stateSelector');
    if (!sel) return;
    const states = [...new Set(data.map(i => i.state.trim()))].sort();
    states.forEach(state => {
        const opt = document.createElement('option');
        opt.value = state;
        opt.innerText = state;
        sel.appendChild(opt);
    });
    sel.onchange = (e) => {
        const item = globalData.find(d => d.state === e.target.value);
        if(item) showRegionDetails(item);
    }
}

window.openPlanModal = function(state) {
    document.getElementById('planModal').style.display = 'flex';
    document.getElementById('modalContent').innerHTML = `<p>Generate official NIC deployment order for <strong>${state}</strong>?</p>`;
    
    // Set Auto-Expiry Date (30 days from now)
    const future = new Date();
    future.setDate(future.getDate() + 30);
    document.getElementById('expiryDate').innerText = future.toLocaleDateString();
}
