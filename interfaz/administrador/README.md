# 🛡️ Módulo de UI de Administración Antifraude & Analítica Fintech

Módulo web independiente, desacoplado y portable para la administración, visualización y gestión de transacciones, detección de fraudes con Inteligencia Artificial, gestión de usuarios y analítica en tiempo real.

---

## 📁 Estructura del Módulo

```text
modulo_admin_ui/
├── __init__.py                 # Exportador principal y fábrica del Blueprint
├── blueprint.py                # Definición de rutas, controladores y contexto global
├── data_provider.py            # Capa de abstracción de datos (Mock y SQLite incluidos)
├── config.py                   # Configuración de temas, marcas, paginación y seguridad
├── run_standalone.py           # Servidor independiente para demo/pruebas rápidas
├── requirements.txt            # Dependencias mínimas (Flask, Jinja2, Werkzeug)
├── README.md                   # Documentación general
├── INTEGRACION.md              # Guía paso a paso para integrarlo en otro proyecto
├── static/
│   ├── css/
│   │   └── admin.css           # Sistema de diseño Fintech Dark (tokens, grids, tablas, modales)
│   └── js/
│       └── admin.js            # Lógica de navegación móvil, modales, filtros e interactividad
└── templates/
    └── admin/
        ├── base_admin.html     # Layout maestro del panel (sidebar, topbar, alertas, footer)
        ├── dashboard.html      # Métricas ejecutivas en tiempo real, KPIs y gráficos
        ├── transacciones.html  # Auditoría de transacciones con filtros dinámicos
        ├── fraudes.html        # Centro de triaje y alertas de seguridad de Machine Learning
        ├── usuarios.html       # Gestión de cuentas y privilegios
        ├── estadisticas.html   # Distribución estadística de variables críticas
        ├── productos.html      # Análisis comparativo de riesgo por producto/canal
        ├── modelos.html        # Comparativa y benchmarking de modelos ML (AUC, F1, Accuracy)
        ├── matriz_confusion.html # Matriz de confusión interactiva y métricas de clasificación
        └── reportes.html       # Reportes consolidados y resúmenes ejecutivos
```

---

## 🚀 Inicio Rápido (Modo Standalone)

Puedes probar el módulo de inmediato de forma aislada sin configurar ninguna base de datos:

```bash
# 1. Entrar a la carpeta del módulo
cd modulo_admin_ui

# 2. Instalar dependencias si es necesario
pip install -r requirements.txt

# 3. Iniciar el servidor de prueba
python run_standalone.py
```

Abre tu navegador en: **`http://127.0.0.1:5050`**

---

## 🔌 Integración en Cualquier Proyecto Flask

Para agregar este panel a una aplicación Flask existente en tan solo **4 líneas de código**:

```python
from flask import Flask
from modulo_admin_ui import create_admin_blueprint, MockAdminDataProvider

app = Flask(__name__)
app.secret_key = "tu_clave_secreta"

# 1. Crear el Blueprint con el proveedor de datos deseado
admin_bp = create_admin_blueprint(
    data_provider=MockAdminDataProvider(), # o tu propio proveedor
    url_prefix="/admin"
)

# 2. Registrar en tu aplicación
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

Acceso al panel: `http://localhost:5000/admin`

---

## 🗄️ Conectar con tu Propia Base de Datos / Backend

El módulo utiliza el patrón **Data Provider (`BaseAdminDataProvider`)**, lo que significa que no depende de ningún motor de base de datos específico. Puedes conectarlo a **PostgreSQL, MySQL, MongoDB, SQLAlchemy, Django ORM o APIs REST**:

```python
from modulo_admin_ui.data_provider import BaseAdminDataProvider

class MiProveedorPostgres(BaseAdminDataProvider):
    def get_kpis(self):
        # Consulta tu base de datos y retorna el diccionario de métricas
        return {
            "total_transacciones": 120000,
            "transacciones_legitimas": 118000,
            "total_fraudes_detectados": 2000,
            "porcentaje_fraude": 1.67,
            "alertas_pendientes": 5,
            "precision_modelo": 99.1
        }
    
    # Implementa los demás métodos requeridos...
```

Consulta el archivo [INTEGRACION.md](file:///c:/Users/jesus/Documents/iknterfaz%20de%20jaki/PROYECTO_FRAUDE/PROYECTO_FRAUDE/modulo_admin_ui/INTEGRACION.md) para ver la guía completa con ejemplos para SQLAlchemy, Django y FastAPI.
