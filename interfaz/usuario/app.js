/**
 * Yape BCP - Lógica de Interfaz de Usuario
 * Conectado en tiempo real con Flask y Modelo de Machine Learning Antifraude
 * Soporta navegación por pestañas (Inicio, Movimientos, Analizar, Consejos, Más),
 * sistema de notificaciones, cambio de tema Claro/Oscuro y aislamiento de transacciones.
 */

let saldoOculto = false;
let saldoActual = 3125.00;
let pollingInterval = null;
let usuarioActivo = null;
try {
    const cached = sessionStorage.getItem("yape_active_user");
    if (cached) usuarioActivo = JSON.parse(cached);
} catch (e) {}

let listaTransaccionesUsuario = [];
let filtroHistorialActual = "TODOS";

function getAuthHeaders(extra = {}) {
    const headers = { ...extra };
    if (usuarioActivo && usuarioActivo.id_usuario) {
        headers["X-User-Id"] = String(usuarioActivo.id_usuario);
    }
    return headers;
}

document.addEventListener("DOMContentLoaded", async () => {
    inicializarReloj();
    inicializarTemaUsuario();
    
    const sesionValida = await verificarSesion();
    if (!sesionValida) return;

    inicializarNavegacionVistas();
    inicializarEventos();
    inicializarNotificaciones();
    inicializarModalesSeguridad();

    cargarPerfilUsuario();
    cargarTransacciones();
    cargarResumenSeguridad();
    cargarNotificaciones();

    // Sondeo automático cada 5 segundos para sincronización en vivo
    pollingInterval = setInterval(() => {
        cargarPerfilUsuario(false);
        cargarTransacciones(false);
        cargarNotificaciones(false);
    }, 5000);
});

// ============================================================
// 1. RELOJ Y TEMA CLARO / OSCURO
// ============================================================

function inicializarReloj() {
    const clockEl = document.getElementById("statusClock");
    if (!clockEl) return;
    function updateClock() {
        const now = new Date();
        const hrs = String(now.getHours()).padStart(2, '0');
        const mins = String(now.getMinutes()).padStart(2, '0');
        clockEl.textContent = `${hrs}:${mins}`;
    }
    updateClock();
    setInterval(updateClock, 30000);
}

function inicializarTemaUsuario() {
    const savedTheme = localStorage.getItem("yape_user_theme") || "dark";
    aplicarTemaUsuario(savedTheme);

    const btnThemeToggle = document.getElementById("btnThemeToggleUser");
    const btnSettingsTheme = document.getElementById("btnToggleThemeInSettings");
    const btnHeaderTheme = document.getElementById("btnThemeToggleHeader");

    const alternar = () => {
        const actual = document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
        const nuevo = actual === "dark" ? "light" : "dark";
        aplicarTemaUsuario(nuevo);
        localStorage.setItem("yape_user_theme", nuevo);
    };

    if (btnThemeToggle) btnThemeToggle.addEventListener("click", alternar);
    if (btnSettingsTheme) btnSettingsTheme.addEventListener("click", alternar);
    if (btnHeaderTheme) btnHeaderTheme.addEventListener("click", alternar);
}

function aplicarTemaUsuario(theme) {
    const isLight = theme === "light";
    document.documentElement.setAttribute("data-theme", isLight ? "light" : "dark");
    document.body.classList.toggle("theme-light", isLight);
    document.body.classList.toggle("theme-dark", !isLight);

    const iconEl = document.getElementById("userThemeIcon");
    const labelEl = document.getElementById("userThemeLabel");
    const settingsLabel = document.getElementById("settingsThemeStatus");
    const headerIcon = document.getElementById("headerThemeIcon");

    if (iconEl) iconEl.textContent = isLight ? "☀️" : "🌙";
    if (labelEl) labelEl.textContent = isLight ? "Modo Claro" : "Modo Oscuro";
    if (settingsLabel) settingsLabel.textContent = isLight ? "Claro" : "Oscuro";
    if (headerIcon) headerIcon.textContent = isLight ? "☀️" : "🌙";
}

// ============================================================
// 2. NAVEGACIÓN ENTRE PESTAÑAS (INICIO, MOVIMIENTOS, ANALIZAR...)
// ============================================================

function inicializarNavegacionVistas() {
    const tabs = document.querySelectorAll(".nav-tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const targetViewId = tab.getAttribute("data-target");
            cambiarVista(targetViewId);
        });
    });

    // Enlace directo desde botón "Historial" en Inicio
    const btnHistorial = document.getElementById("btnHistorial");
    if (btnHistorial) {
        btnHistorial.addEventListener("click", () => {
            cambiarVista("viewMovimientos");
        });
    }

    // Enlace desde la tarjeta de protección en Inicio hacia "Analizar"
    const btnGoToSecurity = document.getElementById("btnGoToSecurityCard");
    if (btnGoToSecurity) {
        btnGoToSecurity.addEventListener("click", () => {
            cambiarVista("viewAnalizar");
        });
    }

    // Enlace "Ver todos" en consejos
    const btnLinkAllConsejos = document.getElementById("btnLinkAllConsejos");
    if (btnLinkAllConsejos) {
        btnLinkAllConsejos.addEventListener("click", () => {
            cambiarVista("viewConsejos");
        });
    }
}

function cambiarVista(viewId) {
    if (!viewId) return;

    // Ocultar todas las vistas y remover clase activa de tabs
    document.querySelectorAll(".app-view").forEach(v => v.classList.remove("active"));
    document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));

    // Activar vista seleccionada
    const targetView = document.getElementById(viewId);
    if (targetView) {
        targetView.classList.add("active");
        const appScreen = document.getElementById("appScreen");
        if (appScreen) appScreen.scrollTop = 0;
    }

    // Activar tab correspondiente
    const activeTab = document.querySelector(`.nav-tab[data-target="${viewId}"]`);
    if (activeTab) {
        activeTab.classList.add("active");
    }

    // Actualizar datos según la vista
    if (viewId === "viewMovimientos") {
        renderizarHistorialCompleto();
    } else if (viewId === "viewAnalizar") {
        cargarResumenSeguridad();
    }
}

// ============================================================
// 3. AUTENTICACIÓN Y SESIÓN
// ============================================================

async function verificarSesion() {
    try {
        const res = await fetch("/api/auth/sesion", { headers: getAuthHeaders() });
        const data = await res.json();
        if (!data.autenticado) {
            sessionStorage.removeItem("yape_active_user");
            window.location.href = "/usuario/login";
            return false;
        }

        usuarioActivo = data.usuario;
        try {
            sessionStorage.setItem("yape_active_user", JSON.stringify(data.usuario));
        } catch (e) {}

        if (data.usuario && data.usuario.nombre) {
            const firstName = data.usuario.primer_nombre || data.usuario.nombre.split(' ')[0];
            const greetingEl = document.getElementById("userGreeting");
            if (greetingEl) greetingEl.textContent = `¡Hola, ${firstName}!`;

            const parts = data.usuario.nombre.split(' ');
            const initials = (parts[0][0] + (parts[1] ? parts[1][0] : '')).toUpperCase();
            
            const avatarCircle = document.getElementById("userAvatarCircle");
            if (avatarCircle) avatarCircle.textContent = initials;

            const avatarLg = document.getElementById("avatarCircleLarge");
            if (avatarLg) avatarLg.textContent = initials;

            const settingsFullName = document.getElementById("settingsFullName");
            if (settingsFullName) settingsFullName.textContent = data.usuario.nombre;

            const settingsEmail = document.getElementById("settingsEmail");
            if (settingsEmail) settingsEmail.textContent = data.usuario.correo || "usuario@correo.com";
        }
        return true;
    } catch (err) {
        return true;
    }
}

// ============================================================
// 4. EVENTOS DE INTERFAZ Y MODALES
// ============================================================

function inicializarEventos() {
    // Cerrar sesión (solo desde el botón en la sección Más)
    const btnLogoutFull = document.getElementById("btnLogoutFull");
    const handleLogout = async () => {
        if (confirm("¿Deseas cerrar tu sesión de Yape?")) {
            sessionStorage.removeItem("yape_active_user");
            await fetch("/api/auth/logout", { method: "POST", headers: getAuthHeaders() });
            window.location.href = "/usuario/login";
        }
    };
    if (btnLogoutFull) btnLogoutFull.addEventListener("click", handleLogout);

    // Toggle modo expandido / teléfono
    const btnToggleDevice = document.getElementById("btnToggleDevice");
    const deviceWrapper = document.getElementById("deviceWrapper");
    if (btnToggleDevice && deviceWrapper) {
        btnToggleDevice.addEventListener("click", () => {
            deviceWrapper.classList.toggle("expanded");
            btnToggleDevice.textContent = deviceWrapper.classList.contains("expanded") 
                ? "📱 Vista Teléfono" 
                : "📱 Vista Móvil / Expandida";
        });
    }

    // Ocultar / Mostrar Saldo
    const btnToggleBalance = document.getElementById("btnToggleBalance");
    if (btnToggleBalance) {
        btnToggleBalance.addEventListener("click", () => {
            saldoOculto = !saldoOculto;
            renderizarSaldo();
        });
    }

    // Modal Mi QR (Cobrar)
    const btnCobrar = document.getElementById("btnCobrar");
    const modalQR = document.getElementById("modalQR");
    const btnCloseModalQR = document.getElementById("btnCloseModalQR");
    if (btnCobrar && modalQR) {
        btnCobrar.addEventListener("click", () => {
            // Rellenar datos del usuario en el QR
            if (usuarioActivo) {
                const qrName = document.getElementById("qrUserName");
                const qrAvatar = document.getElementById("qrAvatarCircle");
                if (qrName && usuarioActivo.nombre) qrName.textContent = usuarioActivo.nombre;
                if (qrAvatar && usuarioActivo.nombre) {
                    const parts = usuarioActivo.nombre.split(' ');
                    qrAvatar.textContent = (parts[0]?.[0] || '') + (parts[1]?.[0] || '');
                }
            }
            modalQR.style.display = "flex";
        });
    }
    if (btnCloseModalQR && modalQR) {
        btnCloseModalQR.addEventListener("click", () => { modalQR.style.display = "none"; });
    }
    document.getElementById("btnShareQR")?.addEventListener("click", () => {
        alert("📱 En producción compartiría tu QR vía WhatsApp, correo o descarga.");
    });

    // Modal Servicios
    const btnServicios = document.getElementById("btnServicios");
    const modalServicios = document.getElementById("modalServicios");
    const btnCloseModalServicios = document.getElementById("btnCloseModalServicios");
    if (btnServicios && modalServicios) {
        btnServicios.addEventListener("click", () => { modalServicios.style.display = "flex"; });
    }
    if (btnCloseModalServicios && modalServicios) {
        btnCloseModalServicios.addEventListener("click", () => { modalServicios.style.display = "none"; });
    }
    // Servicios individuales — simulación de clic
    ["svcLuz","svcAgua","svcCelular","svcCable","svcInternet","svcSeguro"].forEach(id => {
        document.getElementById(id)?.addEventListener("click", (e) => {
            const name = e.currentTarget.querySelector("span")?.textContent || id;
            alert(`💡 Servicio "${name}" seleccionado.\nEn producción se abriría el formulario de pago BCP.`);
        });
    });

    // Modal Yapear
    const btnOpenYapear = document.getElementById("btnOpenYapear");
    const modalYapear = document.getElementById("modalYapear");
    const btnCloseModalYapear = document.getElementById("btnCloseModalYapear");

    if (btnOpenYapear && modalYapear) {
        btnOpenYapear.addEventListener("click", () => {
            modalYapear.style.display = "flex";
            actualizarBotonSubmit();
        });
    }

    if (btnCloseModalYapear && modalYapear) {
        btnCloseModalYapear.addEventListener("click", () => {
            modalYapear.style.display = "none";
        });
    }

    // Cierre al hacer click en el fondo del modal
    document.querySelectorAll(".modal-overlay").forEach(m => {
        m.addEventListener("click", (e) => {
            if (e.target === m) m.style.display = "none";
        });
    });

    // Contact Pills
    const contactPills = document.querySelectorAll(".contact-pill");
    const inputDestinatario = document.getElementById("inputDestinatario");
    contactPills.forEach(pill => {
        pill.addEventListener("click", () => {
            contactPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            const phone = pill.getAttribute("data-phone");
            const name = pill.getAttribute("data-name");
            if (inputDestinatario) {
                inputDestinatario.value = `${name} (${phone})`;
            }
        });
    });

    // Botones de montos rápidos (+10, +20, +50, +100)
    const quickAmtBtns = document.querySelectorAll(".btn-quick-amt");
    const inputMonto = document.getElementById("inputMonto");
    quickAmtBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const addVal = parseFloat(btn.getAttribute("data-val")) || 0;
            const currentVal = parseFloat(inputMonto.value) || 0;
            inputMonto.value = (currentVal + addVal).toFixed(2);
            actualizarBotonSubmit();
        });
    });

    if (inputMonto) {
        inputMonto.addEventListener("input", actualizarBotonSubmit);
    }

    // Formulario Yapear
    const formYapear = document.getElementById("formYapear");
    if (formYapear) {
        formYapear.addEventListener("submit", procesarYapeo);
    }

    // Cierre de Voucher y Alerta
    document.getElementById("btnCloseVoucher")?.addEventListener("click", () => {
        document.getElementById("modalVoucher").style.display = "none";
    });

    document.getElementById("btnCloseAlert")?.addEventListener("click", () => {
        document.getElementById("modalSecurityAlert").style.display = "none";
    });

    // Botón refrescar
    document.getElementById("btnRefreshTx")?.addEventListener("click", () => {
        cargarPerfilUsuario(true);
        cargarTransacciones(true);
    });

    // Buscador y filtros en Historial
    const searchInput = document.getElementById("inputSearchHistory");
    if (searchInput) {
        searchInput.addEventListener("input", () => {
            renderizarHistorialCompleto();
        });
    }

    const filterPills = document.querySelectorAll(".filter-pill");
    filterPills.forEach(pill => {
        pill.addEventListener("click", () => {
            filterPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            filtroHistorialActual = pill.getAttribute("data-filter") || "TODOS";
            renderizarHistorialCompleto();
        });
    });

    // Botones de simulación rápida
    configurarBotonesPrueba();
}

function actualizarBotonSubmit() {
    const inputMonto = document.getElementById("inputMonto");
    const btnYapearText = document.getElementById("btnYapearText");
    if (inputMonto && btnYapearText) {
        const val = parseFloat(inputMonto.value) || 0;
        btnYapearText.textContent = `¡Yapear S/ ${val.toFixed(2)}!`;
    }
}

function configurarBotonesPrueba() {
    const modalYapear = document.getElementById("modalYapear");
    const inputDestinatario = document.getElementById("inputDestinatario");
    const inputMonto = document.getElementById("inputMonto");
    const inputNota = document.getElementById("inputNota");
    const chkSimularFraude = document.getElementById("chkSimularFraude");
    const chkDestNuevo = document.getElementById("chkDestNuevo");
    const chkHoraInusual = document.getElementById("chkHoraInusual");
    const chkCambioDisp = document.getElementById("chkCambioDisp");

    // Prueba 1: Yapeo Normal (S/ 25)
    document.getElementById("btnTestNormal")?.addEventListener("click", () => {
        if (modalYapear) modalYapear.style.display = "flex";
        if (inputDestinatario) inputDestinatario.value = "María Gómez (987 654 321)";
        if (inputMonto) inputMonto.value = "25.00";
        if (inputNota) inputNota.value = "Almuerzo de trabajo";
        if (chkSimularFraude) chkSimularFraude.checked = false;
        if (chkDestNuevo) chkDestNuevo.checked = false;
        if (chkHoraInusual) chkHoraInusual.checked = false;
        if (chkCambioDisp) chkCambioDisp.checked = false;
        actualizarBotonSubmit();
    });

    // Prueba 2: Monto Atípico (S/ 750)
    document.getElementById("btnTestWarning")?.addEventListener("click", () => {
        if (modalYapear) modalYapear.style.display = "flex";
        if (inputDestinatario) inputDestinatario.value = "Carlos Quispe (912 345 678)";
        if (inputMonto) inputMonto.value = "750.00";
        if (inputNota) inputNota.value = "Pago de cuota";
        if (chkSimularFraude) chkSimularFraude.checked = false;
        if (chkDestNuevo) chkDestNuevo.checked = true;
        if (chkHoraInusual) chkHoraInusual.checked = false;
        if (chkCambioDisp) chkCambioDisp.checked = false;
        actualizarBotonSubmit();
    });

    // Prueba 3: Intento de Fraude Crítico (S/ 4,200)
    document.getElementById("btnTestFraud")?.addEventListener("click", () => {
        if (modalYapear) modalYapear.style.display = "flex";
        if (inputDestinatario) inputDestinatario.value = "Destinatario Desconocido (955 888 999)";
        if (inputMonto) inputMonto.value = "4200.00";
        if (inputNota) inputNota.value = "Transferencia urgente";
        if (chkSimularFraude) chkSimularFraude.checked = true;
        if (chkDestNuevo) chkDestNuevo.checked = true;
        if (chkHoraInusual) chkHoraInusual.checked = true;
        if (chkCambioDisp) chkCambioDisp.checked = true;
        actualizarBotonSubmit();
    });
}

// ============================================================
// 5. SISTEMA DE NOTIFICACIONES (CAMPANA FUNCIONAL)
// ============================================================

function inicializarNotificaciones() {
    const modalNotif = document.getElementById("modalNotifications");
    const btnClose = document.getElementById("btnCloseModalNotif");
    const btnMarkRead = document.getElementById("btnMarkAllRead");

    // Todos los botones que abren notificaciones
    document.querySelectorAll(".btn-notifications-trigger").forEach(btn => {
        btn.addEventListener("click", () => {
            if (modalNotif) modalNotif.style.display = "flex";
            cargarNotificaciones(true);
        });
    });

    if (btnClose && modalNotif) {
        btnClose.addEventListener("click", () => {
            modalNotif.style.display = "none";
        });
    }

    if (btnMarkRead) {
        btnMarkRead.addEventListener("click", async () => {
            await fetch("/api/usuario/notificaciones/marcar-leidas", { method: "POST", headers: getAuthHeaders() });
            document.querySelectorAll(".notif-card-item").forEach(item => item.classList.remove("unread"));
            document.querySelectorAll(".notif-badge-dot").forEach(b => b.style.display = "none");
            const unreadCount = document.getElementById("notifUnreadBadge");
            if (unreadCount) unreadCount.textContent = "0 nuevas";
        });
    }
}

async function cargarNotificaciones(mostrarAnimacion = false) {
    const container = document.getElementById("notificationsListContainer");
    const unreadCountBadge = document.getElementById("notifUnreadBadge");
    const badgeDots = document.querySelectorAll(".notif-badge-dot");

    try {
        const res = await fetch("/api/usuario/notificaciones", { headers: getAuthHeaders() });
        const data = await res.json();

        if (data.status === "success") {
            const noLeidas = data.no_leidas || 0;

            badgeDots.forEach(dot => {
                dot.style.display = noLeidas > 0 ? "block" : "none";
            });

            if (unreadCountBadge) {
                unreadCountBadge.textContent = noLeidas > 0 ? `${noLeidas} nuevas` : "Al día";
            }

            if (container) {
                if (!data.notificaciones || data.notificaciones.length === 0) {
                    container.innerHTML = `
                        <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
                            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎉</div>
                            <p>No tienes notificaciones pendientes.</p>
                        </div>
                    `;
                    return;
                }

                container.innerHTML = "";
                data.notificaciones.forEach(notif => {
                    const card = document.createElement("div");
                    card.className = `notif-card-item ${notif.leida ? '' : 'unread'}`;

                    card.innerHTML = `
                        <div class="notif-card-top">
                            <span class="notif-tag">${notif.badge || notif.tipo}</span>
                            <span class="notif-time">${notif.fecha}</span>
                        </div>
                        <strong class="notif-title">${notif.titulo}</strong>
                        <p class="notif-desc">${notif.mensaje}</p>
                    `;
                    container.appendChild(card);
                });
            }
        }
    } catch (err) {
        console.warn("Error al cargar notificaciones:", err);
    }
}

// ============================================================
// 6. MODALES DE IMAGEN 3 ("YAPE SEGURO")
// ============================================================

function inicializarModalesSeguridad() {
    // Compromiso
    const modalCompromiso = document.getElementById("modalCompromiso");
    document.getElementById("btnOpenCompromiso")?.addEventListener("click", () => {
        if (modalCompromiso) modalCompromiso.style.display = "flex";
    });
    document.getElementById("btnCloseCompromiso")?.addEventListener("click", () => {
        if (modalCompromiso) modalCompromiso.style.display = "none";
    });

    // Monitoreo
    const modalMonitoreo = document.getElementById("modalMonitoreo");
    document.getElementById("btnOpenMonitoreo")?.addEventListener("click", () => {
        if (modalMonitoreo) modalMonitoreo.style.display = "flex";
    });
    document.getElementById("btnCloseMonitoreo")?.addEventListener("click", () => {
        if (modalMonitoreo) modalMonitoreo.style.display = "none";
    });

    // Detección Fraude
    const modalDeteccion = document.getElementById("modalDeteccion");
    document.getElementById("btnOpenDeteccion")?.addEventListener("click", () => {
        if (modalDeteccion) modalDeteccion.style.display = "flex";
    });
    document.getElementById("btnCloseDeteccion")?.addEventListener("click", () => {
        if (modalDeteccion) modalDeteccion.style.display = "none";
    });

    // Ingeniería Social
    const modalIngenieria = document.getElementById("modalIngenieria");
    document.getElementById("btnOpenIngenieria")?.addEventListener("click", () => {
        if (modalIngenieria) modalIngenieria.style.display = "flex";
    });
    document.getElementById("btnCloseIngenieria")?.addEventListener("click", () => {
        if (modalIngenieria) modalIngenieria.style.display = "none";
    });

    // Yape PIN
    const modalPin = document.getElementById("modalPin");
    const openPin = () => { if (modalPin) modalPin.style.display = "flex"; };
    document.getElementById("btnOpenPinModal")?.addEventListener("click", openPin);
    document.getElementById("btnSettingsPin")?.addEventListener("click", openPin);

    document.getElementById("btnClosePinModal")?.addEventListener("click", () => {
        if (modalPin) modalPin.style.display = "none";
    });
    document.getElementById("btnConfirmPinDone")?.addEventListener("click", () => {
        if (modalPin) modalPin.style.display = "none";
        alert("✓ Yape PIN activo y sincronizado con tu cuenta.");
    });
}

// ============================================================
// 7. CARGA DE DATOS: PERFIL, RESUMEN Y TRANSACCIONES
// ============================================================

async function cargarPerfilUsuario(mostrarNotif = false) {
    try {
        const res = await fetch("/api/usuario/perfil", { headers: getAuthHeaders() });
        const data = await res.json();
        if (data.status === "success") {
            const u = data.usuario;
            saldoActual = parseFloat(u.cuenta.saldo);
            renderizarSaldo();

            const accEl = document.getElementById("accountNumberDisplay");
            if (accEl) accEl.textContent = `Cuenta BCP: ${u.cuenta.numero_cuenta}`;

            const pillEl = document.getElementById("accountStatusPill");
            const textEl = document.getElementById("accountStatusText");
            if (pillEl && textEl) {
                if (u.cuenta.estado === "BLOQUEADA") {
                    pillEl.className = "account-status-pill blocked";
                    textEl.textContent = "Cuenta Bloqueada";
                } else {
                    pillEl.className = "account-status-pill";
                    textEl.textContent = "Cuenta Activa";
                }
            }

            const devEl = document.getElementById("deviceInfoText");
            if (devEl && u.dispositivo) {
                devEl.textContent = `Dispositivo: ${u.dispositivo.modelo} • Modelo ML Gradient Boosting Activo`;
            }

            const setDev = document.getElementById("settingsDeviceModel");
            if (setDev && u.dispositivo) {
                setDev.textContent = `${u.dispositivo.modelo} • ${u.dispositivo.so}`;
            }
        }
    } catch (err) {
        console.warn("Error consultando perfil de usuario:", err);
    }
}

function renderizarSaldo() {
    const el = document.getElementById("balanceAmount");
    if (!el) return;
    if (saldoOculto) {
        el.textContent = "••••••";
    } else {
        el.textContent = saldoActual.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
}

async function cargarResumenSeguridad() {
    try {
        const res = await fetch("/api/usuario/seguridad-resumen", { headers: getAuthHeaders() });
        const data = await res.json();
        if (data.status === "success") {
            const elCount = document.getElementById("seguroAnalyzedCount");
            if (elCount) elCount.textContent = Number(data.transacciones_analizadas).toLocaleString();

            const elGrowth = document.getElementById("seguroGrowthBadge");
            if (elGrowth) elGrowth.textContent = data.crecimiento_semana || "↑ 12%";

            const elRiskText = document.getElementById("seguroRiskLevelText");
            if (elRiskText) {
                elRiskText.textContent = data.riesgo_detectado;
                elRiskText.style.color = data.riesgo_detectado === "Bajo" ? "#10B981" : "#F59E0B";
            }

            const elRiskDesc = document.getElementById("seguroRiskDescText");
            if (elRiskDesc) elRiskDesc.textContent = data.descripcion_riesgo;
        }
    } catch (e) {
        console.warn("Error al cargar resumen de seguridad:", e);
    }
}

async function cargarTransacciones(conAnimacion = true) {
    const previewContainer = document.getElementById("txListContainer");
    try {
        const res = await fetch("/api/usuario/transacciones", { headers: getAuthHeaders() });
        const data = await res.json();
        if (data.status === "success") {
            listaTransaccionesUsuario = data.transacciones || [];
            
            // Renderizar vista previa (en Inicio)
            if (previewContainer) {
                renderizarListaTransacciones(listaTransaccionesUsuario.slice(0, 4), previewContainer);
            }

            // Renderizar vista completa (en Movimientos)
            renderizarHistorialCompleto();
        }
    } catch (err) {
        if (previewContainer) {
            previewContainer.innerHTML = `<div class="tx-loading" style="color: #EF4444;">Error al conectar con la base de datos.</div>`;
        }
    }
}

function renderizarListaTransacciones(transacciones, container) {
    if (!transacciones || transacciones.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 1.5rem 1rem; color: var(--text-muted);">
                <p>No tienes movimientos recientes.</p>
                <span style="font-size: 0.8rem; color: var(--yape-cyan);">¡Realiza tu primer yapeo arriba!</span>
            </div>
        `;
        return;
    }

    container.innerHTML = "";
    transacciones.forEach(tx => {
        const item = document.createElement("div");
        item.className = "tx-item";

        let iconType = "tx-icon-yape";
        let iconSymbol = "Y";
        if (tx.producto.toLowerCase().includes("servicio")) {
            iconType = "tx-icon-service";
            iconSymbol = "⚡";
        } else if (tx.producto.toLowerCase().includes("transferencia")) {
            iconType = "tx-icon-transfer";
            iconSymbol = "⇄";
        }

        let statusClass = "status-approved";
        let statusText = "Aprobada";

        if (tx.resultado === "SOSPECHOSA") {
            if (tx.alerta && tx.alerta.estado === "PENDIENTE") {
                statusClass = "status-pending";
                statusText = "En Revisión";
            } else if (tx.alerta && tx.alerta.estado === "CONFIRMADA") {
                statusClass = "status-suspicious";
                statusText = "Bloqueada";
            } else {
                statusClass = "status-suspicious";
                statusText = "Pausada";
            }
        }

        const fechaFormat = tx.fecha_hora ? tx.fecha_hora.substring(0, 16) : "Hoy";

        item.innerHTML = `
            <div class="tx-left">
                <div class="tx-icon-pill ${iconType}">${iconSymbol}</div>
                <div class="tx-details-col">
                    <span class="tx-title">${tx.producto}</span>
                    <span class="tx-date">${fechaFormat}</span>
                </div>
            </div>
            <div class="tx-right">
                <span class="tx-amount">- S/ ${parseFloat(tx.monto).toFixed(2)}</span>
                <span class="tx-status-badge ${statusClass}">${statusText}</span>
            </div>
        `;

        container.appendChild(item);
    });
}

function renderizarHistorialCompleto() {
    const container = document.getElementById("fullHistoryContainer");
    if (!container) return;

    const searchInput = document.getElementById("inputSearchHistory");
    const query = searchInput ? searchInput.value.trim().toLowerCase() : "";

    let filtradas = listaTransaccionesUsuario;

    // Filtro de estado
    if (filtroHistorialActual !== "TODOS") {
        filtradas = filtradas.filter(tx => tx.resultado === filtroHistorialActual);
    }

    // Filtro de búsqueda
    if (query) {
        filtradas = filtradas.filter(tx => 
            tx.producto.toLowerCase().includes(query) ||
            String(tx.monto).includes(query) ||
            (tx.fecha_hora && tx.fecha_hora.includes(query))
        );
    }

    if (filtradas.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 3rem 1.5rem; background: var(--bg-card); border-radius: 20px; border: 1px solid var(--border-color);">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">💳</div>
                <h4 style="color: var(--text-primary); margin-bottom: 0.35rem;">Sin movimientos encontrados</h4>
                <p style="color: var(--text-secondary); font-size: 0.85rem;">
                    ${listaTransaccionesUsuario.length === 0 ? "Aún no has realizado transferencias con esta cuenta." : "No hay resultados que coincidan con tu búsqueda."}
                </p>
            </div>
        `;
        return;
    }

    renderizarListaTransacciones(filtradas, container);
}

// ============================================================
// 8. PROCESAR YAPEO CON MACHINE LEARNING
// ============================================================

async function procesarYapeo(e) {
    e.preventDefault();

    const btnSubmit = document.getElementById("btnSubmitYapear");
    const btnText = document.getElementById("btnYapearText");
    const spinner = document.getElementById("spinnerYapear");

    const inputDestinatario = document.getElementById("inputDestinatario");
    const inputMonto = document.getElementById("inputMonto");
    const inputNota = document.getElementById("inputNota");

    const chkSimularFraude = document.getElementById("chkSimularFraude");
    const chkDestNuevo = document.getElementById("chkDestNuevo");
    const chkHoraInusual = document.getElementById("chkHoraInusual");
    const chkCambioDisp = document.getElementById("chkCambioDisp");

    const monto = parseFloat(inputMonto.value);
    const destinatario = inputDestinatario.value.trim();
    const mensaje = inputNota.value.trim();

    if (isNaN(monto) || monto <= 0) {
        alert("Por favor ingresa un monto válido.");
        return;
    }

    btnSubmit.disabled = true;
    btnText.textContent = "Evaluando seguridad con IA...";
    spinner.style.display = "inline-block";

    const payload = {
        user_id: usuarioActivo ? usuarioActivo.id_usuario : undefined,
        monto: monto,
        destinatario: destinatario,
        mensaje: mensaje,
        simular_fraude: chkSimularFraude ? chkSimularFraude.checked : false,
        destinatario_nuevo: (chkDestNuevo && chkDestNuevo.checked) ? 1 : 0,
        hora_inusual: (chkHoraInusual && chkHoraInusual.checked) ? 1 : 0,
        cambio_dispositivo: (chkCambioDisp && chkCambioDisp.checked) ? 1 : 0
    };

    try {
        const res = await fetch("/api/usuario/yapear", {
            method: "POST",
            headers: getAuthHeaders({ "Content-Type": "application/json" }),
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        document.getElementById("modalYapear").style.display = "none";

        if (res.status === 403 || data.status === "blocked") {
            alert(data.mensaje || "Tu cuenta está bloqueada por seguridad. Contacta con soporte BCP.");
            cargarPerfilUsuario();
            return;
        }

        if (res.status === 400) {
            alert(data.mensaje || "Error al realizar la operación.");
            return;
        }

        if (data.status === "success") {
            saldoActual = parseFloat(data.nuevo_saldo);
            renderizarSaldo();

            document.getElementById("voucherAmount").textContent = `S/ ${monto.toFixed(2)}`;
            document.getElementById("voucherDestinatario").textContent = destinatario;
            document.getElementById("voucherFecha").textContent = data.fecha_hora || new Date().toLocaleString();
            document.getElementById("voucherCodigo").textContent = data.codigo_operacion || `YP-${Math.floor(100000 + Math.random()*900000)}`;
            document.getElementById("voucherMensaje").textContent = mensaje || "Sin mensaje";

            document.getElementById("modalVoucher").style.display = "flex";

        } else if (data.status === "suspicious") {
            const modalAlert = document.getElementById("modalSecurityAlert");
            document.getElementById("alertRiskLevel").textContent = `${data.nivel_riesgo} (${data.probabilidad_fraude}%)`;
            
            const riskBar = document.getElementById("alertRiskBar");
            if (riskBar) riskBar.style.width = `${Math.min(data.probabilidad_fraude, 100)}%`;

            const factorsUl = document.getElementById("alertFactorsList");
            if (factorsUl) {
                factorsUl.innerHTML = "";
                if (data.factores && data.factores.length > 0) {
                    data.factores.forEach(f => {
                        const li = document.createElement("li");
                        li.textContent = f;
                        factorsUl.appendChild(li);
                    });
                } else {
                    const li = document.createElement("li");
                    li.textContent = "Desviación multivariable del perfil de usuario habitual.";
                    factorsUl.appendChild(li);
                }
            }

            modalAlert.style.display = "flex";
        }

        cargarTransacciones();
        cargarPerfilUsuario();
        cargarResumenSeguridad();
        cargarNotificaciones();

    } catch (err) {
        alert("Error de conexión con el servidor antifraude.");
    } finally {
        btnSubmit.disabled = false;
        btnText.textContent = `¡Yapear S/ ${monto.toFixed(2)}!`;
        spinner.style.display = "none";
    }
}
