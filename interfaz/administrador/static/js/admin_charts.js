/* ==========================================================================
   ADMINISTRADOR - GRÁFICOS Y ACCIONES DINÁMICAS (CHART.JS)
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  // Manejo de Sidebar en dispositivos móviles/tablets
  const hamburgerBtn = document.getElementById("admin-hamburger");
  const sidebar = document.getElementById("admin-sidebar");
  const overlay = document.getElementById("sidebar-overlay");

  if (hamburgerBtn && sidebar && overlay) {
    hamburgerBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open");
      overlay.classList.toggle("active");
    });

    overlay.addEventListener("click", () => {
      sidebar.classList.remove("open");
      overlay.classList.remove("active");
    });
  }

  // Si Chart.js no está en la página, salir
  if (typeof Chart === "undefined") return;

  // Paleta de colores Yape
  const YAPE_PURPLE = "#742284";
  const YAPE_CYAN = "#00d2c4";
  const YAPE_DANGER = "#ef4444";
  const YAPE_SUCCESS = "#10b981";
  const YAPE_AMBER = "#f59e0b";

  function getTextColor() {
    return document.documentElement.getAttribute("data-theme") === "dark" ? "#aba1bd" : "#645a73";
  }

  function getGridColor() {
    return document.documentElement.getAttribute("data-theme") === "dark" ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)";
  }

  const chartInstances = {};

  // 1. Gráfico Distribución Normal vs Fraude (Doughnut)
  const ctxFraude = document.getElementById("chart-distribucion-fraude");
  if (ctxFraude) {
    chartInstances.fraude = new Chart(ctxFraude, {
      type: "doughnut",
      data: {
        labels: ["Transacciones Legítimas (93.56%)", "Fraudes Detectados (6.44%)"],
        datasets: [{
          data: [46778, 3222],
          backgroundColor: [YAPE_PURPLE, YAPE_DANGER],
          borderColor: "transparent",
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: getTextColor(), boxWidth: 12 }
          }
        }
      }
    });
  }

  // 2. Gráfico Operaciones por Producto (Bar)
  const ctxProd = document.getElementById("chart-productos-ops");
  if (ctxProd) {
    chartInstances.productos = new Chart(ctxProd, {
      type: "bar",
      data: {
        labels: ["Yape", "Compra", "Pago servicios", "Transferencia", "Recarga"],
        datasets: [{
          label: "Cantidad de Operaciones",
          data: [20083, 9945, 7491, 7457, 5024],
          backgroundColor: YAPE_PURPLE,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: { ticks: { color: getTextColor() }, grid: { display: false } },
          y: { ticks: { color: getTextColor() }, grid: { color: getGridColor() } }
        }
      }
    });
  }

  // 3. Gráfico Porcentaje de Fraude por Producto (Bar horizontal / vertical)
  const ctxPctFraude = document.getElementById("chart-pct-fraude-producto");
  if (ctxPctFraude) {
    chartInstances.pctFraude = new Chart(ctxPctFraude, {
      type: "bar",
      data: {
        labels: ["Compra", "Recarga", "Pago servicios", "Yape", "Transferencia"],
        datasets: [{
          label: "% Tasa de Fraude",
          data: [6.70, 6.69, 6.47, 6.33, 6.21],
          backgroundColor: [YAPE_DANGER, "#f87171", "#fb923c", YAPE_CYAN, YAPE_PURPLE],
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => `Tasa de Fraude: ${context.parsed.y}%`
            }
          }
        },
        scales: {
          x: { ticks: { color: getTextColor() }, grid: { display: false } },
          y: {
            ticks: { color: getTextColor(), callback: (v) => v + "%" },
            grid: { color: getGridColor() },
            suggestedMin: 5,
            suggestedMax: 8
          }
        }
      }
    });
  }

  // 4. Gráfico Monto Promedio por Producto
  const ctxMontoProd = document.getElementById("chart-monto-producto");
  if (ctxMontoProd) {
    chartInstances.montoProd = new Chart(ctxMontoProd, {
      type: "line",
      data: {
        labels: ["Compra", "Recarga", "Pago servicios", "Yape", "Transferencia"],
        datasets: [
          {
            label: "Monto Promedio (S/)",
            data: [402.32, 404.61, 406.10, 402.82, 402.81],
            borderColor: YAPE_PURPLE,
            backgroundColor: "rgba(116, 34, 132, 0.1)",
            tension: 0.3,
            fill: true,
            pointRadius: 5
          },
          {
            label: "Mediana (S/)",
            data: [240.73, 243.20, 252.01, 248.03, 249.40],
            borderColor: YAPE_CYAN,
            borderDash: [5, 5],
            tension: 0.3,
            pointRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { color: getTextColor(), boxWidth: 12 } }
        },
        scales: {
          x: { ticks: { color: getTextColor() }, grid: { display: false } },
          y: { ticks: { color: getTextColor() }, grid: { color: getGridColor() } }
        }
      }
    });
  }

  // 5. Comparación General de Modelos ML
  const ctxModelos = document.getElementById("chart-comparacion-modelos");
  if (ctxModelos) {
    chartInstances.modelos = new Chart(ctxModelos, {
      type: "bar",
      data: {
        labels: ["Gradient Boosting (Mejor)", "PyTorch", "TensorFlow", "Random Forest", "Árbol Decisión", "Reg. Logística"],
        datasets: [
          {
            label: "Accuracy",
            data: [0.9865, 0.9612, 0.9527, 0.9546, 0.9222, 0.9155],
            backgroundColor: YAPE_PURPLE
          },
          {
            label: "F1-Score",
            data: [0.8847, 0.7617, 0.7223, 0.7201, 0.5939, 0.5835],
            backgroundColor: YAPE_CYAN
          },
          {
            label: "Recall",
            data: [0.8043, 0.9627, 0.9550, 0.9068, 0.8835, 0.9193],
            backgroundColor: YAPE_AMBER
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { color: getTextColor(), boxWidth: 12 } }
        },
        scales: {
          x: { ticks: { color: getTextColor() }, grid: { display: false } },
          y: {
            ticks: { color: getTextColor() },
            grid: { color: getGridColor() },
            suggestedMin: 0.5,
            suggestedMax: 1.0
          }
        }
      }
    });
  }

  // 6. Gráfico Radar / Radar de Métricas de Modelos Top
  const ctxRadar = document.getElementById("chart-radar-modelos");
  if (ctxRadar) {
    chartInstances.radar = new Chart(ctxRadar, {
      type: "radar",
      data: {
        labels: ["Accuracy", "Precision", "Recall", "F1-Score"],
        datasets: [
          {
            label: "Gradient Boosting",
            data: [0.9865, 0.9829, 0.8043, 0.8847],
            borderColor: YAPE_PURPLE,
            backgroundColor: "rgba(116, 34, 132, 0.25)"
          },
          {
            label: "PyTorch",
            data: [0.9612, 0.6301, 0.9627, 0.7617],
            borderColor: YAPE_CYAN,
            backgroundColor: "rgba(0, 210, 196, 0.25)"
          },
          {
            label: "TensorFlow",
            data: [0.9527, 0.5807, 0.9550, 0.7223],
            borderColor: YAPE_AMBER,
            backgroundColor: "rgba(245, 158, 11, 0.25)"
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom", labels: { color: getTextColor(), boxWidth: 10 } }
        },
        scales: {
          r: {
            angleLines: { color: getGridColor() },
            grid: { color: getGridColor() },
            pointLabels: { color: getTextColor(), font: { size: 11, weight: "bold" } },
            ticks: { display: false }
          }
        }
      }
    });
  }

  // 7. Gráfico Distribución Horaria y Alertas 24h
  const ctxHorario = document.getElementById("chart-tendencia-horaria");
  if (ctxHorario) {
    const horasLabels = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`);
    // Datos realistas basados en comportamiento transaccional
    const volumenOperaciones = [450, 280, 150, 110, 130, 290, 850, 1850, 3100, 4200, 4900, 5200, 5600, 4800, 4300, 3900, 4400, 5100, 5800, 5400, 4700, 3800, 2400, 1200];
    const fraudesDetectados = [48, 52, 65, 58, 44, 25, 18, 12, 15, 20, 22, 19, 21, 24, 28, 30, 34, 41, 46, 52, 60, 68, 72, 62];

    chartInstances.horario = new Chart(ctxHorario, {
      type: "line",
      data: {
        labels: horasLabels,
        datasets: [
          {
            label: "Volumen de Operaciones",
            data: volumenOperaciones,
            borderColor: YAPE_PURPLE,
            backgroundColor: "rgba(116, 34, 132, 0.12)",
            yAxisID: "y",
            fill: true,
            tension: 0.35,
            pointRadius: 2,
            pointHoverRadius: 5
          },
          {
            label: "Fraudes Detectados (Alto Riesgo)",
            data: fraudesDetectados,
            borderColor: YAPE_DANGER,
            backgroundColor: "rgba(239, 68, 68, 0.18)",
            yAxisID: "y1",
            fill: true,
            tension: 0.35,
            pointRadius: 3,
            pointHoverRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false
        },
        plugins: {
          legend: { position: "top", labels: { color: getTextColor(), boxWidth: 12 } }
        },
        scales: {
          x: { ticks: { color: getTextColor(), maxRotation: 0, autoSkip: true, maxTicksLimit: 12 }, grid: { display: false } },
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            ticks: { color: getTextColor() },
            grid: { color: getGridColor() },
            title: { display: true, text: 'Volumen', color: getTextColor() }
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            grid: { drawOnChartArea: false },
            ticks: { color: YAPE_DANGER },
            title: { display: true, text: 'Fraudes', color: YAPE_DANGER }
          }
        }
      }
    });
  }

  // 8. Gráfico Estadísticas: Medias y Desviaciones
  const ctxStatsMedias = document.getElementById("chart-stats-medias");
  if (ctxStatsMedias) {
    chartInstances.statsMedias = new Chart(ctxStatsMedias, {
      type: "bar",
      data: {
        labels: ["Monto (S/)", "Monto Prom Usuario", "Velocidad Op (seg)", "Edad", "Distancia (km)"],
        datasets: [
          {
            label: "Promedio (Mean)",
            data: [403.39, 526.29, 92.71, 49.02, 4.95],
            backgroundColor: YAPE_PURPLE,
            borderRadius: 6
          },
          {
            label: "Desv. Estándar (Std)",
            data: [494.97, 274.44, 51.01, 18.20, 4.98],
            backgroundColor: YAPE_CYAN,
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { color: getTextColor(), boxWidth: 12 } }
        },
        scales: {
          x: { ticks: { color: getTextColor() }, grid: { display: false } },
          y: { ticks: { color: getTextColor() }, grid: { color: getGridColor() } }
        }
      }
    });
  }

  // 9. Gráfico Estadísticas: Dispersión de Percentiles (Q1, Mediana, Q3)
  const ctxStatsPerc = document.getElementById("chart-stats-percentiles");
  if (ctxStatsPerc) {
    chartInstances.statsPerc = new Chart(ctxStatsPerc, {
      type: "line",
      data: {
        labels: ["Monto (S/)", "Monto Prom Usuario", "Velocidad Op (seg)", "Edad"],
        datasets: [
          {
            label: "25% (Q1)",
            data: [125.64, 287.86, 49.00, 33.00],
            borderColor: YAPE_AMBER,
            backgroundColor: "transparent",
            tension: 0.3,
            pointRadius: 4
          },
          {
            label: "Mediana (50%)",
            data: [246.68, 526.65, 93.00, 49.00],
            borderColor: YAPE_PURPLE,
            backgroundColor: "rgba(116, 34, 132, 0.1)",
            tension: 0.3,
            fill: true,
            pointRadius: 5
          },
          {
            label: "75% (Q3)",
            data: [483.14, 763.53, 137.00, 65.00],
            borderColor: YAPE_CYAN,
            backgroundColor: "transparent",
            tension: 0.3,
            pointRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { color: getTextColor(), boxWidth: 12 } }
        },
        scales: {
          x: { ticks: { color: getTextColor() }, grid: { display: false } },
          y: { ticks: { color: getTextColor() }, grid: { color: getGridColor() } }
        }
      }
    });
  }

  // Actualizar colores cuando se cambia el tema
  window.addEventListener("themechange", () => {
    const textColor = getTextColor();
    const gridColor = getGridColor();

    Object.values(chartInstances).forEach((chart) => {
      if (chart.options.scales) {
        if (chart.options.scales.x) {
          chart.options.scales.x.ticks.color = textColor;
        }
        if (chart.options.scales.y) {
          chart.options.scales.y.ticks.color = textColor;
          chart.options.scales.y.grid.color = gridColor;
        }
        if (chart.options.scales.r) {
          chart.options.scales.r.pointLabels.color = textColor;
          chart.options.scales.r.grid.color = gridColor;
          chart.options.scales.r.angleLines.color = gridColor;
        }
      }
      if (chart.options.plugins && chart.options.plugins.legend) {
        chart.options.plugins.legend.labels.color = textColor;
      }
      chart.update();
    });
  });
});
