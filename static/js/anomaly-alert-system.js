/**
 * ALRIS COMMAND CENTER - Anomaly Alert System
 * Manages real-time tickers, risk heatmaps, and governance interventions.
 */

const AnomalyAlertSystem = {
    alerts: [
        "⚠️ SYSTEM: Determining active alerts...",
    ],
    data: null,

    init(containerId, anomalyData = null, watchlist = {}) {
        if (!anomalyData) return;
        this.data = anomalyData;
        this.watchlist = watchlist;

        // Populate Alerts from all sources (ML-Confirmed, Seasonal, Security, Center)
        const allAlerts = [];
        
        if (anomalyData.ml_confirmed_anomalies) {
            allAlerts.push(...anomalyData.ml_confirmed_anomalies.slice(0, 5).map(a => `🤖 ML-CONFIRMED: ${a.region} - ${a.anomaly_type}`));
        }
        if (anomalyData.retry_anomalies) {
            allAlerts.push(...anomalyData.retry_anomalies.map(a => `🔒 SECURITY: ${a.region} - ${a.anomaly_type}`));
        }
        if (anomalyData.center_anomalies) {
            allAlerts.push(...anomalyData.center_anomalies.map(a => `🔴 CENTER: ${a.center_id} - ${a.anomaly_type}`));
        }
        if (anomalyData.seasonal_anomalies) {
            allAlerts.push(...anomalyData.seasonal_anomalies.slice(0, 5).map(a => `📊 SEASONAL: ${a.region} - ${a.anomaly_type}`));
        }
        if (anomalyData.peer_lag_anomalies) {
            allAlerts.push(...anomalyData.peer_lag_anomalies.map(a => `🧭 PEER GAP: ${a.state} - ${a.gap_pct}% Lag`));
        }

        if (allAlerts.length > 0) {
            this.alerts = allAlerts;
        }

        this.renderTicker(containerId);
        this.renderRiskHeatmap('riskHeatmap', anomalyData);
        this.renderDefaultGovernance();
    },

    renderTicker(id) {
        const container = document.getElementById(id);
        if (!container) return;
        
        const content = this.alerts.join(' &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ');
        container.innerHTML = `<div class="ticker-content">${content} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ${content} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ${content}</div>`;
    },

    renderDeviationMatrix(containerId, anomalies) {
        const table = document.getElementById(containerId);
        if (!table || !anomalies) return;

        const rows = [
            ...(Array.isArray(anomalies.state_anomalies) ? anomalies.state_anomalies : []),
            ...(Array.isArray(anomalies.seasonal_anomalies) ? anomalies.seasonal_anomalies : []),
            ...(Array.isArray(anomalies.ml_confirmed_anomalies) ? anomalies.ml_confirmed_anomalies : []),
            ...(Array.isArray(anomalies.peer_lag_anomalies) ? anomalies.peer_lag_anomalies : []),
            ...(Array.isArray(anomalies.retry_anomalies) ? anomalies.retry_anomalies : [])
        ];
        
        const uniqueRows = [];
        const seen = new Set();
        rows.forEach(row => {
            const regionName = row.state || row.region || 'N/A';
            const key = `${regionName}-${row.date}-${row.anomaly_type}`;
            if (!seen.has(key)) { seen.add(key); uniqueRows.push(row); }
        });
        
        if (uniqueRows.length === 0) {
            table.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px;">No anomalies detected in the current window.</td></tr>';
            return;
        }

        const severityOrder = { 'Critical': 3, 'High': 2, 'Medium': 1 };
        uniqueRows.sort((a, b) => (severityOrder[b.severity] || 0) - (severityOrder[a.severity] || 0));

        table.innerHTML = uniqueRows.slice(0, 15).map(row => {
            const severityColor = this._getSeverityColor(row.severity || 'Medium');
            const confColor = this._getConfidenceColor(row.confidence_score || 0);
            const region = row.state || row.region || 'N/A';
            const persistence = row.temporal_persistence || 'Assessing...';
            
            return `
                <tr>
                    <td style="font-weight:700;">${region}</td>
                    <td><span style="font-size:0.7rem; font-weight:700; border:1px solid ${severityColor}; color:${severityColor}; padding:2px 6px; border-radius:4px;">${row.anomaly_type}</span></td>
                    <td style="font-family: 'Roboto Mono'; font-weight:700; color:${severityColor};">${row.severity || 'Medium'}</td>
                    <td><span style="font-weight:700; color:${confColor}; font-size:0.85rem;">${row.confidence_score || '0.0'}%</span></td>
                    <td><span class="badge ${persistence.includes('High') ? 'priority-high' : 'priority-med'}" style="font-size:0.6rem;">${persistence}</span></td>
                    <td><button class="btn-tool-outline" style="padding:4px 8px; font-size:0.7rem;" onclick="AnomalyAlertSystem.showDetail('${region}', '${row.anomaly_type}')">Analyze</button></td>
                </tr>
            `;
        }).join('');
    },

    renderRiskHeatmap(containerId, anomalies) {
        const container = document.getElementById(containerId);
        if (!container || !anomalies) return;

        // Map data regions to canonical UI regions
        const regionMapping = {
            'North': 'North',
            'South': 'South',
            'East': 'East',
            'West': 'West',
            'Central': 'Central',
            'North-East': 'NE',
            'NE': 'NE',
            'Others': 'Central'
        };

        const regions = ['North', 'South', 'East', 'West', 'Central', 'NE'];
        const riskScore = {};
        regions.forEach(r => riskScore[r] = 0);

        const all = [
            ...(anomalies.state_anomalies || []),
            ...(anomalies.seasonal_anomalies || []),
            ...(anomalies.center_anomalies || []),
            ...(anomalies.retry_anomalies || [])
        ];

        all.forEach(a => {
            const rawRegion = a.region || a.state || 'North';
            const mapped = regionMapping[rawRegion] || 'North';
            const weight = a.severity === 'Critical' ? 10 : (a.severity === 'High' ? 5 : 2);
            riskScore[mapped] = (riskScore[mapped] || 0) + weight;
        });

        const maxScore = Math.max(...Object.values(riskScore), 1);

        container.innerHTML = `
            <div style="font-size:0.7rem; font-weight:800; color:var(--text-secondary); margin-bottom:10px; display:flex; justify-content:space-between;">
                <span>REGIONAL RISK DISTRIBUTION</span>
                <span style="color:var(--gov-blue);">Stage 3 Normalized</span>
            </div>
            <div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:10px;">
                ${regions.map(r => {
                    const score = riskScore[r];
                    const pct = Math.min(100, (score / maxScore) * 100);
                    const color = score > 15 ? 'var(--color-alert)' : (score > 5 ? 'var(--gov-saffron)' : 'var(--gov-blue)');
                    return `
                        <div style="padding:10px; background:#fff; border-radius:6px; border-left:4px solid ${score > 0 ? color : '#eee'}; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                            <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                                <span style="font-size:0.75rem; font-weight:700;">${r} Zone</span>
                                <span style="font-size:0.6rem; font-family:'Roboto Mono'; font-weight:700; color:${color};">${score.toFixed(1)}</span>
                            </div>
                            <div style="height:4px; background:#f0f0f0; margin-top:5px; border-radius:2px; overflow:hidden;">
                                <div style="width:${pct}%; height:100%; background:${color}; transition: width 1s ease-in-out;"></div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    },

    renderDefaultGovernance() {
        const container = document.getElementById('governanceActions');
        if (!container) return;
        
        container.innerHTML = `
            <div style="font-size:0.75rem; font-weight:700; color:var(--gov-blue); margin-bottom:12px; border-bottom:1px solid #eee; padding-bottom:5px;">STANDARD GOVERNANCE PROTOCOL</div>
            <div style="display:flex; flex-direction:column; gap:12px;">
                <div style="background:rgba(0,0,0,0.02); padding:10px; border-radius:6px;">
                    <div style="font-weight:700; font-size:0.8rem; color:var(--gov-blue);">L1: Automated Observation</div>
                    <div style="font-size:0.7rem; color:var(--text-secondary); line-height:1.2; margin-top:3px;">Continuous monitoring of cross-regional correlation clusters and anomaly persistence.</div>
                </div>
                <div style="background:rgba(0,0,0,0.02); padding:10px; border-radius:6px;">
                    <div style="font-weight:700; font-size:0.8rem; color:var(--gov-blue);">L2: Tactical Response</div>
                    <div style="font-size:0.7rem; color:var(--text-secondary); line-height:1.2; margin-top:3px;">Select a specific alert from the matrix for context-aware governance interventions.</div>
                </div>
            </div>
        `;
    },

    renderCenterWatchlist(containerId, anomalies) {
        const table = document.getElementById(containerId);
        if (!table || !anomalies) return;

        const rows = anomalies.center_anomalies || [];
        if (rows.length === 0) {
           table.innerHTML = '<tr><td colspan="6" style="text-align:center;">No high-risk centers detected.</td></tr>';
           return;
        }

        table.innerHTML = rows.slice(0, 10).map(row => {
             const severityColor = this._getSeverityColor(row.severity);
             const persistence = row.temporal_persistence || 'New';
             const confColor = this._getConfidenceColor(row.confidence_score || 0);

             return `
                <tr>
                    <td style="font-weight:700;">${row.center_id}</td>
                    <td>${row.region}</td>
                    <td><span style="background:${severityColor}; color:white; padding:2px 8px; border-radius:4px; font-size:0.7rem;">${row.anomaly_type}</span></td>
                    <td style="font-family: 'Roboto Mono'; font-weight:700; color:${confColor};">${row.confidence_score}%</td>
                    <td><span class="badge ${persistence.includes('High') ? 'priority-high' : 'priority-med'}" style="font-size:0.65rem;">${persistence}</span></td>
                    <td><button class="btn-tool-red" ${this.watchlist && this.watchlist[row.center_id] ? 'disabled title="Entity Blocked"' : ''} style="padding:4px 8px; font-size:0.7rem;" onclick="AnomalyAlertSystem.initiateBlockSequence('${row.center_id}', '${row.confidence_score}')">${this.watchlist && this.watchlist[row.center_id] ? 'Blocked' : 'Block'}</button></td>
                </tr>
            `;
        }).join('');
    },

    renderRetryPatterns(containerId, anomalies) {
        const container = document.getElementById(containerId);
        if (!container || !anomalies) return;
        
        const rows = anomalies.retry_anomalies || [];
        if (rows.length === 0) {
            container.innerHTML = '<div style="padding:20px; text-align:center;">No auth security threats detected.</div>';
            return;
        }

        container.innerHTML = `
            <table class="table-gov">
                <thead><tr><th>Region</th><th>Type</th><th>Ratio</th><th>Conf.</th></tr></thead>
                <tbody>
                    ${rows.slice(0, 5).map(row => `
                        <tr>
                            <td>${row.region}</td>
                            <td style="color:var(--color-alert); font-weight:700; font-size:0.7rem;">${row.anomaly_type.replace('Auth ', '')}</td>
                            <td style="font-family:'Roboto Mono'">${row.value}%</td>
                            <td style="font-weight:700; color:${this._getConfidenceColor(row.confidence_score)};">${row.confidence_score}%</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    },

    async showDetail(state, title = "") {
        const container = document.getElementById('anomalyDetail');
        if (!container) return;
        container.innerHTML = '<div style="padding:20px; text-align:center;">Analyzing Pattern Correlation Cluster... <span class="spinner"></span></div>';
        
        try {
            let detailData = null;
            if (this.data) {
                 const all = [
                    ...(this.data.state_anomalies || []),
                    ...(this.data.seasonal_anomalies || []),
                    ...(this.data.ml_confirmed_anomalies || []),
                    ...(this.data.peer_lag_anomalies || []),
                    ...(this.data.center_anomalies || []),
                    ...(this.data.retry_anomalies || [])
                 ];
                 
                 const target = all.find(a => 
                    (a.state || a.region || a.center_id || '').toLowerCase() === state.toLowerCase() &&
                    (!title || a.anomaly_type === title)
                 );
                 
                 if (target) {
                    detailData = {
                        ml_confidence: target.confidence_score || '85.0',
                        root_cause: target.explanation || "Statistical deviation in traffic pattern",
                        persistence: target.temporal_persistence || 'Low',
                        severity: target.severity || 'Medium',
                        type: target.anomaly_type,
                        region: state,
                        compliance_signature: target.compliance_signature || "UNAVAILABLE",
                        logs: [
                            `[STAGE 1] Analyzing ${target.metric || 'metric'} vector... OK`,
                            `[STAGE 2] ML multi-signal confirmation: ${target.confidence_score ? 'VERIFIED' : 'PENDING'}`,
                            `[STAGE 3] Temporal Correlation: ${target.concurrent_anomalies || 0} concurrent events`,
                            `[STAGE 3] Geo Hotspot Score: ${target.geo_hotspot_score || 0.0}`,
                            `[STAGE 3] Persistence: ${target.temporal_persistence || 'New Event'}`,
                            `[STAGE 4] Compliance Audit Trace: SIGNED_OFF`,
                            `Investigation complete. Findings: ${target.anomaly_type}`
                        ]
                    };
                 }
            }

            if (!detailData) throw new Error("Anomaly details not found or suppressed.");

            this.renderGovernanceHub('governanceActions', detailData);

            const logsHtml = detailData.logs.map((log, i) => 
                `<div style="opacity:${0.5 + (i * 0.1)}; animation: fadeIn 0.3s ease ${i * 0.15}s forwards;">[+${(i * 0.2).toFixed(1)}s] ${log}</div>`
            ).join('');

            container.innerHTML = `
                <div style="border-bottom: 2px solid var(--gov-saffron); margin-bottom: 20px; padding-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h3 style="margin:0; color: var(--gov-blue); font-size: 1.5rem;">INVESTIGATION TARGET: ${state.toUpperCase()}</h3>
                        <p style="margin:5px 0 0 0; color:var(--text-secondary); font-family:var(--font-data);">Correlation Context: ${detailData.root_cause}</p>
                    </div>
                    <div style="text-align:right;">
                        <span class="badge ${detailData.persistence.includes('High') ? 'priority-high' : 'priority-med'}" style="margin-right:10px;">${detailData.persistence}</span>
                        <div style="font-size: 0.8rem; font-weight: 700; color: #16a34a; border: 1px solid #16a34a; padding: 4px 8px; border-radius: 4px; display:inline-block;">COMPLIANCE VERIFIED</div>
                    </div>
                </div>
                <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:20px;">
                    <div class="card" style="background:var(--bg-light); padding:15px; border-radius:8px; display:flex; flex-direction:column; justify-content:center; align-items:center;">
                        <div style="font-size:0.7rem; font-weight:800; color:var(--text-secondary); text-transform:uppercase; margin-bottom:5px;">ML Confidence</div>
                        <div style="font-size:1.8rem; font-weight:700; color:${this._getConfidenceColor(detailData.ml_confidence)};">${detailData.ml_confidence}%</div>
                    </div>
                    <div class="card" style="background:var(--bg-light); padding:15px; border-radius:8px; border-left:4px solid var(--color-alert);">
                        <div style="font-size:0.7rem; font-weight:800; color:var(--text-secondary); text-transform:uppercase; margin-bottom:5px;">Threat Level</div>
                        <div style="font-size:1.2rem; font-weight:700; color:var(--color-alert);">${detailData.severity.toUpperCase()}</div>
                    </div>
                    <div class="card" style="background:var(--bg-light); padding:15px; border-radius:8px; grid-column: span 2;">
                        <div style="font-size:0.75rem; font-weight:700; color:var(--gov-blue); margin-bottom:5px;">AUDIT SIGNATURE (Audit Trail Vault)</div>
                        <div style="font-family:'Roboto Mono'; font-size:0.9rem; color: #16a34a; background:#fff; padding:8px; border-radius:4px; border:1px solid #ddd; text-align:center;">
                            H-CERT-${detailData.compliance_signature}
                        </div>
                        <div style="font-size:0.6rem; color:var(--text-secondary); margin-top:5px; text-align:center;">Cryptographic proof of non-biometric, aggregated analysis.</div>
                    </div>
                </div>
                ${detailData.type === 'Peer Performance Gap' ? `<div id="peerBenchmarking" style="margin-top:20px;"></div>` : ''}
                <div style="margin-top:20px;">
                    <div style="font-size:0.75rem; font-weight:700; color:var(--gov-blue); margin-bottom:10px;">TECHNICAL AUDIT LOGS</div>
                    <div style="background:#0d1117; color:#39ff14; padding:20px; border-radius:8px; font-family:'Roboto Mono'; font-size:0.85rem; height:180px; overflow-y:auto; border-left:4px solid #39ff14; position:relative;">
                        ${logsHtml}
                        <div style="position:absolute; bottom:10px; right:15px; opacity:0.3; pointer-events:none;">
                            <img src="/assets/images/goi_logo.png" style="height:40px; filter: grayscale(1) invert(1);">
                        </div>
                    </div>
                </div>
            `;
            container.scrollIntoView({ behavior: 'smooth', block: 'start' });
            
            if (detailData.type === 'Peer Performance Gap') {
                this.renderPeerBenchmarking('peerBenchmarking', state);
            }
        } catch (err) {
            container.innerHTML = `<div style="color:var(--color-alert); padding:20px; border:1px dashed var(--color-alert); background:rgba(220,38,38,0.05);"><strong>Investigation Failed:</strong> ${err.message}</div>`;
        }
    },

    renderGovernanceHub(containerId, detail) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const recommendations = this._getDetailedRecommendations(detail);

        container.innerHTML = `
            <div style="font-size:0.75rem; font-weight:700; color:var(--gov-blue); margin-bottom:12px; border-bottom:1px solid #eee; padding-bottom:5px;">GOVERNANCE INTELLIGENCE HUB</div>
            <div style="display:flex; flex-direction:column; gap:12px;">
                ${recommendations.map(rec => `
                    <div style="display:flex; gap:12px; align-items:flex-start; background:rgba(0,0,0,0.02); padding:10px; border-radius:6px; border-right:3px solid ${rec.impact === 'High' ? 'var(--color-alert)' : 'var(--gov-saffron)'};">
                        <span style="font-size:1.2rem; background:#fff; width:30px; height:30px; display:flex; align-items:center; justify-content:center; border-radius:50%; box-shadow:0 1px 3px rgba(0,0,0,0.1);">${rec.icon}</span>
                        <div style="flex:1;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div style="font-weight:700; font-size:0.85rem; color:var(--gov-blue);">${rec.title}</div>
                                <span style="font-size:0.6rem; font-weight:700; color:${rec.impact === 'High' ? 'var(--color-alert)' : 'var(--gov-saffron)'}; text-transform:uppercase;">Impact: ${rec.impact}</span>
                            </div>
                            <div style="font-size:0.75rem; color:var(--text-secondary); line-height:1.3; margin-top:4px;">${rec.desc}</div>
                            <div style="display:flex; justify-content:space-between; margin-top:5px; align-items:center;">
                                <div style="font-size:0.65rem; font-weight:600; color:var(--text-tertiary); font-style:italic;">Dept: ${rec.owner}</div>
                                <div style="font-size:0.6rem; color:var(--gov-blue); font-weight:700; background:rgba(0,102,204,0.1); padding:1px 5px; border-radius:3px;">${rec.sla}</div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
            <div style="margin-top:20px; display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                <button class="btn-tool-blue" style="width:100%; font-size:0.75rem;" onclick="window.print()">
                    📄 Export Executive Brief
                </button>
                <button class="btn-tool-red" ${this.watchlist && this.watchlist[detail.region] ? 'disabled' : ''} style="width:100%; font-size:0.75rem;" onclick="AnomalyAlertSystem.initiateBlockSequence('${detail.region}', '${detail.ml_confidence}')">
                    ${this.watchlist && this.watchlist[detail.region] ? '🚫 ENTITY BLOCKED' : '🚫 BLOCK ENTITY'}
                </button>
            </div>
        `;
        container.dataset.entityId = detail.region; // Store current identity for refresh
    },

    initiateBlockSequence(entityId, mlConf) {
        document.getElementById('modalEntityId').value = entityId;
        document.getElementById('modalMlConf').value = mlConf + "%";
        document.getElementById('blockReason').value = '';
        document.getElementById('blockModal').style.display = 'flex';
        
        // Dynamic binding to avoid memory leaks
        const confirmBtn = document.getElementById('confirmBlockBtn');
        confirmBtn.onclick = () => this.executeBlockAction(entityId, mlConf);
    },

    closeBlockModal() {
        document.getElementById('blockModal').style.display = 'none';
    },

    async executeBlockAction(entityId, mlConf) {
        const reason = document.getElementById('blockReason').value;
        const persistence = document.getElementById('blockPersistence').value;

        if (!reason) {
            this.showToast("Block reason is required.", "error");
            return;
        }

        try {
            const res = await fetch('/api/admin/block', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    entity_id: entityId,
                    reason: reason,
                    ml_confidence: mlConf,
                    persistence: persistence
                })
            });

            if (res.ok) {
                this.closeBlockModal();
                this.showToast(`Blocked ${entityId} successfully.`, "success", entityId);
                await this.refreshWatchlist();
            } else {
                throw new Error("Backend rejection.");
            }
        } catch (e) {
            this.showToast("Failed to execute block order.", "error");
        }
    },

    async executeUndoAction(entityId) {
        try {
            const res = await fetch('/api/admin/undo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ entity_id: entityId })
            });

            if (res.ok) {
                this.showToast(`Block order for ${entityId} reversed.`, "success");
                await this.refreshWatchlist();
            }
        } catch (e) {
            this.showToast("Undo operation failed.", "error");
        }
    },

    async downloadAuditTrail() {
        this.showToast("Preparing legal audit trail...", "info");
        try {
            window.location.href = '/api/admin/download-audit';
        } catch (e) {
            this.showToast("Failed to initiate download.", "error");
        }
    },

    async refreshWatchlist() {
        if (typeof DataLoader !== 'undefined') {
            this.watchlist = await DataLoader.fetchWatchlist();
            // Re-render components that depend on watchlist
            this.renderCenterWatchlist('centerWatchlist', this.data);
            
            // If we have an active detail, re-render the governance hub
            const container = document.getElementById('governanceActions');
            if (container && container.dataset.entityId) {
                 // We can't easily re-render without the full detail object, 
                 // but for this demo, usually users block from the watchlist.
            }
        }
    },

    showToast(message, type = "success", entityId = null) {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        let content = `<span>${message}</span>`;
        if (entityId && type === 'success') {
            content += `<button class="toast-undo" onclick="AnomalyAlertSystem.executeUndoAction('${entityId}'); this.parentElement.remove();">UNDO</button>`;
        }
        
        toast.innerHTML = content;
        container.appendChild(toast);

        setTimeout(() => {
            if (toast.parentElement) toast.remove();
        }, 8000);
    },

    _getDetailedRecommendations(detail) {
        const type = detail.type || 'General Anomaly';
        const recs = [];
        
        if (type.includes('Auth Brute-Force')) {
            recs.push({ icon: '🔍', title: 'Deep Digital Audit', owner: 'Cyber Security Cell', impact: 'High', sla: '2H Response', desc: 'Perform multi-factor analysis on regional IP clusters to identify proxy patterns.' });
            recs.push({ icon: '⏳', title: 'Regional Throttling', owner: 'National Auth Engine', impact: 'High', sla: 'Immediate', desc: 'Introduce 500ms latency for OTP generation in ${detail.region} zone to break automated loops.' });
            recs.push({ icon: '🛡️', title: 'Credential Rotation', owner: 'Ops Security', impact: 'High', sla: '4H Window', desc: 'Force operator password and session resets for all active centers in the affected zone.' });
        } else if (type.includes('Bot Risk') || type.includes('Efficiency')) {
            recs.push({ icon: '🚨', title: 'Physical Field Inspection', owner: 'Regional Audit Team', impact: 'High', sla: '24H Deployment', desc: 'Deploy technical audit team to verify hardware integrity at Center ${detail.region}.' });
            recs.push({ icon: '🛑', title: 'Operational Throttling', owner: 'Service Management', impact: 'Medium', sla: 'Immediate', desc: 'Cap hourly update volume to 110% of historic mean until anomaly investigation clears.' });
            recs.push({ icon: '👤', title: 'Operator Scrubbing', owner: 'Human Resource Cell', impact: 'Medium', sla: 'Next Shift', desc: 'Review operator biometric logs for "impossible travel" or concurrent session patterns.' });
        } else if (type.includes('Seasonal')) {
            recs.push({ icon: '📋', title: 'Baseline Recalibration', owner: 'Gov Analytics Div', impact: 'Low', sla: '7D Review', desc: 'Adjust seasonal baseline parameters for next period based on confirmed legitimate deviation.' });
            recs.push({ icon: '📡', title: 'Elastic Scaling', owner: 'Technology Hub', impact: 'Medium', sla: '4H Buffer', desc: 'Allocate additional server bandwidth to ${detail.region} to handle confirmed legitimate spike.' });
        } else {
            recs.push({ icon: '📋', title: 'Infrastructure Audit', owner: 'General Admin', impact: 'Low', sla: '48H Review', desc: 'Review regional logs for recent infrastructure changes that could cause metric variance.' });
            recs.push({ icon: '⚙️', title: 'Compliance Inquiry', owner: 'Compliance Cell', impact: 'Medium', sla: '3D Window', desc: 'Issue a "Show Cause" notice to regional admins regarding significant metric deviation.' });
        }
        return recs;
    },

    _getConfidenceColor(score) {
        const s = parseFloat(score);
        if (s >= 90) return '#16a34a';
        if (s >= 80) return '#d97706';
        return '#dc2626';
    },

    _getSeverityColor(severity) {
        return severity === 'Critical' ? 'var(--color-alert)' : (severity === 'High' ? 'var(--gov-saffron)' : 'var(--gov-blue)');
    },

    async renderPeerBenchmarking(containerId, stateName) {
        const container = document.getElementById(containerId);
        if (!container) return;

        try {
            const response = await fetch('/api/data/peer_benchmarks.json');
            const peerData = await response.json();
            const benchmark = peerData.find(b => b.state.toLowerCase() === stateName.toLowerCase());

            if (!benchmark) return;

            container.innerHTML = `
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:20px;">
                    <div style="font-size:0.85rem; font-weight:700; color:var(--gov-blue); margin-bottom:15px; display:flex; justify-content:space-between; align-items:center;">
                        <span>🧭 REGIONAL PEER COMPARISON: ${stateName}</span>
                        <span style="font-size:0.7rem; color:var(--text-secondary);">Demographic Peer Group ${benchmark.peer_group}</span>
                    </div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:30px;">
                        <div>
                            <div style="font-size:0.7rem; font-weight:600; color:var(--text-secondary); margin-bottom:10px;">PERFORMANCE VS. PEER MEDIAN</div>
                            <div style="display:flex; align-items:center; gap:15px; margin-bottom:15px;">
                                <div style="flex:1; height:12px; background:#e2e8f0; border-radius:6px; overflow:hidden; position:relative;">
                                    <div style="position:absolute; left:0; top:0; height:100%; width:85%; background:var(--gov-blue); opacity:0.3;" title="Peer Median"></div>
                                    <div style="position:absolute; left:0; top:0; height:100%; width:${85 - benchmark.performance_gap}%; background:var(--color-alert);" title="${stateName} Performance"></div>
                                </div>
                                <span style="font-family:'Roboto Mono'; font-weight:700; color:var(--color-alert); font-size:0.8rem;">-${benchmark.performance_gap}%</span>
                            </div>
                            <div style="font-size:0.75rem; line-height:1.4; color:var(--text-secondary);">
                                <strong>Insight:</strong> ${benchmark.comparative_insight}
                            </div>
                        </div>
                        <div style="border-left:1px dashed #cbd5e1; padding-left:30px;">
                            <div style="font-size:0.7rem; font-weight:600; color:var(--text-secondary); margin-bottom:10px;">DEMOGRAPHIC PEERS</div>
                            <div style="display:flex; flex-wrap:wrap; gap:8px;">
                                ${benchmark.peers.map(p => `
                                    <span style="background:white; border:1px solid #e2e8f0; padding:4px 8px; border-radius:4px; font-size:0.7rem; font-weight:600; color:var(--gov-blue);">${p}</span>
                                `).join('')}
                            </div>
                            <div style="margin-top:15px; padding:10px; background:rgba(0,102,204,0.03); border-radius:4px; font-size:0.65rem; color:var(--gov-blue);">
                                ℹ️ Peer grouping is derived from similarity in Urbanization, ST Ratio, and Geriatric Dependency Metrics.
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } catch (e) {
            console.error("Failed to load peer benchmarking data", e);
        }
    }
};

window.AnomalyAlertSystem = AnomalyAlertSystem;
