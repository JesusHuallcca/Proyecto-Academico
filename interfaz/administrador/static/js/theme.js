/* ==========================================================================
   SISTEMA DE TEMA PERSISTENTE CLARO / OSCURO (YAPE.IA)
   Cambio instantáneo en el DOM sin recargar la página + sync con Backend
   ========================================================================== */

(function () {
  const THEME_KEY = "yape_antifraude_theme";

  function aplicarTema(tema) {
    document.documentElement.setAttribute("data-theme", tema);
    localStorage.setItem(THEME_KEY, tema);

    // Actualizar todos los botones de tema presentes en la página
    document.querySelectorAll(".theme-toggle-btn").forEach((btn) => {
      const iconSpan = btn.querySelector(".theme-icon");
      const iconHtml = tema === "dark" ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
      if (iconSpan) {
        iconSpan.innerHTML = iconHtml;
      } else {
        btn.innerHTML = iconHtml;
      }
      btn.setAttribute("title", tema === "dark" ? "Cambiar a modo claro" : "Cambiar a modo oscuro");
      btn.setAttribute("aria-label", tema === "dark" ? "Cambiar a modo claro" : "Cambiar a modo oscuro");
    });

    // Notificar a Chart.js u otros componentes si existen
    window.dispatchEvent(new CustomEvent("themechange", { detail: { theme: tema } }));

    // Sincronizar asíncronamente con el backend sin bloquear la UI
    try {
      fetch("/api/tema", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tema: tema }),
      }).catch(() => {});
    } catch (e) {}
  }

  function obtenerTemaActual() {
    return document.documentElement.getAttribute("data-theme") || localStorage.getItem(THEME_KEY) || "light";
  }

  function alternarTema() {
    const actual = obtenerTemaActual();
    const nuevo = actual === "dark" ? "light" : "dark";
    aplicarTema(nuevo);
  }

  // Inicializar al cargar el DOM
  document.addEventListener("DOMContentLoaded", () => {
    // Si el servidor inyectó data-theme o hay en localStorage
    const saved = localStorage.getItem(THEME_KEY) || document.documentElement.getAttribute("data-theme") || "light";
    aplicarTema(saved);

    // Asignar evento click a todos los botones de toggle
    document.querySelectorAll(".theme-toggle-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        alternarTema();
      });
    });
  });

  // Exponer globalmente
  window.alternarTema = alternarTema;
  window.aplicarTema = aplicarTema;
})();
