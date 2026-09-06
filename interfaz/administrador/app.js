/**
 * Centro Antifraude BCP - Yape
 * Lógica del Dashboard de Administrador
 * Visualizaciones con Chart.js, feed en tiempo real y gestión de alertas
 */

let charts = {
    timeline: null,
    riskDist: null,
    products: null,
    models: null
};

let autoRefreshInterval = null;

document.addEventListener("DOMContentLoaded", async () => {
    const sesionValida = await verificarSesionAdmin();
    if (!sesionValida) return;

    configurarChartDefaults();
    inicializarTabs();
    inicializarEventos();
    
    // Carga inicial de datos
    cargarMetricas();
    cargarGraficos();
    cargarTransacciones();
    cargarAlertas();

    // Sondeo periódico cada 4 segundos para actualización en tiempo real
    autoRefreshInterval = setInterval(() => {
        cargarMetricas(false);
        cargarGraficos(false);
        cargarTransacciones(false);
        cargarAlertas(false);
    }, 4000);
});

async function verificarSesionAdmin() {
    try {
        const res = await fetch("/api/auth/sesion");
        const data = await res.json();
        if (!data.autenticado || data.usuario.tipo_usuario !== "ADMIN") {
            window.location.href = "/admin/login";
            return false;
        }
        return true;
    } catch (err) {
        return true;
    }
}

// ============================================================
// CONFIGURACIÓN GLOBAL DE CHART.JS (ESTILO DARK FINTECH)
// ============================================================

function configurarChartDefaults() {
    if (typeof Chart === "undefined") return;

    Chart.defaults.color = "#94A3B8";
    Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
    Chart.defaults.font.size = 11;
    Chart.defaults.plugins.tooltip.backgroundColor = "rgba(17, 24, 39, 0.95)";
    Chart.defaults.plugins.tooltip.titleColor = "#FFFFFF";
    Chart.defaults.plugins.tooltip.bodyColor = "#E2E8F0";
    Chart.defaults.plugins.tooltip.borderColor = "rgba(255, 255, 255, 0.1)";
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 10;
}

// ============================================================
// GESTIÓN DE PESTAÑAS (TABS)
// ============================================================

function inicializarTabs() {
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetId = btn.getAttribute("data-tab");

            tabButtons.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            const targetEl = document.getElementById(targetId);
            if (targetEl) targetEl.classList.add("active");

            // Redibujar gráficos si entra a la pestaña de resumen
            if (targetId === "tab-overview") {
                Object.values(charts).forEach(ch => { if (ch) ch.resize(); });
            }
        });
    });
}

// ============================================================
// EVENTOS Y BOTONES DE SIMULACIÓN
// ============================================================

function inicializarEventos() {
    // 0. Cerrar Sesión de Administrador
    document.getElementById("btnLogoutAdmin")?.addEventListener("click", async () => {
        if (confirm("¿Deseas cerrar tu sesión del Centro Antifraude?")) {
            await fetch("/api/auth/logout", { method: "POST" });
            window.location.href = "/admin/login";
        }
    });

    // 1. Simular Ráfaga
    document.getElementById("btnSimBurst")?.addEventListener("click", () => {
        ejecutarSimulacion("rafaga");
    });

    // 2. Simular Fraude
    document.getElementById("btnSimFraud")?.addEventListener("click", () => {
        ejecutarSimulacion("fraude");
    });

    // 3. Reset Demo
    document.getElementById("btnResetDemo")?.addEventListener("click", async () => {
        if (!confirm("¿Deseas reiniciar la base de datos al estado inicial de demostración?")) return;
        try {
            const res = await fetch("/api/admin/reset-demo", { method: "POST" });
            const data = await res.json();
            alert(data.mensaje || "Base de datos restaurada.");
            cargarMetricas();
            cargarGraficos();
            cargarTransacciones();
            cargarAlertas();
        } catch (err) {
            alert("Error al reiniciar datos.");
        }
    });

    // 4. Búsqueda y Filtros de Transacciones
    const inputSearchTx = document.getElementById("inputSearchTx");
    const selectFilterTx = document.getElementById("selectFilterTx");
    const btnRefreshAdminTx = document.getElementById("btnRefreshAdminTx");

    if (inputSearchTx) inputSearchTx.addEventListener("input", filtrarTablaTransacciones);
    if (selectFilterTx) selectFilterTx.addEventListener("change", () => cargarTransacciones(true));
    if (btnRefreshAdminTx) btnRefreshAdminTx.addEventListener("click", () => cargarTransacciones(true));

    // 5. Filtro de Alertas
    const selectFilterAlerts = document.getElementById("selectFilterAlerts");
    const btnRefreshAdminAlerts = document.getElementById("btnRefreshAdminAlerts");

    if (selectFilterAlerts) selectFilterAlerts.addEventListener("change", () => cargarAlertas(true));
    if (btnRefreshAdminAlerts) btnRefreshAdminAlerts.addEventListener("click", () => cargarAlertas(true));

    // 6. Cerrar Modal Forense
    const modalForensic = document.getElementById("modalForensic");
    const btnCloseForensic = document.getElementById("btnCloseForensic");
    const btnCloseForensicFooter = document.getElementById("btnCloseForensicFooter");

    [btnCloseForensic, btnCloseForensicFooter].forEach(b => {
        b?.addEventListener("click", () => {
            if (modalForensic) modalForensic.style.display = "none";
        });
    });

    if (modalForensic) {
        modalForensic.addEventListener("click", (e) => {
            if (e.target === modalForensic) modalForensic.style.display = "none";
        });
    }
}

async function ejecutarSimulacion(tipo) {
    try {
        const res = await fetch("/api/admin/simular", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tipo: tipo })
        });
        const data = await res.json();
        if (data.status === "success") {
            // Actualizar vistas de inmediato
            cargarMetricas(false);
            cargarGraficos(false);
            cargarTransacciones(false);
            cargarAlertas(false);
        }
    } catch (err) {
        console.warn("Error en simulación:", err);
    }
}

// ============================================================
// CARGA DE MÉTRICAS Y KPIS
// ============================================================

async function cargarMetricas(conSpinner = true) {
    try {
        const res = await fetch("/api/admin/metricas");
        const data = await res.json();
        if (data.status === "success") {
            const m = data.metricas;

            document.getElementById("kpiTotalTx").textContent = m.total_transacciones.toLocaleString();
            document.getElementById("kpiVolumenTotal").textContent = `S/ ${m.volumen_total.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            
            document.getElementById("kpiTasaFraude").textContent = `${m.tasa_fraude}%`;
            document.getElementById("kpiTotalFraudes").textContent = `${m.total_fraudes_detectados} sospechosas`;

            document.getElementById("kpiDineroProtegido").textContent = `S/ ${m.dinero_protegido.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            document.getElementById("kpiAlertasPendientes").textContent = m.alertas_pendientes;

            // Badges en pestañas
            const bTx = document.getElementById("badgeTxCount");
            if (bTx) bTx.textContent = m.total_transacciones;

            const bAl = document.getElementById("badgeAlertsCount");
            if (bAl) bAl.textContent = m.alertas_pendientes;
        }
    } catch (err) {
        console.warn("Error al cargar métricas:", err);
    }
}

// ============================================================
// CARGA Y RENDERIZADO DE GRÁFICOS (CHART.JS)
// ============================================================

async function cargarGraficos(conSpinner = true) {
    try {
        const res = await fetch("/api/admin/graficos");
        const data = await res.json();
        if (data.status === "success") {
            renderizarChartTimeline(data.timeline);
            renderizarChartRiskDist(data.distribucion_riesgo);
            renderizarChartProducts(data.productos);
            renderizarChartModels(data.modelos);
            renderizarTablaModelos(data.modelos);
        }
    } catch (err) {
        console.warn("Error al cargar gráficos:", err);
    }
}

function renderizarChartTimeline(data) {
    const ctx = document.getElementById("chartTimeline");
    if (!ctx) return;

    if (charts.timeline) {
        charts.timeline.data.labels = data.labels;
        charts.timeline.data.datasets[0].data = data.normales;
        charts.timeline.data.datasets[1].data = data.fraudes;
        charts.timeline.update();
        return;
    }

    charts.timeline = new Chart(ctx, {
        type: "line",
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: "Transacciones Normales",
                    data: data.normales,
                    borderColor: "#00D2C4",
                    backgroundColor: "rgba(0, 210, 196, 0.1)",
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2.5,
                    pointRadius: 3,
                    pointBackgroundColor: "#00D2C4"
                },
                {
                    label: "Sospechosas / Fraude",
                    data: data.fraudes,
                    borderColor: "#EF4444",
                    backgroundColor: "rgba(239, 68, 68, 0.15)",
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2.5,
                    pointRadius: 4,
                    pointBackgroundColor: "#EF4444"
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: "rgba(255, 255, 255, 0.05)" }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: "rgba(255, 255, 255, 0.05)" },
                    ticks: { precision: 0 }
                }
            }
        }
    });
}

function renderizarChartRiskDist(data) {
    const ctx = document.getElementById("chartRiskDist");
    if (!ctx) return;

    if (charts.riskDist) {
        charts.riskDist.data.datasets[0].data = data.data;
        charts.riskDist.update();
        return;
    }

    charts.riskDist = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: data.labels,
            datasets: [{
                data: data.data,
                backgroundColor: [
                    "#10B981", // Bajo
                    "#F59E0B", // Medio
                    "#F87171", // Alto
                    "#EF4444"  // Crítico
                ],
                borderWidth: 2,
                borderColor: "#111827"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "70%",
            plugins: {
                legend: {
                    position: "right",
                    labels: { boxWidth: 12, padding: 14 }
                }
            }
        }
    });
}

function renderizarChartProducts(data) {
    const ctx = document.getElementById("chartProducts");
    if (!ctx) return;

    if (charts.products) {
        charts.products.data.labels = data.labels;
        charts.products.data.datasets[0].data = data.fraudes;
        charts.products.data.datasets[1].data = data.totales;
        charts.products.update();
        return;
    }

    charts.products = new Chart(ctx, {
        type: "bar",
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: "Fraudes Detectados",
                    data: data.fraudes,
                    backgroundColor: "#EF4444",
                    borderRadius: 6
                },
                {
                    label: "Total Operaciones",
                    data: data.totales,
                    backgroundColor: "rgba(138, 43, 226, 0.4)",
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { display: false } },
                y: { grid: { color: "rgba(255, 255, 255, 0.05)" }, beginAtZero: true }
            }
        }
    });
}

function renderizarChartModels(modelos) {
    const ctx = document.getElementById("chartModels");
    if (!ctx || !modelos || modelos.length === 0) return;

    const labels = modelos.map(m => m.nombre);
    const accData = modelos.map(m => m.accuracy);
    const f1Data = modelos.map(m => m.f1_score);

    if (charts.models) {
        charts.models.data.labels = labels;
        charts.models.data.datasets[0].data = accData;
        charts.models.data.datasets[1].data = f1Data;
        charts.models.update();
        return;
    }

    charts.models = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Exactitud (Accuracy %)",
                    data: accData,
                    backgroundColor: "#00D2C4",
                    borderRadius: 6
                },
                {
                    label: "F1-Score (%)",
                    data: f1Data,
                    backgroundColor: "#8A2BE2",
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            scales: {
                x: {
                    min: 40,
                    max: 100,
                    grid: { color: "rgba(255, 255, 255, 0.05)" }
                },
                y: { grid: { display: false } }
            }
        }
    });
}

function renderizarTablaModelos(modelos) {
    const tbody = document.getElementById("tbodyModelsTable");
    if (!tbody || !modelos) return;

    tbody.innerHTML = "";
    modelos.forEach(m => {
        const tr = document.createElement("tr");
        const esSeleccionado = m.estado === "SELECCIONADO";

        tr.innerHTML = `
            <td>
                <strong>${m.nombre}</strong>
                ${esSeleccionado ? '<span style="color: var(--cyan); font-size: 0.75rem; margin-left: 6px;">★ En Producción</span>' : ''}
            </td>
            <td><span class="tab-badge">${m.tipo}</span></td>
            <td><strong>${m.accuracy}%</strong></td>
            <td>${m.precision}%</td>
            <td>${m.recall}%</td>
            <td><strong>${m.f1_score}%</strong></td>
            <td>
                <span class="risk-badge ${esSeleccionado ? 'risk-bajo' : ''}">
                    ${m.estado}
                </span>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// ============================================================
// TABLA DE TRANSACCIONES EN VIVO
// ============================================================

async function cargarTransacciones(conFiltro = false) {
    const tbody = document.getElementById("tbodyTransactions");
    if (!tbody) return;

    const selectFilter = document.getElementById("selectFilterTx");
    const filtro = selectFilter ? selectFilter.value : "";

    try {
        let url = "/api/admin/transacciones?limit=50";
        if (filtro) url += `&resultado=${filtro}`;

        const res = await fetch(url);
        const data = await res.json();
        if (data.status === "success") {
            renderizarTablaTransacciones(data.transacciones, tbody);
        }
    } catch (err) {
        console.warn("Error al cargar transacciones:", err);
    }
}

function renderizarTablaTransacciones(lista, tbody) {
    if (!lista || lista.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 2rem;">No se encontraron registros.</td></tr>`;
        return;
    }

    tbody.innerHTML = "";
    lista.forEach(tx => {
        const tr = document.createElement("tr");

        let riskClass = "risk-bajo";
        if (tx.nivel_riesgo === "CRITICO") riskClass = "risk-critico";
        else if (tx.nivel_riesgo === "ALTO") riskClass = "risk-alto";
        else if (tx.nivel_riesgo === "MEDIO") riskClass = "risk-medio";

        let probColor = "#10B981";
        if (tx.probabilidad_fraude >= 80) probColor = "#EF4444";
        else if (tx.probabilidad_fraude >= 50) probColor = "#F59E0B";

        tr.innerHTML = `
            <td>#${tx.id_transaccion}</td>
            <td style="color: var(--text-secondary); font-size: 0.8rem;">${tx.fecha_hora}</td>
            <td><strong>${tx.usuario}</strong></td>
            <td><span class="tab-badge">${tx.producto}</span></td>
            <td><strong>S/ ${parseFloat(tx.monto).toFixed(2)}</strong></td>
            <td>
                <div class="prob-bar-cell">
                    <div class="prob-track">
                        <div class="prob-fill" style="width: ${tx.probabilidad_fraude}%; background-color: ${probColor};"></div>
                    </div>
                    <span>${tx.probabilidad_fraude}%</span>
                </div>
            </td>
            <td><span class="risk-badge ${riskClass}">${tx.nivel_riesgo}</span></td>
            <td>
                <span style="color: ${tx.resultado === 'APROBADA' ? '#10B981' : '#EF4444'}; font-weight: 700;">
                    ${tx.resultado}
                </span>
            </td>
            <td>
                <button class="btn-inspect-tx" onclick="abrirRadiografiaForense(${tx.id_transaccion})">
                    🔍 Radiografía
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filtrarTablaTransacciones() {
    const query = document.getElementById("inputSearchTx").value.toLowerCase();
    const rows = document.querySelectorAll("#tbodyTransactions tr");

    rows.forEach(r => {
        const text = r.textContent.toLowerCase();
        r.style.display = text.includes(query) ? "" : "none";
    });
}

// ============================================================
// RADIOGRAFÍA FORENSE DE TRANSACCIÓN (MODAL AUDITORÍA)
// ============================================================

async function abrirRadiografiaForense(idTx) {
    const modal = document.getElementById("modalForensic");
    const content = document.getElementById("forensicContent");
    const txIdTitle = document.getElementById("forensicTxId");

    if (txIdTitle) txIdTitle.textContent = idTx;
    if (modal) modal.style.display = "flex";
    if (content) content.innerHTML = `<div class="loading-state">Cargando diagnóstico forense...</div>`;

    try {
        const res = await fetch(`/api/admin/transacciones/${idTx}`);
        const data = await res.json();
        if (data.status === "success") {
            const tx = data.transaccion;
            const esFraude = tx.resultado === "SOSPECHOSA";

            content.innerHTML = `
                <!-- Veredicto Principal -->
                <div class="forensic-verdict-box ${esFraude ? '' : 'normal'}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="font-size: 1.15rem; color: ${esFraude ? '#EF4444' : '#10B981'}; margin-bottom: 0.2rem;">
                                Veredicto IA: ${esFraude ? 'POSIBLE FRAUDE DETECTADO' : 'TRANSACCIÓN NORMAL'}
                            </h4>
                            <p style="font-size: 0.85rem; color: #CBD5E1;">
                                Modelo evaluador: <strong>${tx.nombre_modelo || 'Gradient Boosting'}</strong> • 
                                Probabilidad de Fraude: <strong style="color: ${esFraude ? '#EF4444' : '#10B981'};">${tx.probabilidad_fraude}%</strong>
                            </p>
                        </div>
                        <span class="risk-badge ${esFraude ? 'risk-critico' : 'risk-bajo'}" style="font-size: 0.9rem; padding: 0.4rem 0.8rem;">
                            ${tx.nivel_alerta || (esFraude ? 'CRÍTICO' : 'BAJO')}
                        </span>
                    </div>
                </div>

                <!-- Grid de Variables Clave Analizadas -->
                <h4 style="color: white; margin-top: 0.5rem;">Variables Clave Analizadas por el Modelo</h4>
                <div class="forensic-grid">
                    <div class="forensic-metric-box">
                        <span>Monto de Operación</span>
                        <strong>S/ ${parseFloat(tx.monto).toFixed(2)}</strong>
                    </div>
                    <div class="forensic-metric-box">
                        <span>Monto Promedio Histórico</span>
                        <strong>S/ ${parseFloat(tx.monto_promedio_usuario || 45).toFixed(2)}</strong>
                    </div>
                    <div class="forensic-metric-box">
                        <span>Hora de Operación</span>
                        <strong>${tx.hora}:00 hrs ${tx.hora_inusual ? '⚠️ (Madrugada)' : '✓ (Habitual)'}</strong>
                    </div>
                    <div class="forensic-metric-box">
                        <span>Destinatario Nuevo</span>
                        <strong>${tx.destinatario_nuevo ? '⚠️ Sí (Riesgo)' : '✓ No (Conocido)'}</strong>
                    </div>
                    <div class="forensic-metric-box">
                        <span>Cambio de Dispositivo</span>
                        <strong>${tx.cambio_dispositivo ? '⚠️ Sí (Nuevo equipo)' : '✓ No (Habitual)'}</strong>
                    </div>
                    <div class="forensic-metric-box">
                        <span>Llamada Reciente (Vishing)</span>
                        <strong>${tx.llamada_reciente ? '⚠️ Sí (Llamada previa)' : '✓ No'}</strong>
                    </div>
                    <div class="forensic-metric-box">
                        <span>Velocidad de Operación</span>
                        <strong>${tx.velocidad_operacion} seg ${tx.velocidad_operacion < 12 ? '⚠️ (Anómala)' : '✓'}</strong>
                    </div>
                    <div class="forensic-metric-box">
                        <span>Distancia Geográfica</span>
                        <strong>${tx.distancia_ubicacion} km ${tx.ubicacion_inusual ? '⚠️ (Inusual)' : '✓'}</strong>
                    </div>
                </div>

                <!-- Descripción de Alerta si existe -->
                ${tx.desc_alerta ? `
                    <div style="background: rgba(255, 255, 255, 0.05); padding: 1rem; border-radius: 12px; border: 1px solid var(--border-card);">
                        <strong style="color: var(--cyan); font-size: 0.85rem; display: block; margin-bottom: 0.3rem;">Detalle de la Alerta:</strong>
                        <p style="font-size: 0.85rem; color: #E2E8F0;">${tx.desc_alerta}</p>
                    </div>
                ` : ''}
            `;
        }
    } catch (err) {
        content.innerHTML = `<div style="color: #EF4444; padding: 2rem;">Error al obtener la radiografía forense.</div>`;
    }
}

// ============================================================
// GESTIÓN DE ALERTAS DE FRAUDE
// ============================================================

async function cargarAlertas(conFiltro = false) {
    const container = document.getElementById("alertsCardsList");
    if (!container) return;

    const select = document.getElementById("selectFilterAlerts");
    const estado = select ? select.value : "PENDIENTE";

    try {
        let url = "/api/admin/alertas";
        if (estado) url += `?estado=${estado}`;

        const res = await fetch(url);
        const data = await res.json();
        if (data.status === "success") {
            renderizarListaAlertas(data.alertas, container);
        }
    } catch (err) {
        console.warn("Error al cargar alertas:", err);
    }
}

function renderizarListaAlertas(alertas, container) {
    if (!alertas || alertas.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 3rem; background: var(--bg-card); border-radius: 16px; color: var(--text-secondary);">
                🎉 No hay alertas bajo el filtro seleccionado.
            </div>
        `;
        return;
    }

    container.innerHTML = "";
    alertas.forEach(al => {
        const card = document.createElement("div");
        const esCritico = al.nivel === "CRITICO";
        card.className = `alert-item-card ${esCritico ? 'critico' : 'alto'}`;

        card.innerHTML = `
            <div class="alert-item-main">
                <div class="alert-top-row">
                    <span class="alert-id-tag">ALERTA #${al.id_alerta}</span>
                    <span class="risk-badge ${esCritico ? 'risk-critico' : 'risk-alto'}">${al.nivel} (${al.probabilidad_fraude || 88}%)</span>
                    <span class="tab-badge">${al.estado}</span>
                </div>
                <p class="alert-desc-text">${al.descripcion || 'Comportamiento atípico detectado en la operación.'}</p>
                <div class="alert-meta-info">
                    <span>👤 Usuario: <strong>${al.nombre} ${al.apellido}</strong></span>
                    <span>💰 Monto: <strong>S/ ${parseFloat(al.monto).toFixed(2)}</strong></span>
                    <span>📅 Fecha: <strong>${al.fecha_alerta}</strong></span>
                    <span>📦 Canal: <strong>${al.producto}</strong></span>
                </div>
            </div>
            
            <div class="alert-actions-group">
                ${al.estado === 'PENDIENTE' ? `
                    <button class="btn-action-alert btn-approve-alert" onclick="resolverAlerta(${al.id_alerta}, 'APROBAR')">
                        ✓ Aprobar Operación
                    </button>
                    <button class="btn-action-alert btn-confirm-alert" onclick="resolverAlerta(${al.id_alerta}, 'CONFIRMAR_FRAUDE')">
                        🚨 Confirmar Fraude
                    </button>
                    <button class="btn-action-alert btn-dismiss-alert" onclick="resolverAlerta(${al.id_alerta}, 'DESCARTAR')">
                        ✕ Descartar
                    </button>
                ` : `
                    <span style="font-size: 0.82rem; color: var(--text-muted); text-align: center;">
                        Resuelta como <strong>${al.estado}</strong>
                    </span>
                `}
            </div>
        `;

        container.appendChild(card);
    });
}

async function resolverAlerta(idAlerta, accion) {
    let motivo = "Validación de analista en consola";
    if (accion === "CONFIRMAR_FRAUDE") {
        if (!confirm("¿Confirmar fraude? Esto bloqueará de inmediato la cuenta del usuario para proteger su saldo.")) return;
        motivo = "Fraude confirmado por analista de ciberseguridad.";
    }

    try {
        const res = await fetch(`/api/admin/alertas/${idAlerta}/resolver`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ accion: accion, comentario: motivo })
        });
        const data = await res.json();
        if (data.status === "success") {
            cargarAlertas(false);
            cargarMetricas(false);
            cargarTransacciones(false);
        }
    } catch (err) {
        alert("Error al resolver la alerta.");
    }
}
