# 🛡️ Sistema Inteligente de Detección y Prevención de Fraude — Yape BCP

Plataforma integral de ciberseguridad y prevención de fraudes financieros en tiempo real para transacciones de **Yape (Banco de Crédito del Perú - BCP)**, impulsada por algoritmos avanzados de **Machine Learning (Gradient Boosting Classifier)**.

---

## 🚀 Características Principales

### 📱 1. Aplicación Móvil de Usuario (Yape)
- **Autenticación Segura & OTP Real:** Registro de nuevos usuarios con verificación de correo electrónico en tiempo real mediante tokens OTP de 6 dígitos enviados por SMTP Gmail seguro.
- **Yapeo Inteligente con Evaluación en Vivo:** Cada intento de transacción es evaluado en milisegundos por el modelo de ML. Si detecta anomalías multivariables (monto atípico, destinatario nuevo, hora inusual, etc.), bloquea preventivamente la transacción y genera una alerta SOC.
- **Historial Aislado:** Cada usuario visualiza estricta y únicamente sus propios movimientos y comprobantes.
- **Yape Seguro:** Panel de ciberseguridad personal que indica el estado del monitoreo, transacciones analizadas y nivel de riesgo.
- **Soporte de Temas:** Conmutador fluido entre modo Claro (*Light*) y modo Oscuro (*Dark*).

### 🖥️ 2. Centro de Control y Monitoreo SOC (Administrador)
- **Dashboard Ejecutivo:** KPIs en tiempo real (volumen analizado, tasa de fraude, dinero salvado, alertas críticas).
- **Auditoría de Transacciones:** Tabla interactiva con filtros dinámicos por producto, nivel de riesgo y resultado ML.
- **Gestión de Cuentas y Usuarios:** Activación, bloqueo preventivo y asignación de roles.
- **Estadísticas Descriptivas:** Exploración analítica basada en más de 50,000 registros históricos.
- **Análisis por Producto:** Vulnerabilidad relativa por canal (Yape, Transferencia BCP, Pago de Servicios, Compras Web).
- **Benchmarking de Modelos:** Comparación de desempeño entre **Gradient Boosting** (98.65% de precisión), PyTorch y TensorFlow.
- **Matrices de Confusión Interactivas:** Visualización de falsos positivos, falsos negativos, sensibilidad y especificidad.
- **Reportes Ejecutivos:** Vista de auditoría formateada lista para exportar a PDF o imprimir.
- **Perfil de Administrador:** Gestión de credenciales de seguridad, cambio de contraseña y revisión de privilegios SOC.

---

## 🛠️ Stack Tecnológico

| Capa | Tecnologías |
| :--- | :--- |
| **Backend** | Python 3.10+, Flask (Blueprints modulares), Werkzeug |
| **Machine Learning** | Scikit-Learn (Gradient Boosting), Joblib, Pandas, NumPy |
| **Base de Datos** | SQLite3 relacional con foreign keys e integridad referencial |
| **Frontend** | HTML5 semántico, CSS3 Vanilla moderno (Glassmorphism, Dark/Light theme), JavaScript ES6+ |
| **Visualización** | Chart.js 4.x |
| **Comunicaciones** | SMTPLib con cifrado TLS 587 (Gmail API / App Password) |

---

## 📁 Estructura del Proyecto

```text
├── datos/                  # Datasets de entrenamiento y transacciones analizadas
├── documentacion/          # Especificaciones técnicas y diagramas
├── graficos/               # Visualizaciones generadas del modelo
├── interfaz/               # Aplicación web Flask y módulos UI
│   ├── administrador/      # Módulo modular SOC del Administrador (Templates, CSS, JS)
│   ├── database/           # Base de datos SQLite (fraude_yape.db) y scripts de seed
│   ├── static/             # Recursos estáticos globales
│   ├── templates/          # Portal principal y plantillas base
│   ├── usuario/            # Interfaz de la app móvil Yape
│   └── app.py              # Servidor principal Flask y APIs REST
├── modelos/                # Pesos del modelo entrenado (.pkl), Scaler y Columnas
├── notebooks/              # Jupyter Notebooks de EDA y entrenamiento del modelo
├── pruebas/                # Scripts de test y validación
├── resultados/             # CSVs analíticos y matrices de confusión
└── requirements.txt        # Dependencias de Python
```

---

## ⚡ Instalación y Puesta en Marcha

### 1. Clonar el Repositorio
```bash
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
cd TU_REPOSITORIO
```

### 2. Crear y Activar Entorno Virtual
En Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

En Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. (Opcional) Configuración de Correo para Códigos OTP Reales
Si deseas que el sistema envíe correos reales a los usuarios registrados, copia la plantilla de configuración:
```bash
cp interfaz/config_correo.example.json interfaz/config_correo.json
```
Edita `interfaz/config_correo.json` con tu correo de Gmail y una [Contraseña de Aplicación de Google](https://myaccount.google.com/apppasswords).

### 5. Iniciar la Aplicación
```bash
python interfaz/app.py
```

Accede desde tu navegador:
- **Portal Principal:** [http://localhost:5000/](http://localhost:5000/)
- **App Usuario (Yape):** [http://localhost:5000/usuario](http://localhost:5000/usuario)
- **Centro Antifraude Admin:** [http://localhost:5000/admin](http://localhost:5000/admin)

---

## 🔑 Credenciales de Demostración

| Rol | Correo | Contraseña |
| :--- | :--- | :--- |
| **Administrador SOC** | `admin@bcp.com` | `admin123` |
| **Usuario Yape** | `juan@correo.com` | `juan123` |

---

## 🔒 Seguridad y Buenas Prácticas
- Las contraseñas se almacenan con hashing seguro (`werkzeug.security`).
- Las sesiones de Administrador y Usuario están completamente segregadas para evitar colisiones de contexto en pruebas locales simultáneas.
- Las credenciales privadas y claves de aplicación están protegidas mediante `.gitignore`.
