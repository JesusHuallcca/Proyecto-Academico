# 🛠️ Guía de Integración y Personalización

Esta guía explica detalladamente cómo trasladar y adaptar el **Módulo de UI de Administración** a cualquier otro proyecto web (Flask, FastAPI, Django o microservicios).

---

## 1. Copiar los Archivos a tu Nuevo Proyecto

Simplemente copia la carpeta `modulo_admin_ui/` dentro del directorio raíz o de módulos de tu nuevo proyecto:

```text
mi_nuevo_proyecto/
├── app.py                     # Tu aplicación principal
├── modulo_admin_ui/           # Carpeta del módulo exportado
│   ├── blueprint.py
│   ├── data_provider.py
│   ├── config.py
│   ├── static/
│   └── templates/
```

---

## 2. Métodos de Integración

### Opción A: Proyecto Flask Existente

En tu `app.py`:

```python
from flask import Flask
from modulo_admin_ui import create_admin_blueprint, SQLiteAdminDataProvider, AdminConfig

app = Flask(__name__)
app.secret_key = "clave_segura_de_tu_proyecto"

# Configuración personalizada de marca y temas
config = AdminConfig()
config.BRAND_NAME = "Mi Empresa Antifraude"
config.BRAND_SUBTITLE = "Centro de Operaciones"
config.BRAND_LOGO_TEXT = "E"
config.REQUIRE_AUTH = True  # Valida que exista session['id_usuario']

# Proveedor de datos conectado a tu SQLite
provider = SQLiteAdminDataProvider("ruta/a/tu/base_de_datos.db")

# Registro del Blueprint
admin_blueprint = create_admin_blueprint(
    data_provider=provider,
    config=config,
    url_prefix="/admin"
)
app.register_blueprint(admin_blueprint)

if __name__ == "__main__":
    app.run(debug=True)
```

---

### Opción B: Conectar con SQLAlchemy / PostgreSQL / MySQL

Crea un archivo `mi_data_provider.py` que herede de `BaseAdminDataProvider`:

```python
from modulo_admin_ui.data_provider import BaseAdminDataProvider
from models import db, Transaction, Alert, User  # Tus modelos de SQLAlchemy

class SQLAlchemyDataProvider(BaseAdminDataProvider):
    def get_kpis(self):
        total = Transaction.query.count()
        fraudes = Alert.query.filter_by(nivel='CRITICO').count()
        pendientes = Alert.query.filter_by(estado='PENDIENTE').count()
        
        return {
            "total_transacciones": total,
            "transacciones_legitimas": total - fraudes,
            "total_fraudes_detectados": fraudes,
            "porcentaje_fraude": round((fraudes / total * 100) if total else 0, 2),
            "alertas_pendientes": pendientes,
            "precision_modelo": 98.5
        }

    def get_transactions(self, limit=100, filtro_resultado="TODOS", filtro_producto="TODOS"):
        q = Transaction.query
        if filtro_producto != "TODOS":
            q = q.filter_by(producto=filtro_producto)
        return [t.to_dict() for t in q.order_by(Transaction.id.desc()).limit(limit).all()]

    def get_alerts(self, filtro_estado="TODOS"):
        q = Alert.query
        if filtro_estado != "TODOS":
            q = q.filter_by(estado=filtro_estado)
        return [a.to_dict() for a in q.all()]

    def update_alert_status(self, id_alerta, nuevo_estado):
        alerta = Alert.query.get(id_alerta)
        if alerta:
            alerta.estado = nuevo_estado
            db.session.commit()
            return True
        return False

    def get_users(self):
        return [u.to_dict() for u in User.query.all()]

    def create_user(self, nombre, apellido, correo, password, tipo_usuario):
        # Lógica para registrar usuario en tu ORM
        pass

    def update_user_status(self, id_usuario, nuevo_estado):
        # Lógica para actualizar estado
        pass

    def get_descriptive_stats(self):
        return []

    def get_product_analysis(self):
        return []

    def get_model_comparison(self):
        return {}

    def get_confusion_matrices(self):
        return {}
```

Luego pásalo al crear el blueprint:
```python
provider = SQLAlchemyDataProvider()
admin_bp = create_admin_blueprint(data_provider=provider)
app.register_blueprint(admin_bp)
```

---

## 3. Personalización de Estilos y Colores

Puedes personalizar todos los colores y fuentes cambiando las variables CSS en [modulo_admin_ui/static/css/admin.css](file:///c:/Users/jesus/Documents/iknterfaz%20de%20jaki/PROYECTO_FRAUDE/PROYECTO_FRAUDE/modulo_admin_ui/static/css/admin.css) o inyectando un bloque CSS en `base_admin.html`:

```css
:root {
  /* Color principal de la marca */
  --yape-primary: #1E40AF;        /* Azul Corporativo */
  --yape-primary-hover: #1D4ED8;
  
  /* Color secundario / acento */
  --yape-cyan: #06B6D4;           /* Cyan Acento */
  --yape-cyan-hover: #22D3EE;

  /* Fondo de la aplicación (Dark / Light) */
  --bg-app: #0F172A;
  --bg-sidebar: #0B0F19;
  --bg-card: #1E293B;
  
  /* Tipografías */
  --font-heading: 'Inter', sans-serif;
  --font-body: 'Inter', sans-serif;
}
```

---

## 4. Endpoints y Vistas Disponibles

| Endpoint | Ruta | Descripción |
| :--- | :--- | :--- |
| `admin_dashboard` | `/admin/dashboard` | Tablero general de control con KPIs y gráficos Chart.js |
| `admin_transacciones` | `/admin/transacciones` | Registro tabular de transacciones con filtros de búsqueda |
| `admin_fraudes` | `/admin/fraudes` | Panel de revisión y triaje de alertas de seguridad |
| `admin_usuarios` | `/admin/usuarios` | Listado, creación y activación/desactivación de cuentas |
| `admin_estadisticas` | `/admin/estadisticas` | Estadísticas descriptivas de variables del modelo |
| `admin_productos` | `/admin/productos` | Comparativa de volumen y tasa de fraude por producto |
| `admin_modelos` | `/admin/modelos` | Benchmarking de modelos de ML (AUC, F1, Recall, Latencia) |
| `admin_confusion` | `/admin/confusion` | Matrices de confusión interactivas |
| `admin_reportes` | `/admin/reportes` | Reportes ejecutivos consolidados |
| `api_kpis` | `/admin/api/kpis` | Endpoint JSON con métricas en tiempo real |
| `api_alertas` | `/admin/api/alertas` | Endpoint JSON con alertas filtradas |
