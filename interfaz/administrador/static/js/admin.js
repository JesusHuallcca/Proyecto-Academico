/**
 * SISTEMA ANTIFRAUDE YAPE - LÓGICA FRONTEND
 * Navegación móvil, modales, interactividad de formularios y gráficos
 */

document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  initMobileNavigation();
  initPasswordToggle();
  initFormCalculations();
  initPresets();
  initModals();
});

/* ==========================================================================
   0. TEMA CLARO / OSCURO (THEME SWITCHER)
   ========================================================================== */
function initThemeToggle() {
  const btnToggle = document.getElementById('btnThemeToggleAdmin');
  const iconIndicator = document.getElementById('themeIconIndicator');
  const textLabel = document.getElementById('themeTextLabel');

  // Obtener tema actual guardado o por defecto dark
  const currentTheme = localStorage.getItem('admin_theme') || 'dark';
  applyTheme(currentTheme);

  if (btnToggle) {
    btnToggle.addEventListener('click', () => {
      const activeTheme = document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
      const newTheme = activeTheme === 'dark' ? 'light' : 'dark';
      applyTheme(newTheme);
      localStorage.setItem('admin_theme', newTheme);
    });
  }

  function applyTheme(theme) {
    if (theme === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
      document.body.classList.add('theme-light');
      if (iconIndicator) iconIndicator.textContent = '☀️';
      if (textLabel) textLabel.textContent = 'Modo Claro';
    } else {
      document.documentElement.setAttribute('data-theme', 'dark');
      document.body.classList.remove('theme-light');
      if (iconIndicator) iconIndicator.textContent = '🌙';
      if (textLabel) textLabel.textContent = 'Modo Oscuro';
    }

    // Actualizar colores de gráficos Chart.js si están inicializados
    if (window.Chart && typeof window.Chart.instances === 'object') {
      const isLight = theme === 'light';
      const textColor = isLight ? '#475569' : '#94A3B8';
      const gridColor = isLight ? 'rgba(0, 0, 0, 0.06)' : 'rgba(255, 255, 255, 0.05)';

      Object.values(window.Chart.instances).forEach(chart => {
        if (chart.options && chart.options.scales) {
          ['x', 'y'].forEach(axis => {
            if (chart.options.scales[axis]) {
              if (chart.options.scales[axis].ticks) chart.options.scales[axis].ticks.color = textColor;
              if (chart.options.scales[axis].grid) chart.options.scales[axis].grid.color = gridColor;
            }
          });
        }
        if (chart.options && chart.options.plugins && chart.options.plugins.legend) {
          if (chart.options.plugins.legend.labels) chart.options.plugins.legend.labels.color = textColor;
        }
        chart.update();
      });
    }
  }
}

/* ==========================================================================
   1. NAVEGACIÓN MÓVIL Y SIDEBAR
   ========================================================================== */
function initMobileNavigation() {
  const toggleBtn = document.getElementById('menuToggleBtn');
  const sidebar = document.getElementById('appSidebar');

  if (!toggleBtn || !sidebar) return;

  toggleBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    sidebar.classList.toggle('open');
  });

  // Cerrar al hacer click fuera del sidebar en móvil
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768 && sidebar.classList.contains('open')) {
      if (!sidebar.contains(e.target) && e.target !== toggleBtn) {
        sidebar.classList.remove('open');
      }
    }
  });

  // Cerrar al presionar Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sidebar.classList.contains('open')) {
      sidebar.classList.remove('open');
    }
  });
}

/* ==========================================================================
   2. TOGGLE MOSTRAR / OCULTAR CONTRASEÑA
   ========================================================================== */
function initPasswordToggle() {
  const toggleBtn = document.getElementById('togglePasswordBtn');
  const passwordInput = document.getElementById('passwordInput');

  if (!toggleBtn || !passwordInput) return;

  toggleBtn.addEventListener('click', () => {
    const isPassword = passwordInput.type === 'password';
    passwordInput.type = isPassword ? 'text' : 'password';

    // Cambiar icono SVG
    toggleBtn.innerHTML = isPassword ? `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
        <line x1="1" y1="1" x2="23" y2="23"></line>
      </svg>
    ` : `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
        <circle cx="12" cy="12" r="3"></circle>
      </svg>
    `;
  });
}

/* ==========================================================================
   3. CÁLCULO DINÁMICO DE SALDO POSTERIOR
   ========================================================================== */
function initFormCalculations() {
  const inputMonto = document.getElementById('input_monto');
  const inputSaldoAnterior = document.getElementById('input_saldo_anterior');
  const inputSaldoPosterior = document.getElementById('input_saldo_posterior');

  if (!inputMonto || !inputSaldoAnterior || !inputSaldoPosterior) return;

  function recalcularSaldo() {
    const monto = parseFloat(inputMonto.value) || 0;
    const saldoAnt = parseFloat(inputSaldoAnterior.value) || 0;
    const saldoPost = Math.max(0, saldoAnt - monto);
    inputSaldoPosterior.value = saldoPost.toFixed(2);
  }

  inputMonto.addEventListener('input', recalcularSaldo);
  inputSaldoAnterior.addEventListener('input', recalcularSaldo);
}

/* ==========================================================================
   4. PRESETS DE CASOS DE PRUEBA (NORMAL VS SOSPECHOSO)
   ========================================================================== */
function initPresets() {
  const btnNormal = document.getElementById('btnPresetNormal');
  const btnFraude = document.getElementById('btnPresetFraude');

  if (!btnNormal && !btnFraude) return;

  if (btnNormal) {
    btnNormal.addEventListener('click', () => {
      cargarPreset({
        monto: 35.00,
        monto_promedio_usuario: 80.00,
        saldo_anterior: 1250.00,
        saldo_posterior: 1215.00,
        producto: 'Yape',
        destinatario_nuevo: 0,
        hora_inusual: 0,
        velocidad_operacion: 35,
        llamada_reciente: 0,
        cambio_dispositivo: 0,
        edad: 32,
        usuario_nuevo: 0,
        dias_desde_registro: 540,
        operaciones_dia: 2,
        operaciones_ultima_hora: 1,
        alertas_ignoradas: 0,
        distancia_ubicacion: 0.8,
        ubicacion_inusual: 0,
        hora: 14,
        dia_semana: 2
      });
      mostrarToast('Caso de prueba "Transacción Segura" cargado.');
    });
  }

  if (btnFraude) {
    btnFraude.addEventListener('click', () => {
      cargarPreset({
        monto: 1450.00,
        monto_promedio_usuario: 90.00,
        saldo_anterior: 1500.00,
        saldo_posterior: 50.00,
        producto: 'Transferencia',
        destinatario_nuevo: 1,
        hora_inusual: 1,
        velocidad_operacion: 12,
        llamada_reciente: 1,
        cambio_dispositivo: 1,
        edad: 26,
        usuario_nuevo: 1,
        dias_desde_registro: 4,
        operaciones_dia: 8,
        operaciones_ultima_hora: 4,
        alertas_ignoradas: 2,
        distancia_ubicacion: 48.5,
        ubicacion_inusual: 1,
        hora: 3,
        dia_semana: 6
      });
      mostrarToast('Caso de prueba "Posible Fraude" cargado.');
    });
  }
}

function cargarPreset(datos) {
  for (const [key, val] of Object.entries(datos)) {
    const el = document.getElementById('input_' + key);
    if (el) {
      if (el.type === 'checkbox') {
        el.checked = Boolean(val);
      } else {
        el.value = val;
      }
    }
  }
}

/* ==========================================================================
   5. MODALES Y TOASTS
   ========================================================================== */
function initModals() {
  document.querySelectorAll('[data-modal-target]').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-modal-target');
      const modal = document.getElementById(targetId);
      if (modal) modal.classList.add('active');
    });
  });

  document.querySelectorAll('.modal-close, [data-modal-close]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = btn.closest('.modal-overlay');
      if (modal) modal.classList.remove('active');
    });
  });

  document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.remove('active');
    });
  });
}

function mostrarToast(mensaje) {
  let toast = document.getElementById('appToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'appToast';
    toast.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #10B981;
      color: #0A0E17;
      font-weight: 700;
      padding: 0.85rem 1.4rem;
      border-radius: 9999px;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
      z-index: 9999;
      font-size: 0.9rem;
      transition: all 0.3s ease;
      opacity: 0;
      transform: translateY(20px);
    `;
    document.body.appendChild(toast);
  }

  toast.textContent = mensaje;
  toast.style.opacity = '1';
  toast.style.transform = 'translateY(0)';

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(20px)';
  }, 2500);
}
