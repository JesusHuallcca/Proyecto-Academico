# Módulo de UI de Administración — yape.ia

Este paquete contiene **exclusivamente los componentes de la interfaz de usuario (UI) del Administrador**, desacoplados de bases de datos, lógica de autenticación específica y modelos de Machine Learning.

---

## 📁 Estructura del Módulo

```text
modulo_ui_administrador/
├── demo_servidor.py                # Servidor Flask mínimo autocontenido para pruebas inmediatas
├── README.md                       # Guía de integración y documentación técnica
├── templates/
│   ├── base.html                   # Layout base global (fuentes, CDN FontAwesome, Chart.js, tema)
│   └── administrador/
│       ├── layout_admin.html       # Sidebar lateral, navbar superior, drawer móvil y selector de tema
│       ├── dashboard.html          # Panel principal con KPIs, gráficas y actividad reciente
│       ├── transacciones.html      # Monitoreo, filtros avanzados y tabla de transacciones
│       ├── usuarios.html           # Listado, estado y auditoría de cuentas de usuarios
│       ├── estadisticas.html       # Tablas analíticas y métricas descriptivas
│       ├── productos.html          # Métricas de riesgo por tipo de producto financiero
│       ├── modelos.html            # Comparativa y benchmarking de modelos analíticos / ML
│       ├── metricas.html           # Curvas ROC-AUC, precisión, recall y F1-score
│       ├── matrices.html           # Matrices de confusión interactivas
│       └── reportes.html           # Plantilla de informe ejecutivo lista para imprimir/PDF
└── static/
    ├── css/
    │   ├── base.css                # Sistema de diseño, tokens (colores, sombras, tipografía, modo claro/oscuro)
    │   └── admin.css               # Estilos especializados del panel de administración (grids, sidebar, cards)
    └── js/
        ├── theme.js                # Lógica de cambio y persistencia de tema (Claro / Oscuro)
        └── admin_charts.js         # Inicialización de gráficos interactivos Chart.js y control de sidebar móvil
```

---

## 🚀 Cómo probarlo inmediatamente

1. Asegúrate de tener Flask instalado:
   ```bash
   pip install flask
   ```
2. Ejecuta el servidor demo incluido:
   ```bash
   python demo_servidor.py
   ```
3. Abre tu navegador en **http://localhost:5050** para ver todas las pantallas del administrador funcionando con datos de prueba.

---

## 🔌 Cómo integrarlo en tu proyecto

### 1. Copiar carpetas
- Copia el contenido de `templates/` a la carpeta de plantillas de tu proyecto (Flask, Jinja2, FastAPI o Django con Jinja).
- Copia el contenido de `static/` a la carpeta de archivos estáticos de tu proyecto.

### 2. Dependencias externas (incluidas vía CDN en `base.html`)
- **Tipografías:** Plus Jakarta Sans & Outfit (Google Fonts).
- **Iconografía:** Font Awesome 6.5.1 (`cdnjs.cloudflare.com`).
- **Gráficos interactivos:** Chart.js 4.4.1 (`cdn.jsdelivr.net`).

### 3. Rutas requeridas por las plantillas
Cada plantilla enlaza a las siguientes rutas mediante `url_for`:

| Nombre de Endpoint | Descripción | Parámetros esperados |
| :--- | :--- | :--- |
| `admin_dashboard` | Panel principal del administrador | KPIs (`kpis`), transacciones recientes (`transacciones`) |
| `admin_transacciones` | Lista de transacciones | Lista de transacciones (`transacciones`), paginación (`pagina`, `total_paginas`) |
| `admin_usuarios` | Gestión de usuarios | Lista de usuarios (`usuarios`) |
| `admin_toggle_usuario` | Activar/desactivar estado de usuario | `id_usuario` |
| `admin_estadisticas` | Estadísticas descriptivas | `estadisticas` (lista de diccionarios) |
| `admin_productos` | Vulnerabilidad por producto | `productos` (lista de diccionarios) |
| `admin_modelos` | Comparativa de modelos | `modelos` (lista de diccionarios) |
| `admin_metricas` | Curvas y métricas de desempeño | Ninguno requerido (utiliza `admin_charts.js`) |
| `admin_matrices` | Matrices de confusión | `matrices` (diccionario con matrices) |
| `admin_reportes` | Reporte ejecutivo imprimible | Ninguno obligatorio |
| `logout` | Cerrar sesión | Redirección |
| `api_tema` (POST `/api/tema`) | Sincronizar tema con backend | JSON `{"tema": "dark" | "light"}` |

### 4. Variables de sesión usadas en el layout
El sidebar y navbar muestran información del usuario en sesión si existen estas variables:
- `session['nombre']`: Nombre mostrado en el avatar y cabecera (ej: "Administrador").
- `session['tema']`: Tema inicial ("light" o "dark").
