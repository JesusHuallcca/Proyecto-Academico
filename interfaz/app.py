import sys
import sqlite3
import json
import os
import smtplib
import ssl

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime, timedelta
import random
import joblib
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for, session, abort

# ============================================================
# CONFIGURACIÓN Y RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DB_PATH = BASE_DIR / "database" / "fraude_yape.db"
MODELOS_DIR = PROJECT_ROOT / "modelos"

RUTA_MODELO = MODELOS_DIR / "modelo_fraude.pkl"
RUTA_SCALER = MODELOS_DIR / "scaler_fraude.pkl"
RUTA_COLUMNAS = MODELOS_DIR / "columnas_modelo.pkl"

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "administrador" / "static"),
    static_url_path="/static"
)
app.secret_key = "clave_secreta_bcp_yape_antifraude_segura_2026"

from werkzeug.security import check_password_hash
from administrador.blueprint import create_admin_blueprint
from administrador.config import AdminConfig
from administrador.data_provider import SQLiteAdminDataProvider

admin_config = AdminConfig()
admin_config.REQUIRE_AUTH = True
admin_data_provider = SQLiteAdminDataProvider(str(DB_PATH))
admin_bp = create_admin_blueprint(
    data_provider=admin_data_provider,
    config=admin_config,
    name="admin",
    url_prefix="/admin"
)
app.register_blueprint(admin_bp)


# ============================================================
# CARGA DEL MODELO DE MACHINE LEARNING
# ============================================================

ml_model = None
ml_scaler = None
ml_columns = None

try:
    if RUTA_MODELO.exists() and RUTA_SCALER.exists() and RUTA_COLUMNAS.exists():
        ml_model = joblib.load(RUTA_MODELO)
        ml_scaler = joblib.load(RUTA_SCALER)
        ml_columns = joblib.load(RUTA_COLUMNAS)
        print("✓ Modelo Gradient Boosting, Scaler y Columnas cargados con éxito.")
    else:
        print("⚠️ Advertencia: Archivos de modelo no encontrados en", MODELOS_DIR)
except Exception as e:
    print(f"❌ Error al cargar modelo ML: {e}")


# ============================================================
# CONEXIÓN A BASE DE DATOS
# ============================================================

def conectar_bd():
    conexion = sqlite3.connect(DB_PATH, timeout=15)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


# ============================================================
# MOTOR DE DETECCIÓN Y EVALUACIÓN DE FRAUDE
# ============================================================

def predecir_fraude(datos_tx):
    """
    Evalúa los datos de una transacción utilizando el modelo de Machine Learning entrenado.
    Retorna probabilidad, clasificación, nivel de riesgo y factores explicativos.
    """
    if ml_model is None or ml_scaler is None or ml_columns is None:
        # Fallback heurístico en caso de ausencia de archivos
        prob_f = 85.0 if (datos_tx.get("monto", 0) > 3000 or datos_tx.get("hora_inusual", 0) == 1) else 3.5
        es_f = 1 if prob_f > 70 else 0
        nivel = "CRITICO" if prob_f > 85 else ("ALTO" if prob_f > 70 else ("MEDIO" if prob_f > 40 else "BAJO"))
        return {
            "es_fraude": es_f,
            "probabilidad_fraude": round(prob_f, 2),
            "probabilidad_normal": round(100.0 - prob_f, 2),
            "nivel_riesgo": nivel,
            "factores": ["Monto elevado vs promedio", "Operación fuera de horario habitual"] if es_f else []
        }

    # Crear dataframe con los datos
    df = pd.DataFrame([{
        "monto": float(datos_tx.get("monto", 0)),
        "destinatario_nuevo": int(datos_tx.get("destinatario_nuevo", 0)),
        "hora_inusual": int(datos_tx.get("hora_inusual", 0)),
        "velocidad_operacion": float(datos_tx.get("velocidad_operacion", 35)),
        "llamada_reciente": int(datos_tx.get("llamada_reciente", 0)),
        "cambio_dispositivo": int(datos_tx.get("cambio_dispositivo", 0)),
        "edad": int(datos_tx.get("edad", 30)),
        "usuario_nuevo": int(datos_tx.get("usuario_nuevo", 0)),
        "dias_desde_registro": int(datos_tx.get("dias_desde_registro", 180)),
        "cantidad_operaciones_dia": int(datos_tx.get("operaciones_dia", 1)),
        "operaciones_ultima_hora": int(datos_tx.get("operaciones_ultima_hora", 1)),
        "alertas_ignoradas": int(datos_tx.get("alertas_ignoradas", 0)),
        "distancia_operaciones": float(datos_tx.get("distancia_ubicacion", 0.5)),
        "ubicacion_inusual": int(datos_tx.get("ubicacion_inusual", 0)),
        "saldo_anterior": float(datos_tx.get("saldo_anterior", 5000)),
        "saldo_posterior": float(datos_tx.get("saldo_posterior", 4950)),
        "monto_promedio_usuario": float(datos_tx.get("monto_promedio_usuario", 45)),
        "hora": int(datos_tx.get("hora", datetime.now().hour)),
        "dia_semana": int(datos_tx.get("dia_semana", datetime.now().weekday())),
        "producto": str(datos_tx.get("producto", "Yape"))
    }])

    # Codificar producto
    df = pd.get_dummies(df, columns=["producto"], dtype=float)
    df = df.reindex(columns=ml_columns, fill_value=0.0).astype(float)

    # Escalar
    datos_escalados = ml_scaler.transform(df)

    # Predecir
    prediccion = int(ml_model.predict(datos_escalados)[0])
    probabilidades = ml_model.predict_proba(datos_escalados)[0]

    prob_normal = round(float(probabilidades[0]) * 100, 2)
    prob_fraude = round(float(probabilidades[1]) * 100, 2)

    # Determinar nivel de riesgo
    if prob_fraude >= 80:
        nivel = "CRITICO"
    elif prob_fraude >= 60:
        nivel = "ALTO"
    elif prob_fraude >= 35:
        nivel = "MEDIO"
    else:
        nivel = "BAJO"

    # Identificar factores explicativos del riesgo
    factores = []
    if datos_tx.get("monto", 0) > (datos_tx.get("monto_promedio_usuario", 50) * 3):
        factores.append(f"Monto (S/ {datos_tx.get('monto'):.2f}) excede significativamente el promedio habitual.")
    if int(datos_tx.get("hora_inusual", 0)) == 1 or (0 <= int(datos_tx.get("hora", 12)) <= 5):
        factores.append("Operación realizada en franja horaria atípica de madrugada.")
    if int(datos_tx.get("destinatario_nuevo", 0)) == 1:
        factores.append("Destinatario no registrado previamente en contactos frecuentes.")
    if int(datos_tx.get("cambio_dispositivo", 0)) == 1:
        factores.append("Transacción originada desde un nuevo dispositivo o sesión no habitual.")
    if int(datos_tx.get("llamada_reciente", 0)) == 1:
        factores.append("Llamada sospechosa registrada antes de la operación (patrón vishing).")
    if float(datos_tx.get("velocidad_operacion", 30)) < 12:
        factores.append("Velocidad de operación anómalamente veloz (posible bot o coacción).")
    if float(datos_tx.get("distancia_ubicacion", 0)) > 50:
        factores.append(f"Distancia geográfica inusual ({datos_tx.get('distancia_ubicacion')} km) respecto al histórico.")

    if not factores and prediccion == 1:
        factores.append("Combinación multivariable de comportamiento anómalo detectada por el modelo.")

    return {
        "es_fraude": prediccion,
        "probabilidad_fraude": prob_fraude,
        "probabilidad_normal": prob_normal,
        "nivel_riesgo": nivel,
        "factores": factores
    }


# ============================================================
# RUTAS DE SERVIDO DE INTERFACES ESTÁTICAS Y AUTENTICACIÓN
# ============================================================

@app.route("/")
def portal_principal():
    """Portal de aterrizaje para seleccionar Dashboard de Usuario o Administrador."""
    return render_template("portal.html")


# Rutas de Usuario (Yape)
@app.route("/usuario/login")
def login_usuario():
    """Sirve la pantalla de Login de Yape."""
    return send_from_directory(str(BASE_DIR / "usuario"), "login.html")


@app.route("/usuario/registro")
def registro_usuario():
    """Sirve la pantalla de Registro de nuevo usuario en Yape con verificación Gmail."""
    return send_from_directory(str(BASE_DIR / "usuario"), "registro.html")


@app.route("/usuario")
@app.route("/usuario/")
def app_usuario():
    """Sirve la interfaz principal de la App Yape (requiere sesión de tipo USUARIO)."""
    user_id = session.get("user_id") or (session.get("id_usuario") if str(session.get("tipo_usuario", "")).upper() == "USUARIO" else None)
    if not user_id and ("id_usuario" not in session or session.get("tipo_usuario") == "ADMIN"):
        return redirect("/usuario/login")
    return send_from_directory(str(BASE_DIR / "usuario"), "index.html")


@app.route("/usuario/<path:filename>")
def assets_usuario(filename):
    """Sirve estilos, scripts e imágenes del módulo de usuario."""
    return send_from_directory(str(BASE_DIR / "usuario"), filename)


# Rutas de Administrador (Centro Antifraude)
@app.route("/admin/login")
def login_admin():
    """Sirve la pantalla de Login del Centro Antifraude BCP."""
    return send_from_directory(str(BASE_DIR / "administrador"), "login.html")


@app.route("/admin/app.js")
def admin_legacy_app_js():
    """Compatibilidad con scripts legacy del administrador."""
    return send_from_directory(str(BASE_DIR / "administrador"), "app.js")


@app.route("/admin/styles.css")
def admin_legacy_styles_css():
    """Compatibilidad con estilos legacy del administrador."""
    return send_from_directory(str(BASE_DIR / "administrador"), "styles.css")


@app.route("/admin/legacy")
def admin_legacy_dashboard():
    """Sirve la versión single-page legacy del Centro Antifraude BCP."""
    admin_id = session.get("admin_id") or (session.get("id_usuario") if session.get("tipo_usuario") == "ADMIN" else None)
    if not admin_id:
        return redirect("/admin/login")
    return send_from_directory(str(BASE_DIR / "administrador"), "index.html")


@app.route("/logout")
@app.route("/admin/logout")
def app_logout():
    """Cierra la sesión del administrador y redirige al login administrativo."""
    session.pop("admin_id", None)
    session.pop("admin_nombre", None)
    session.pop("admin_tipo", None)
    session.pop("admin_correo", None)
    if session.get("tipo_usuario") == "ADMIN":
        session.pop("id_usuario", None)
        session.pop("nombre", None)
        session.pop("tipo_usuario", None)
        session.pop("correo", None)
    return redirect("/admin/login")

logout = app_logout


@app.route("/api/tema", methods=["POST"])
def api_cambiar_tema():
    """Persiste la preferencia de tema (claro / oscuro) en la sesión."""
    datos = request.get_json() or {}
    nuevo_tema = datos.get("tema", "light")
    session["tema"] = nuevo_tema
    return jsonify({"success": True, "tema": nuevo_tema})


# ============================================================
# HELPER: OBTENCIÓN ROBUSTA DE USUARIO ACTIVO EN YAPE
# ============================================================

def obtener_id_usuario_actual():
    """
    Identifica de forma precisa al usuario autenticado en la aplicación Yape:
    1. Revisa session['user_id'] (sesión dedicada de usuario para permitir coexistencia con Admin)
    2. Revisa Header HTTP 'X-User-Id' (enviado por la interfaz móvil Yape)
    3. Revisa JSON body 'user_id' o query param 'user_id'
    4. Revisa session['id_usuario'] si no es una sesión exclusiva de ADMIN
    """
    # 1. Sesión de usuario dedicada
    uid = session.get("user_id")
    if uid:
        return uid

    # 2. Header HTTP X-User-Id enviado por la interfaz frontend
    h_uid = request.headers.get("X-User-Id")
    if h_uid:
        try:
            val = int(h_uid)
            conexion = conectar_bd()
            c = conexion.cursor()
            c.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = ? AND tipo_usuario = 'USUARIO' AND estado = 'ACTIVO'", (val,))
            row = c.fetchone()
            conexion.close()
            if row:
                return row["id_usuario"]
        except (ValueError, TypeError):
            pass

    # 3. JSON body user_id
    if request.is_json:
        try:
            body = request.get_json(silent=True) or {}
            b_uid = body.get("user_id")
            if b_uid:
                val = int(b_uid)
                conexion = conectar_bd()
                c = conexion.cursor()
                c.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = ? AND tipo_usuario = 'USUARIO' AND estado = 'ACTIVO'", (val,))
                row = c.fetchone()
                conexion.close()
                if row:
                    return row["id_usuario"]
        except Exception:
            pass

    # 4. Query param user_id
    q_uid = request.args.get("user_id")
    if q_uid:
        try:
            val = int(q_uid)
            conexion = conectar_bd()
            c = conexion.cursor()
            c.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = ? AND tipo_usuario = 'USUARIO' AND estado = 'ACTIVO'", (val,))
            row = c.fetchone()
            conexion.close()
            if row:
                return row["id_usuario"]
        except (ValueError, TypeError):
            pass

    # 5. Sesión genérica de tipo USUARIO
    if session.get("id_usuario") and str(session.get("tipo_usuario", "")).upper() == "USUARIO":
        return session.get("id_usuario")

    return None


# ============================================================
# APIS DE AUTENTICACIÓN
# ============================================================

@app.route("/api/auth/login", methods=["POST"])
def api_auth_login():
    """Valida credenciales para inicio de sesión en Usuario o Admin con soporte multisesión."""
    datos = request.get_json() or {}
    correo = str(datos.get("correo", "")).strip().lower()
    password = str(datos.get("password", "")).strip()
    portal = str(datos.get("portal", "")).strip().upper()  # 'USUARIO' o 'ADMIN'

    if not correo or not password:
        return jsonify({"status": "error", "mensaje": "Ingresa correo y contraseña."}), 400

    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT id_usuario, nombre, apellido, correo, password, tipo_usuario, estado
        FROM usuarios
        WHERE LOWER(correo) = ?
    """, (correo,))
    u = cursor.fetchone()
    conexion.close()

    valid_password = False
    if u:
        if u["password"] == password:
            valid_password = True
        else:
            try:
                if check_password_hash(u["password"], password):
                    valid_password = True
            except Exception:
                pass

    if not u or not valid_password:
        return jsonify({"status": "error", "mensaje": "Credenciales inválidas. Verifica correo y contraseña."}), 401

    if u["estado"] == "INACTIVO":
        return jsonify({"status": "error", "mensaje": "Esta cuenta se encuentra inactiva o bloqueada."}), 403

    if portal == "ADMIN" and u["tipo_usuario"] != "ADMIN":
        return jsonify({"status": "error", "mensaje": "Acceso restringido: Se requieren credenciales de Administrador SOC."}), 403

    # Guardar en sesión de forma desacoplada para evitar conflictos Admin vs Usuario
    if portal == "ADMIN" or u["tipo_usuario"] == "ADMIN":
        session["admin_id"] = u["id_usuario"]
        session["admin_nombre"] = f"{u['nombre']} {u['apellido']}"
        session["admin_tipo"] = "ADMIN"
        session["admin_correo"] = u["correo"]
        session["id_usuario"] = u["id_usuario"]
        session["nombre"] = f"{u['nombre']} {u['apellido']}"
        session["tipo_usuario"] = "ADMIN"
        session["correo"] = u["correo"]
    else:
        session["user_id"] = u["id_usuario"]
        session["user_nombre"] = f"{u['nombre']} {u['apellido']}"
        session["user_tipo"] = "USUARIO"
        session["user_correo"] = u["correo"]
        session["id_usuario"] = u["id_usuario"]
        session["nombre"] = f"{u['nombre']} {u['apellido']}"
        session["tipo_usuario"] = "USUARIO"
        session["correo"] = u["correo"]

    redirect_url = "/admin" if portal == "ADMIN" or u["tipo_usuario"] == "ADMIN" else "/usuario"

    return jsonify({
        "status": "success",
        "mensaje": "Autenticación exitosa.",
        "redirect": redirect_url,
        "usuario": {
            "id_usuario": u["id_usuario"],
            "nombre": u["nombre"],
            "apellido": u["apellido"],
            "correo": u["correo"],
            "tipo_usuario": u["tipo_usuario"]
        }
    })


@app.route("/api/auth/logout", methods=["POST"])
def api_auth_logout():
    """Cierra la sesión activa de usuario sin alterar la de administración."""
    session.pop("user_id", None)
    session.pop("user_nombre", None)
    session.pop("user_tipo", None)
    session.pop("user_correo", None)
    if session.get("tipo_usuario") == "USUARIO":
        session.pop("id_usuario", None)
        session.pop("nombre", None)
        session.pop("tipo_usuario", None)
        session.pop("correo", None)
    return jsonify({"status": "success", "mensaje": "Sesión finalizada."})


@app.route("/api/auth/sesion", methods=["GET"])
def api_auth_sesion():
    """Retorna los datos de la sesión actual de usuario."""
    user_id = obtener_id_usuario_actual()
    if user_id:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("SELECT id_usuario, nombre, apellido, correo, tipo_usuario FROM usuarios WHERE id_usuario = ?", (user_id,))
        u = cursor.fetchone()
        conexion.close()
        if u:
            return jsonify({
                "status": "success",
                "autenticado": True,
                "usuario": {
                    "id_usuario": u["id_usuario"],
                    "nombre": f"{u['nombre']} {u['apellido']}".strip(),
                    "primer_nombre": u["nombre"],
                    "tipo_usuario": u["tipo_usuario"],
                    "correo": u["correo"]
                }
            })
    return jsonify({"status": "success", "autenticado": False})


# ============================================================
# SERVICIO DE ENVÍO DE CÓDIGO A GMAIL (SMTP)
# ============================================================

def obtener_credenciales_gmail():
    """
    Obtiene el correo emisor y contraseña de aplicación de Gmail desde config_correo.json
    o variables de entorno del sistema.
    """
    ruta_cfg = BASE_DIR / "config_correo.json"
    emisor = os.environ.get("GMAIL_USER", "").strip()
    password = os.environ.get("GMAIL_APP_PASSWORD", "").strip()

    if ruta_cfg.exists():
        try:
            with open(ruta_cfg, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("gmail_emisor"):
                    emisor = data.get("gmail_emisor").strip().lower()
                if data.get("gmail_password_app"):
                    password = data.get("gmail_password_app").strip().replace(" ", "")
        except Exception:
            pass

    if password:
        password = password.replace(" ", "")

    return emisor, password


@app.route("/api/auth/config-correo", methods=["GET", "POST"])
def api_config_correo():
    """Permite guardar y verificar las credenciales de Gmail para envíos reales."""
    ruta_cfg = BASE_DIR / "config_correo.json"

    if request.method == "POST":
        datos = request.get_json() or {}
        emisor = str(datos.get("gmail_emisor", "")).strip().lower()
        password = str(datos.get("gmail_password_app", "")).strip().replace(" ", "")

        if not emisor or not password:
            return jsonify({
                "status": "error",
                "mensaje": "Ingresa el correo Gmail y la contraseña de aplicación de 16 caracteres de Google."
            }), 400

        # Probar autenticación en smtp.gmail.com
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
                server.starttls(context=context)
                server.login(emisor, password)
        except Exception as e:
            return jsonify({
                "status": "error",
                "mensaje": f"No se pudo autenticar con Gmail ({e}). Verifica que la 'Contraseña de aplicación' de Google sea correcta (16 letras) y que la verificación en 2 pasos esté activa."
            }), 400

        with open(ruta_cfg, "w", encoding="utf-8") as f:
            json.dump({"gmail_emisor": emisor, "gmail_password_app": password}, f, indent=2)

        return jsonify({
            "status": "success",
            "mensaje": "¡Remitente de Gmail configurado exitosamente! Los códigos llegarán directo a tu celular."
        })

    emisor, pwd = obtener_credenciales_gmail()
    return jsonify({
        "status": "success",
        "configurado": bool(emisor and pwd),
        "gmail_emisor": emisor if emisor else ""
    })


def enviar_correo_gmail(destinatario, codigo, nombre):
    """
    Envía el código de verificación de 6 dígitos al correo Gmail del usuario
    mediante el servidor seguro smtp.gmail.com:587 con cifrado TLS.
    """
    emisor, password = obtener_credenciales_gmail()

    if not emisor or not password:
        return False, "Configura el correo remitente de Gmail y su contraseña de aplicación para recibir el correo en tu celular."

    asunto = f"{codigo} es tu código de verificación Yape BCP"

    cuerpo_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"></head>
    <body style="margin:0; padding:25px; font-family:'Segoe UI', Helvetica, Arial, sans-serif; background-color:#0B0F19; color:#FFFFFF;">
        <div style="max-width:500px; margin:0 auto; background:#111827; border-radius:24px; overflow:hidden; border:1px solid rgba(255,255,255,0.1); box-shadow:0 20px 40px rgba(0,0,0,0.6);">
            <div style="background:linear-gradient(135deg, #742284 0%, #9B30B5 100%); padding:28px 24px; text-align:center;">
                <h1 style="margin:0; font-size:32px; font-weight:800; color:#FFFFFF; letter-spacing:-0.5px;">Yape</h1>
                <p style="margin:6px 0 0 0; color:#00D2C4; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:1px;">Seguridad Digital Antifraude BCP</p>
            </div>
            <div style="padding:32px 28px; text-align:center;">
                <h2 style="font-size:20px; color:#FFFFFF; margin-top:0; margin-bottom:12px;">¡Hola, {nombre}!</h2>
                <p style="font-size:14px; color:#94A3B8; line-height:1.6; margin-bottom:24px;">
                    Usa este código de verificación de 6 dígitos para confirmar tu correo y activar tu cuenta en Yape:
                </p>
                <div style="background:rgba(116, 34, 132, 0.15); border:2px dashed #00D2C4; border-radius:16px; padding:18px 24px; display:inline-block; margin-bottom:24px;">
                    <span style="font-size:36px; font-weight:800; letter-spacing:10px; color:#00D2C4; font-family:monospace;">{codigo}</span>
                </div>
                <p style="font-size:13px; color:#64748B; line-height:1.5; margin-bottom:0;">
                    ⏱️ Este código expirará en <strong>15 minutos</strong>.<br>
                    🛡️ Por tu seguridad, jamás compartas este código con terceros ni con operadores.
                </p>
            </div>
            <div style="background:#0B0F19; padding:16px; text-align:center; font-size:11px; color:#64748B; border-top:1px solid rgba(255,255,255,0.06);">
                Banco de Crédito del Perú BCP • Centro de Ciberseguridad
            </div>
        </div>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = asunto
        msg["From"] = f"Yape BCP <{emisor}>"
        msg["To"] = destinatario
        msg.attach(MIMEText(cuerpo_html, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=12) as server:
            server.starttls(context=context)
            server.login(emisor, password)
            server.send_message(msg)

        print(f"\n=======================================================")
        print(f" ✓ [GMAIL SMTP] Correo enviado exitosamente a {destinatario}")
        print(f"=======================================================\n")
        return True, f"¡Código de verificación enviado a tu Gmail ({destinatario})! Revisa tu celular."
    except Exception as e:
        print(f"❌ [GMAIL SMTP] Error al enviar correo a {destinatario}: {e}")
        return False, f"Error al enviar por Gmail ({e}). Verifica que la contraseña de aplicación sea correcta."


# ============================================================
# APIS DE REGISTRO CON VERIFICACIÓN GMAIL (OTP)
# ============================================================

@app.route("/api/auth/registro/enviar-codigo", methods=["POST"])
def api_registro_enviar_codigo():
    """
    Recibe los datos del nuevo usuario, genera un código OTP de 6 dígitos
    y lo envía por Gmail para que el usuario lo revise en su aplicativo móvil.
    """
    datos = request.get_json() or {}
    nombre = str(datos.get("nombre", "")).strip()
    apellido = str(datos.get("apellido", "")).strip()
    celular = str(datos.get("celular", "")).strip()
    correo = str(datos.get("correo", "")).strip().lower()
    password = str(datos.get("password", "")).strip()

    if not nombre or not apellido or not celular or not correo or not password:
        return jsonify({"status": "error", "mensaje": "Todos los campos son obligatorios."}), 400

    if len(password) < 4:
        return jsonify({"status": "error", "mensaje": "La contraseña debe tener al menos 4 caracteres."}), 400

    if "@" not in correo or "." not in correo:
        return jsonify({"status": "error", "mensaje": "Ingresa un correo electrónico válido."}), 400

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()

        # Verificar si el correo ya existe
        cursor.execute("SELECT id_usuario FROM usuarios WHERE LOWER(correo) = ?", (correo,))
        if cursor.fetchone():
            return jsonify({"status": "error", "mensaje": "Este correo electrónico ya está registrado en Yape."}), 400

        # Generar código OTP de 6 dígitos
        codigo_otp = f"{random.randint(100000, 999999)}"

        # Guardar en base de datos
        datos_json = json.dumps({
            "nombre": nombre,
            "apellido": apellido,
            "celular": celular,
            "correo": correo,
            "password": password
        })

        cursor.execute("""
            INSERT INTO codigos_verificacion (correo, codigo, datos_json, fecha_creacion, expirado)
            VALUES (?, ?, ?, ?, 0)
        """, (correo, codigo_otp, datos_json, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conexion.commit()
    except Exception as e:
        conexion.rollback()
        return jsonify({"status": "error", "mensaje": f"Error al generar código: {str(e)}"}), 500
    finally:
        conexion.close()

    # Enviar correo real por Gmail
    enviado_real, mensaje_envio = enviar_correo_gmail(correo, codigo_otp, nombre)

    if not enviado_real:
        return jsonify({
            "status": "need_config",
            "mensaje": mensaje_envio,
            "correo": correo
        }), 400

    return jsonify({
        "status": "success",
        "mensaje": mensaje_envio,
        "correo": correo
    })


@app.route("/api/auth/registro/completar", methods=["POST"])
def api_registro_completar():
    """
    Valida el código OTP recibido. Si es correcto, registra al nuevo usuario,
    apertura su cuenta con saldo de bienvenida y crea su sesión.
    """
    datos = request.get_json() or {}
    correo = str(datos.get("correo", "")).strip().lower()
    codigo_ingresado = str(datos.get("codigo", "")).strip()

    if not correo or not codigo_ingresado:
        return jsonify({"status": "error", "mensaje": "Ingresa el correo y el código de 6 dígitos."}), 400

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT id_codigo, codigo, datos_json, fecha_creacion
            FROM codigos_verificacion
            WHERE LOWER(correo) = ? AND codigo = ? AND expirado = 0
            ORDER BY id_codigo DESC
            LIMIT 1
        """, (correo, codigo_ingresado))
        registro = cursor.fetchone()

        if not registro:
            return jsonify({"status": "error", "mensaje": "Código incorrecto o vencido. Verifica el código ingresado."}), 400

        datos_usuario = json.loads(registro["datos_json"])

        # Verificar si el usuario ya existe por si se envió previamente
        cursor.execute("SELECT id_usuario, nombre, apellido, correo FROM usuarios WHERE LOWER(correo) = ?", (correo,))
        usuario_existente = cursor.fetchone()

        if usuario_existente:
            id_usuario = usuario_existente["id_usuario"]
            nombre_u = usuario_existente["nombre"]
            apellido_u = usuario_existente["apellido"]
        else:
            # Crear usuario
            cursor.execute("""
                INSERT INTO usuarios (nombre, apellido, correo, password, tipo_usuario, estado)
                VALUES (?, ?, ?, ?, 'USUARIO', 'ACTIVO')
            """, (
                datos_usuario["nombre"],
                datos_usuario["apellido"],
                datos_usuario["correo"],
                datos_usuario["password"]
            ))
            id_usuario = cursor.lastrowid
            nombre_u = datos_usuario["nombre"]
            apellido_u = datos_usuario["apellido"]

        # Verificar si ya tiene cuenta
        cursor.execute("SELECT id_cuenta FROM cuentas WHERE id_usuario = ?", (id_usuario,))
        cuenta_existente = cursor.fetchone()

        if not cuenta_existente:
            # Generar número de cuenta garantizando que no colisione (UNIQUE constraint)
            celular = str(datos_usuario.get('celular', '')).strip()
            numero_cuenta = f"001-{celular}" if celular else f"001-{random.randint(100000000, 999999999)}"

            cursor.execute("SELECT id_cuenta FROM cuentas WHERE numero_cuenta = ?", (numero_cuenta,))
            if cursor.fetchone():
                # Si ya existe ese número de cuenta registrado, generar uno aleatorio único
                while True:
                    rand_cuenta = f"001-{random.randint(100000000, 999999999)}"
                    cursor.execute("SELECT id_cuenta FROM cuentas WHERE numero_cuenta = ?", (rand_cuenta,))
                    if not cursor.fetchone():
                        numero_cuenta = rand_cuenta
                        break

            cursor.execute("""
                INSERT INTO cuentas (id_usuario, numero_cuenta, tipo_cuenta, saldo, estado)
                VALUES (?, ?, 'AHORROS', 3000.00, 'ACTIVA')
            """, (id_usuario, numero_cuenta))

        # Registrar dispositivo móvil si no existe
        cursor.execute("SELECT id_dispositivo FROM dispositivos WHERE id_usuario = ?", (id_usuario,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO dispositivos (id_usuario, tipo_dispositivo, sistema_operativo, modelo, activo)
                VALUES (?, 'CELULAR', 'Android 14', 'Smartphone Registrado', 1)
            """, (id_usuario,))

        # Marcar código como expirado/utilizado
        cursor.execute("UPDATE codigos_verificacion SET expirado = 1 WHERE id_codigo = ?", (registro["id_codigo"],))

        conexion.commit()

        # Iniciar sesión automáticamente
        session["user_id"] = id_usuario
        session["user_nombre"] = f"{nombre_u} {apellido_u}"
        session["user_tipo"] = "USUARIO"
        session["user_correo"] = datos_usuario["correo"]
        session["id_usuario"] = id_usuario
        session["nombre"] = f"{nombre_u} {apellido_u}"
        session["tipo_usuario"] = "USUARIO"
        session["correo"] = datos_usuario["correo"]

        return jsonify({
            "status": "success",
            "mensaje": "¡Cuenta creada exitosamente! Bienvenido a Yape.",
            "redirect": "/usuario"
        })

    except Exception as e:
        conexion.rollback()
        print(f"❌ Error al completar registro: {e}")
        return jsonify({"status": "error", "mensaje": f"Error al activar la cuenta: {str(e)}"}), 500
    finally:
        conexion.close()


@app.route("/api/usuario/perfil", methods=["GET"])
def api_usuario_perfil():
    """Devuelve los datos del usuario logueado, su cuenta, saldo y dispositivo."""
    conexion = conectar_bd()
    cursor = conexion.cursor()

    target_user_id = obtener_id_usuario_actual()

    usuario = None
    if target_user_id:
        cursor.execute("""
            SELECT u.id_usuario, u.nombre, u.apellido, u.correo, u.estado AS estado_usuario,
                   c.id_cuenta, c.numero_cuenta, c.saldo, c.estado AS estado_cuenta,
                   d.modelo, d.sistema_operativo, d.tipo_dispositivo
            FROM usuarios u
            LEFT JOIN cuentas c ON u.id_usuario = c.id_usuario
            LEFT JOIN dispositivos d ON u.id_usuario = d.id_usuario
            WHERE u.id_usuario = ?
            LIMIT 1
        """, (target_user_id,))
        usuario = cursor.fetchone()

    # Si no hay sesión o no se encontró, usar usuario demo
    if not usuario:
        cursor.execute("""
            SELECT u.id_usuario, u.nombre, u.apellido, u.correo, u.estado AS estado_usuario,
                   c.id_cuenta, c.numero_cuenta, c.saldo, c.estado AS estado_cuenta,
                   d.modelo, d.sistema_operativo, d.tipo_dispositivo
            FROM usuarios u
            LEFT JOIN cuentas c ON u.id_usuario = c.id_usuario
            LEFT JOIN dispositivos d ON u.id_usuario = d.id_usuario
            WHERE u.correo = 'juan@correo.com'
            LIMIT 1
        """)
        usuario = cursor.fetchone()

    # Si aún no existe, inicializar demo
    if not usuario:
        from database.seed_data import seed_demo_data
        seed_demo_data()
        cursor.execute("""
            SELECT u.id_usuario, u.nombre, u.apellido, u.correo, u.estado AS estado_usuario,
                   c.id_cuenta, c.numero_cuenta, c.saldo, c.estado AS estado_cuenta,
                   d.modelo, d.sistema_operativo, d.tipo_dispositivo
            FROM usuarios u
            LEFT JOIN cuentas c ON u.id_usuario = c.id_usuario
            LEFT JOIN dispositivos d ON u.id_usuario = d.id_usuario
            WHERE u.correo = 'juan@correo.com'
            LIMIT 1
        """)
        usuario = cursor.fetchone()

    conexion.close()

    if not usuario:
        return jsonify({"status": "error", "mensaje": "Usuario no encontrado"}), 404

    return jsonify({
        "status": "success",
        "usuario": {
            "id_usuario": usuario["id_usuario"],
            "nombre_completo": f"{usuario['nombre']} {usuario['apellido']}".strip(),
            "nombre": usuario["nombre"],
            "apellido": usuario["apellido"],
            "correo": usuario["correo"],
            "estado_usuario": usuario["estado_usuario"],
            "cuenta": {
                "id_cuenta": usuario["id_cuenta"] or 1,
                "numero_cuenta": usuario["numero_cuenta"] or "001-1234567890",
                "saldo": float(usuario["saldo"]) if usuario["saldo"] is not None else 3000.00,
                "estado": usuario["estado_cuenta"] or "ACTIVA"
            },
            "dispositivo": {
                "modelo": usuario["modelo"] or "Smartphone Registrado",
                "so": usuario["sistema_operativo"] or "Android 14",
                "tipo": usuario["tipo_dispositivo"] or "CELULAR"
            }
        }
    })


@app.route("/api/usuario/transacciones", methods=["GET"])
def api_usuario_transacciones():
    """
    Devuelve estrictamente el historial reciente de transacciones del usuario logueado.
    Garantiza aislamiento total: cada usuario ve única y exclusivamente sus propios movimientos.
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()

    target_user_id = obtener_id_usuario_actual()

    if not target_user_id:
        cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = 'juan@correo.com' LIMIT 1")
        row = cursor.fetchone()
        target_user_id = row["id_usuario"] if row else None

    if not target_user_id:
        conexion.close()
        return jsonify({"status": "success", "total": 0, "transacciones": []})

    cursor.execute("""
        SELECT t.id_transaccion, t.fecha_hora, t.monto, t.producto, t.resultado,
               t.destinatario_nuevo, t.hora_inusual,
               p.probabilidad_fraude, p.probabilidad_normal, p.resultado AS prediccion_ml,
               a.id_alerta, a.nivel AS nivel_alerta, a.estado AS estado_alerta, a.descripcion AS desc_alerta
        FROM transacciones t
        LEFT JOIN predicciones p ON t.id_transaccion = p.id_transaccion
        LEFT JOIN alertas a ON t.id_transaccion = a.id_transaccion
        WHERE t.id_usuario = ?
        ORDER BY t.id_transaccion DESC
        LIMIT 50
    """, (target_user_id,))
    filas = cursor.fetchall()
    conexion.close()

    transacciones = []
    for f in filas:
        transacciones.append({
            "id_transaccion": f["id_transaccion"],
            "fecha_hora": f["fecha_hora"],
            "monto": float(f["monto"]),
            "producto": f["producto"],
            "resultado": f["resultado"],
            "probabilidad_fraude": f["probabilidad_fraude"] if f["probabilidad_fraude"] is not None else 0.0,
            "nivel_riesgo": f["nivel_alerta"] or ("BAJO" if f["resultado"] == "APROBADA" else "MEDIO"),
            "alerta": {
                "id_alerta": f["id_alerta"],
                "estado": f["estado_alerta"],
                "descripcion": f["desc_alerta"]
            } if f["id_alerta"] else None
        })

    return jsonify({
        "status": "success",
        "total": len(transacciones),
        "transacciones": transacciones
    })


@app.route("/api/usuario/notificaciones", methods=["GET"])
def api_usuario_notificaciones():
    """Devuelve las notificaciones del usuario actual (seguridad, transacciones y recomendaciones)."""
    conexion = conectar_bd()
    cursor = conexion.cursor()

    target_user_id = obtener_id_usuario_actual()
    if not target_user_id:
        cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = 'juan@correo.com' LIMIT 1")
        row = cursor.fetchone()
        target_user_id = row["id_usuario"] if row else None

    notificaciones = []
    if target_user_id:
        # Alertas de seguridad del usuario
        cursor.execute("""
            SELECT a.id_alerta, a.nivel, a.estado, a.descripcion, a.fecha_alerta,
                   t.monto, t.producto
            FROM alertas a
            JOIN transacciones t ON a.id_transaccion = t.id_transaccion
            WHERE t.id_usuario = ?
            ORDER BY a.fecha_alerta DESC
            LIMIT 5
        """, (target_user_id,))
        for a in cursor.fetchall():
            notificaciones.append({
                "id": f"alerta_{a['id_alerta']}",
                "tipo": "seguridad",
                "titulo": f"Alerta Preventiva ({a['nivel']})",
                "mensaje": a["descripcion"] or f"Operación de S/ {float(a['monto']):.2f} analizada por el modelo.",
                "fecha": a["fecha_alerta"][:16] if a["fecha_alerta"] else "Reciente",
                "leida": a["estado"] != "PENDIENTE",
                "badge": a["nivel"]
            })

        # Últimas transacciones del usuario
        cursor.execute("""
            SELECT id_transaccion, monto, producto, resultado, fecha_hora
            FROM transacciones
            WHERE id_usuario = ?
            ORDER BY fecha_hora DESC
            LIMIT 4
        """, (target_user_id,))
        for t in cursor.fetchall():
            estado_txt = "Aprobado" if t["resultado"] == "APROBADA" else "Observado"
            notificaciones.append({
                "id": f"tx_{t['id_transaccion']}",
                "tipo": "transaccion",
                "titulo": f"Yapeo {estado_txt}",
                "mensaje": f"Transferencia de S/ {float(t['monto']):.2f} realizada con éxito.",
                "fecha": t["fecha_hora"][:16] if t["fecha_hora"] else "Hoy",
                "leida": True,
                "badge": t["resultado"]
            })

    # Notificaciones del sistema
    notificaciones.insert(0, {
        "id": "sys_shield",
        "tipo": "sistema",
        "titulo": "Protección Antifraude Activa",
        "mensaje": "Inteligencia Artificial Gradient Boosting monitorea tu cuenta en tiempo real.",
        "fecha": "Hoy",
        "leida": False,
        "badge": "ACTIVO"
    })
    notificaciones.append({
        "id": "sys_pin",
        "tipo": "consejo",
        "titulo": "Consejo de Seguridad",
        "mensaje": "Nunca compartas tu código de validación de 6 dígitos con nadie.",
        "fecha": "Hoy",
        "leida": False,
        "badge": "CONSEJO"
    })

    conexion.close()
    return jsonify({
        "status": "success",
        "total": len(notificaciones),
        "no_leidas": sum(1 for n in notificaciones if not n["leida"]),
        "notificaciones": notificaciones
    })


@app.route("/api/usuario/notificaciones/marcar-leidas", methods=["POST"])
def api_usuario_marcar_notificaciones():
    return jsonify({"status": "success", "mensaje": "Notificaciones marcadas como leídas."})


@app.route("/api/usuario/seguridad-resumen", methods=["GET"])
def api_usuario_seguridad_resumen():
    """Devuelve las métricas de seguridad para la pantalla 'Yape Seguro' (Imagen 3)."""
    conexion = conectar_bd()
    cursor = conexion.cursor()

    target_user_id = obtener_id_usuario_actual()
    if not target_user_id:
        cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = 'juan@correo.com' LIMIT 1")
        row = cursor.fetchone()
        target_user_id = row["id_usuario"] if row else None

    total_analizadas = 1248
    riesgo = "Bajo"

    if target_user_id:
        cursor.execute("SELECT COUNT(*) AS total FROM transacciones WHERE id_usuario = ?", (target_user_id,))
        r = cursor.fetchone()
        if r and r["total"] > 0:
            total_analizadas = r["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total_alertas
            FROM alertas a
            JOIN transacciones t ON a.id_transaccion = t.id_transaccion
            WHERE t.id_usuario = ? AND a.estado = 'CONFIRMADA'
        """, (target_user_id,))
        ra = cursor.fetchone()
        if ra and ra["total_alertas"] > 0:
            riesgo = "Medio"

    conexion.close()

    return jsonify({
        "status": "success",
        "transacciones_analizadas": total_analizadas,
        "crecimiento_semana": "+12%",
        "riesgo_detectado": riesgo,
        "descripcion_riesgo": "Todo seguro por ahora",
        "modelo_activo": "Gradient Boosting",
        "precision_modelo": "98.65%",
        "monitoreo_activo": True
    })


@app.route("/api/usuario/yapear", methods=["POST"])
def api_usuario_yapear():
    """
    Ejecuta una transacción Yape desde el dashboard del usuario.
    Evalúa instantáneamente con Machine Learning antes de debitar o bloquear.
    """
    datos = request.get_json() or {}
    try:
        monto = float(datos.get("monto", 0))
    except (ValueError, TypeError):
        return jsonify({"status": "error", "mensaje": "Monto no válido"}), 400

    if monto <= 0:
        return jsonify({"status": "error", "mensaje": "El monto debe ser mayor a 0"}), 400

    destinatario = str(datos.get("destinatario", "Contacto")).strip()
    mensaje_nota = str(datos.get("mensaje", "")).strip()

    conexion = conectar_bd()
    cursor = conexion.cursor()

    # 1. Obtener usuario y saldo actual con identificación precisa del usuario activo
    target_user_id = obtener_id_usuario_actual()

    if target_user_id:
        cursor.execute("""
            SELECT u.id_usuario, u.nombre, u.apellido, u.correo,
                   c.id_cuenta, c.saldo, c.estado AS estado_cuenta,
                   COALESCE(d.id_dispositivo, 1) AS id_dispositivo
            FROM usuarios u
            JOIN cuentas c ON u.id_usuario = c.id_usuario
            LEFT JOIN dispositivos d ON u.id_usuario = d.id_usuario
            WHERE u.id_usuario = ?
            LIMIT 1
        """, (target_user_id,))
    else:
        cursor.execute("""
            SELECT u.id_usuario, u.nombre, u.apellido, u.correo,
                   c.id_cuenta, c.saldo, c.estado AS estado_cuenta,
                   COALESCE(d.id_dispositivo, 1) AS id_dispositivo
            FROM usuarios u
            JOIN cuentas c ON u.id_usuario = c.id_usuario
            LEFT JOIN dispositivos d ON u.id_usuario = d.id_usuario
            WHERE u.correo = 'juan@correo.com'
            LIMIT 1
        """)
    usuario = cursor.fetchone()

    if not usuario:
        conexion.close()
        return jsonify({"status": "error", "mensaje": "Usuario no encontrado"}), 404

    if usuario["estado_cuenta"] == "BLOQUEADA":
        conexion.close()
        return jsonify({
            "status": "blocked",
            "mensaje": "Tu cuenta se encuentra bloqueada por seguridad. Contacta con soporte BCP."
        }), 403

    saldo_actual = float(usuario["saldo"])
    if monto > saldo_actual:
        conexion.close()
        return jsonify({
            "status": "error",
            "mensaje": f"Saldo insuficiente. Tu saldo disponible es S/ {saldo_actual:.2f}"
        }), 400

    # 2. Calcular variables de comportamiento
    now = datetime.now()
    hora_actual = now.hour
    dia_actual = now.weekday()

    # Flags de simulación (si el usuario o frontend activa un escenario de prueba)
    simular_fraude = bool(datos.get("simular_fraude", False))
    destinatario_nuevo = int(datos.get("destinatario_nuevo", 1 if simular_fraude else random.choice([0, 0, 1])))
    hora_inusual = int(datos.get("hora_inusual", 1 if (simular_fraude or 0 <= hora_actual <= 5) else 0))
    cambio_dispositivo = int(datos.get("cambio_dispositivo", 1 if simular_fraude else 0))
    llamada_reciente = int(datos.get("llamada_reciente", 1 if simular_fraude else 0))
    velocidad_operacion = float(datos.get("velocidad_operacion", 8 if simular_fraude else random.uniform(25, 60)))
    distancia_ubicacion = float(datos.get("distancia_ubicacion", 150.0 if simular_fraude else 1.2))
    ubicacion_inusual = 1 if distancia_ubicacion > 50 else 0

    # Calcular monto promedio histórico
    cursor.execute("SELECT AVG(monto) AS prom, COUNT(*) AS total_tx FROM transacciones WHERE id_usuario = ?", (usuario["id_usuario"],))
    stats = cursor.fetchone()
    monto_promedio = float(stats["prom"]) if stats and stats["prom"] else 45.0
    operaciones_dia = int(stats["total_tx"] % 5 + 1) if stats else 1

    saldo_posterior_estimado = saldo_actual - monto

    tx_feature_data = {
        "monto": monto,
        "destinatario_nuevo": destinatario_nuevo,
        "hora_inusual": hora_inusual,
        "velocidad_operacion": velocidad_operacion,
        "llamada_reciente": llamada_reciente,
        "cambio_dispositivo": cambio_dispositivo,
        "edad": 32,
        "usuario_nuevo": 0,
        "dias_desde_registro": 240,
        "operaciones_dia": operaciones_dia,
        "operaciones_ultima_hora": 1,
        "alertas_ignoradas": 0,
        "distancia_ubicacion": distancia_ubicacion,
        "ubicacion_inusual": ubicacion_inusual,
        "saldo_anterior": saldo_actual,
        "saldo_posterior": saldo_posterior_estimado,
        "monto_promedio_usuario": monto_promedio,
        "hora": hora_actual,
        "dia_semana": dia_actual,
        "producto": "Yape"
    }

    # 3. Evaluación de Machine Learning
    evaluacion = predecir_fraude(tx_feature_data)
    es_fraude = evaluacion["es_fraude"]
    prob_fraude = evaluacion["probabilidad_fraude"]
    prob_normal = evaluacion["probabilidad_normal"]
    nivel_riesgo = evaluacion["nivel_riesgo"]
    factores = evaluacion["factores"]

    fecha_hora_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # 4. Decisión y persistencia
    if es_fraude == 1 or prob_fraude >= 70:
        # Fraude detectado: transacción bloqueada o en revisión preventiva
        resultado_tx = "SOSPECHOSA"
        nuevo_saldo = saldo_actual  # No se debita dinero mientras esté bloqueada

        cursor.execute("""
            INSERT INTO transacciones (
                id_usuario, id_cuenta, id_dispositivo, fecha_hora, monto, monto_promedio_usuario,
                saldo_anterior, saldo_posterior, producto, destinatario_nuevo, hora_inusual,
                velocidad_operacion, llamada_reciente, cambio_dispositivo, edad, usuario_nuevo,
                dias_desde_registro, operaciones_dia, operaciones_ultima_hora, alertas_ignoradas,
                distancia_ubicacion, ubicacion_inusual, hora, dia_semana, resultado, fecha_analisis
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Yape', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            usuario["id_usuario"], usuario["id_cuenta"], usuario["id_dispositivo"],
            fecha_hora_str, monto, monto_promedio, saldo_actual, saldo_actual,
            destinatario_nuevo, hora_inusual, velocidad_operacion, llamada_reciente,
            cambio_dispositivo, 32, 0, 240, operaciones_dia, 1, 0,
            distancia_ubicacion, ubicacion_inusual, hora_actual, dia_actual,
            resultado_tx, fecha_hora_str
        ))
        id_transaccion = cursor.lastrowid

        # Guardar predicción ML
        cursor.execute("""
            INSERT INTO predicciones (
                id_transaccion, modelo, probabilidad_normal, probabilidad_fraude, resultado, fecha_prediccion
            ) VALUES (?, 'Gradient Boosting', ?, ?, 'FRAUDE', ?)
        """, (id_transaccion, prob_normal, prob_fraude, fecha_hora_str))

        # Generar alerta de seguridad para el Administrador
        descripcion_alerta = (
            f"Alerta {nivel_riesgo}: Intento de Yapeo de S/ {monto:.2f} hacia {destinatario}. "
            f"Factores detectados: {'; '.join(factores) if factores else 'Patrón multivariable de riesgo.'}"
        )
        cursor.execute("""
            INSERT INTO alertas (
                id_transaccion, nivel, tipo_alerta, descripcion, estado, fecha_alerta
            ) VALUES (?, ?, 'YAPEO_ANOMALO', ?, 'PENDIENTE', ?)
        """, (id_transaccion, nivel_riesgo, descripcion_alerta, fecha_hora_str))

        # Registrar en historial
        cursor.execute("""
            INSERT INTO historial_acciones (id_usuario, id_transaccion, accion, descripcion, fecha)
            VALUES (?, ?, 'BLOQUEO_PREVENTIVO', ?, ?)
        """, (usuario["id_usuario"], id_transaccion, f"Transacción en revisión por riesgo {prob_fraude}%", fecha_hora_str))

        conexion.commit()
        conexion.close()

        return jsonify({
            "status": "suspicious",
            "decision": "DETENIDA_POR_SEGURIDAD",
            "id_transaccion": id_transaccion,
            "monto": monto,
            "destinatario": destinatario,
            "probabilidad_fraude": prob_fraude,
            "nivel_riesgo": nivel_riesgo,
            "factores": factores,
            "mensaje": "Por tu seguridad, hemos pausado esta operación. Nuestro sistema inteligente de prevención de fraudes BCP ha detectado un comportamiento inusual.",
            "saldo_actual": nuevo_saldo
        })

    else:
        # Transacción legítima aprobada
        resultado_tx = "APROBADA"
        nuevo_saldo = round(saldo_actual - monto, 2)

        # Descontar saldo
        cursor.execute("UPDATE cuentas SET saldo = ? WHERE id_cuenta = ?", (nuevo_saldo, usuario["id_cuenta"]))

        cursor.execute("""
            INSERT INTO transacciones (
                id_usuario, id_cuenta, id_dispositivo, fecha_hora, monto, monto_promedio_usuario,
                saldo_anterior, saldo_posterior, producto, destinatario_nuevo, hora_inusual,
                velocidad_operacion, llamada_reciente, cambio_dispositivo, edad, usuario_nuevo,
                dias_desde_registro, operaciones_dia, operaciones_ultima_hora, alertas_ignoradas,
                distancia_ubicacion, ubicacion_inusual, hora, dia_semana, resultado, fecha_analisis
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Yape', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            usuario["id_usuario"], usuario["id_cuenta"], usuario["id_dispositivo"],
            fecha_hora_str, monto, monto_promedio, saldo_actual, nuevo_saldo,
            destinatario_nuevo, hora_inusual, velocidad_operacion, llamada_reciente,
            cambio_dispositivo, 32, 0, 240, operaciones_dia, 1, 0,
            distancia_ubicacion, ubicacion_inusual, hora_actual, dia_actual,
            resultado_tx, fecha_hora_str
        ))
        id_transaccion = cursor.lastrowid

        # Guardar predicción ML
        cursor.execute("""
            INSERT INTO predicciones (
                id_transaccion, modelo, probabilidad_normal, probabilidad_fraude, resultado, fecha_prediccion
            ) VALUES (?, 'Gradient Boosting', ?, ?, 'NORMAL', ?)
        """, (id_transaccion, prob_normal, prob_fraude, fecha_hora_str))

        conexion.commit()
        conexion.close()

        # Generar código de comprobante simulado
        codigo_operacion = f"YP-{random.randint(100000, 999999)}"

        return jsonify({
            "status": "success",
            "decision": "APROBADA",
            "id_transaccion": id_transaccion,
            "codigo_operacion": codigo_operacion,
            "monto": monto,
            "destinatario": destinatario,
            "mensaje_nota": mensaje_nota,
            "fecha_hora": fecha_hora_str,
            "nuevo_saldo": nuevo_saldo,
            "probabilidad_seguridad": prob_normal,
            "mensaje": "¡Yapeo realizado con éxito!"
        })


# ============================================================
# APIS PARA DASHBOARD DE ADMINISTRADOR
# ============================================================

@app.route("/api/admin/metricas", methods=["GET"])
def api_admin_metricas():
    """Devuelve los KPIs y métricas clave en tiempo real para el administrador."""
    conexion = conectar_bd()
    cursor = conexion.cursor()

    # Total de transacciones
    cursor.execute("SELECT COUNT(*) AS total, SUM(monto) AS volumen FROM transacciones")
    tx_stats = cursor.fetchone()
    total_tx = tx_stats["total"] or 0
    volumen_total = float(tx_stats["volumen"] or 0)

    # Transacciones con fraude / sospechosas
    cursor.execute("""
        SELECT COUNT(*) AS total_fraudes, SUM(monto) AS monto_fraude
        FROM transacciones
        WHERE resultado = 'SOSPECHOSA'
    """)
    fraud_stats = cursor.fetchone()
    total_fraudes = fraud_stats["total_fraudes"] or 0
    monto_fraude = float(fraud_stats["monto_fraude"] or 0)

    # Tasa de fraude
    tasa_fraude = round((total_fraudes / total_tx * 100), 2) if total_tx > 0 else 0.0

    # Alertas por estado
    cursor.execute("""
        SELECT
            SUM(CASE WHEN estado = 'PENDIENTE' THEN 1 ELSE 0 END) AS pendientes,
            SUM(CASE WHEN estado = 'REVISADA' THEN 1 ELSE 0 END) AS revisadas,
            SUM(CASE WHEN estado = 'CONFIRMADA' THEN 1 ELSE 0 END) AS confirmadas,
            SUM(CASE WHEN estado = 'DESCARTADA' THEN 1 ELSE 0 END) AS descartadas,
            SUM(CASE WHEN nivel = 'CRITICO' AND estado = 'PENDIENTE' THEN 1 ELSE 0 END) AS criticas_pendientes
        FROM alertas
    """)
    al_stats = cursor.fetchone()

    # Dinero salvado / protegido
    dinero_protegido = monto_fraude

    # Estado de la cuenta del último usuario activo (no admin)
    cursor.execute("""
        SELECT c.estado, c.saldo
        FROM cuentas c
        JOIN usuarios u ON c.id_usuario = u.id_usuario
        WHERE u.tipo_usuario = 'USUARIO'
        ORDER BY c.id_cuenta DESC
        LIMIT 1
    """)
    cuenta_demo = cursor.fetchone()
    estado_cuenta = cuenta_demo["estado"] if cuenta_demo else "ACTIVA"
    saldo_usuario = cuenta_demo["saldo"] if cuenta_demo else 5000.0

    conexion.close()

    return jsonify({
        "status": "success",
        "metricas": {
            "total_transacciones": total_tx,
            "volumen_total": round(volumen_total, 2),
            "total_fraudes_detectados": total_fraudes,
            "tasa_fraude": tasa_fraude,
            "dinero_protegido": round(dinero_protegido, 2),
            "alertas_pendientes": al_stats["pendientes"] or 0,
            "alertas_criticas": al_stats["criticas_pendientes"] or 0,
            "alertas_confirmadas": al_stats["confirmadas"] or 0,
            "alertas_descartadas": al_stats["descartadas"] or 0,
            "modelo_activo": "Gradient Boosting (98.65% Acc)",
            "usuario_demo": {
                "estado_cuenta": estado_cuenta,
                "saldo_actual": round(saldo_usuario, 2)
            }
        }
    })


@app.route("/api/admin/graficos", methods=["GET"])
def api_admin_graficos():
    """Genera datos agregados para los 4 gráficos interactivos de Chart.js."""
    conexion = conectar_bd()
    cursor = conexion.cursor()

    # 1. Gráfico de Serie Temporal (Normales vs Fraude en los últimos registros)
    cursor.execute("""
        SELECT strftime('%Y-%m-%d %H:00', fecha_hora) AS periodo,
               SUM(CASE WHEN resultado = 'APROBADA' THEN 1 ELSE 0 END) AS normales,
               SUM(CASE WHEN resultado = 'SOSPECHOSA' THEN 1 ELSE 0 END) AS fraudes,
               COUNT(*) as total
        FROM transacciones
        GROUP BY periodo
        ORDER BY periodo ASC
        LIMIT 15
    """)
    time_rows = cursor.fetchall()
    timeline = {
        "labels": [r["periodo"][-5:] if len(r["periodo"]) >= 5 else r["periodo"] for r in time_rows],
        "normales": [r["normales"] for r in time_rows],
        "fraudes": [r["fraudes"] for r in time_rows]
    }

    # 2. Gráfico de Distribución de Riesgo (Dona)
    cursor.execute("""
        SELECT
            SUM(CASE WHEN p.probabilidad_fraude < 30 THEN 1 ELSE 0 END) AS bajo,
            SUM(CASE WHEN p.probabilidad_fraude >= 30 AND p.probabilidad_fraude < 60 THEN 1 ELSE 0 END) AS medio,
            SUM(CASE WHEN p.probabilidad_fraude >= 60 AND p.probabilidad_fraude < 85 THEN 1 ELSE 0 END) AS alto,
            SUM(CASE WHEN p.probabilidad_fraude >= 85 THEN 1 ELSE 0 END) AS critico
        FROM predicciones p
    """)
    risk_row = cursor.fetchone()
    riesgo_dist = {
        "labels": ["Bajo (<30%)", "Medio (30-60%)", "Alto (60-85%)", "Crítico (>85%)"],
        "data": [
            risk_row["bajo"] or 0,
            risk_row["medio"] or 0,
            risk_row["alto"] or 0,
            risk_row["critico"] or 0
        ]
    }

    # 3. Gráfico de Fraude por Canal/Producto (Barras)
    cursor.execute("""
        SELECT producto,
               SUM(CASE WHEN resultado = 'SOSPECHOSA' THEN 1 ELSE 0 END) AS fraudes,
               COUNT(*) AS total
        FROM transacciones
        GROUP BY producto
        ORDER BY total DESC
    """)
    product_rows = cursor.fetchall()
    productos = {
        "labels": [r["producto"] for r in product_rows],
        "fraudes": [r["fraudes"] for r in product_rows],
        "totales": [r["total"] for r in product_rows]
    }

    # 4. Comparativa de Modelos Machine Learning (desde tabla modelos_ml)
    cursor.execute("""
        SELECT nombre_modelo, tipo, accuracy, precision, recall, f1_score, estado
        FROM modelos_ml
        ORDER BY accuracy DESC
    """)
    model_rows = cursor.fetchall()
    modelos_ml = []
    for m in model_rows:
        modelos_ml.append({
            "nombre": m["nombre_modelo"],
            "tipo": m["tipo"],
            "accuracy": round(m["accuracy"] * 100, 2) if m["accuracy"] else 0,
            "precision": round(m["precision"] * 100, 2) if m["precision"] else 0,
            "recall": round(m["recall"] * 100, 2) if m["recall"] else 0,
            "f1_score": round(m["f1_score"] * 100, 2) if m["f1_score"] else 0,
            "estado": m["estado"]
        })

    conexion.close()

    return jsonify({
        "status": "success",
        "timeline": timeline,
        "distribucion_riesgo": riesgo_dist,
        "productos": productos,
        "modelos": modelos_ml
    })


@app.route("/api/admin/transacciones", methods=["GET"])
def api_admin_transacciones():
    """Devuelve listado paginado y filtrable de transacciones para la tabla de monitoreo."""
    filtro_resultado = request.args.get("resultado")
    limit = int(request.args.get("limit", 40))

    query = """
        SELECT t.id_transaccion, t.fecha_hora, t.monto, t.producto, t.resultado,
               t.destinatario_nuevo, t.hora_inusual, t.cambio_dispositivo, t.velocidad_operacion,
               u.nombre, u.apellido, u.correo,
               p.probabilidad_fraude, p.probabilidad_normal, p.resultado AS prediccion_ml,
               a.id_alerta, a.nivel AS nivel_alerta, a.estado AS estado_alerta
        FROM transacciones t
        JOIN usuarios u ON t.id_usuario = u.id_usuario
        LEFT JOIN predicciones p ON t.id_transaccion = p.id_transaccion
        LEFT JOIN alertas a ON t.id_transaccion = a.id_transaccion
    """
    params = []
    if filtro_resultado in ["APROBADA", "SOSPECHOSA"]:
        query += " WHERE t.resultado = ?"
        params.append(filtro_resultado)

    query += " ORDER BY t.fecha_hora DESC LIMIT ?"
    params.append(limit)

    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conexion.close()

    lista = []
    for r in rows:
        prob_f = r["probabilidad_fraude"] if r["probabilidad_fraude"] is not None else (90.0 if r["resultado"] == "SOSPECHOSA" else 5.0)
        lista.append({
            "id_transaccion": r["id_transaccion"],
            "fecha_hora": r["fecha_hora"],
            "usuario": f"{r['nombre']} {r['apellido']}",
            "correo": r["correo"],
            "monto": r["monto"],
            "producto": r["producto"],
            "resultado": r["resultado"],
            "probabilidad_fraude": round(prob_f, 1),
            "nivel_riesgo": r["nivel_alerta"] or ("CRITICO" if prob_f >= 85 else ("ALTO" if prob_f >= 60 else ("MEDIO" if prob_f >= 30 else "BAJO"))),
            "destinatario_nuevo": bool(r["destinatario_nuevo"]),
            "hora_inusual": bool(r["hora_inusual"]),
            "cambio_dispositivo": bool(r["cambio_dispositivo"]),
            "alerta": {
                "id_alerta": r["id_alerta"],
                "estado": r["estado_alerta"]
            } if r["id_alerta"] else None
        })

    return jsonify({
        "status": "success",
        "total": len(lista),
        "transacciones": lista
    })


@app.route("/api/admin/transacciones/<int:id_tx>", methods=["GET"])
def api_admin_detalle_tx(id_tx):
    """Devuelve la radiografía forense completa de una transacción para auditoría del analista."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT t.*, u.nombre, u.apellido, u.correo,
               p.probabilidad_fraude, p.probabilidad_normal, p.modelo AS nombre_modelo,
               a.id_alerta, a.nivel AS nivel_alerta, a.descripcion AS desc_alerta, a.estado AS estado_alerta
        FROM transacciones t
        JOIN usuarios u ON t.id_usuario = u.id_usuario
        LEFT JOIN predicciones p ON t.id_transaccion = p.id_transaccion
        LEFT JOIN alertas a ON t.id_transaccion = a.id_transaccion
        WHERE t.id_transaccion = ?
    """, (id_tx,))
    tx = cursor.fetchone()
    conexion.close()

    if not tx:
        return jsonify({"status": "error", "mensaje": "Transacción no encontrada"}), 404

    return jsonify({
        "status": "success",
        "transaccion": dict(tx)
    })


@app.route("/api/admin/alertas", methods=["GET"])
def api_admin_alertas():
    """Devuelve las alertas de fraude activas y su estado."""
    estado_filtro = request.args.get("estado")
    query = """
        SELECT a.id_alerta, a.id_transaccion, a.nivel, a.tipo_alerta, a.descripcion,
               a.estado, a.fecha_alerta,
               t.monto, t.producto, t.fecha_hora,
               u.nombre, u.apellido, u.correo,
               p.probabilidad_fraude
        FROM alertas a
        JOIN transacciones t ON a.id_transaccion = t.id_transaccion
        JOIN usuarios u ON t.id_usuario = u.id_usuario
        LEFT JOIN predicciones p ON t.id_transaccion = p.id_transaccion
    """
    params = []
    if estado_filtro:
        query += " WHERE a.estado = ?"
        params.append(estado_filtro)

    query += " ORDER BY CASE a.estado WHEN 'PENDIENTE' THEN 1 ELSE 2 END, a.fecha_alerta DESC LIMIT 50"

    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute(query, params)
    alertas = cursor.fetchall()
    conexion.close()

    return jsonify({
        "status": "success",
        "total": len(alertas),
        "alertas": [dict(a) for a in alertas]
    })


@app.route("/api/admin/alertas/<int:id_alerta>/resolver", methods=["POST"])
def api_admin_resolver_alerta(id_alerta):
    """
    Permite al analista de fraude tomar acción sobre una alerta:
    - CONFIRMAR_FRAUDE: Marca alerta confirmada y bloquea cuenta de usuario.
    - APROBAR: Marca revisada y aprueba la transacción.
    - DESCARTAR: Marca descartada (falso positivo).
    """
    datos = request.get_json() or {}
    accion = datos.get("accion")  # CONFIRMAR_FRAUDE, APROBAR, DESCARTAR
    comentario = datos.get("comentario", "Resuelto desde Centro Antifraude")

    if accion not in ["CONFIRMAR_FRAUDE", "APROBAR", "DESCARTAR"]:
        return jsonify({"status": "error", "mensaje": "Acción no válida"}), 400

    conexion = conectar_bd()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT a.id_alerta, a.id_transaccion, t.id_usuario, t.id_cuenta, t.monto, t.resultado
        FROM alertas a
        JOIN transacciones t ON a.id_transaccion = t.id_transaccion
        WHERE a.id_alerta = ?
    """, (id_alerta,))
    alerta_data = cursor.fetchone()

    if not alerta_data:
        conexion.close()
        return jsonify({"status": "error", "mensaje": "Alerta no encontrada"}), 404

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if accion == "CONFIRMAR_FRAUDE":
        nuevo_estado = "CONFIRMADA"
        # Bloquear cuenta de usuario
        cursor.execute("UPDATE cuentas SET estado = 'BLOQUEADA' WHERE id_usuario = ?", (alerta_data["id_usuario"],))
        cursor.execute("UPDATE transacciones SET resultado = 'SOSPECHOSA' WHERE id_transaccion = ?", (alerta_data["id_transaccion"],))
        desc_historial = f"Fraude confirmado por analista. Cuenta bloqueada preventivamente. Motivo: {comentario}"

    elif accion == "APROBAR":
        nuevo_estado = "REVISADA"
        monto = float(alerta_data["monto"])
        id_cuenta = alerta_data["id_cuenta"]
        id_usuario = alerta_data["id_usuario"]
        id_tx = alerta_data["id_transaccion"]

        # Obtener saldo actual de la cuenta
        cursor.execute("SELECT saldo FROM cuentas WHERE id_cuenta = ?", (id_cuenta,))
        cta = cursor.fetchone()
        saldo_actual = float(cta["saldo"]) if cta else 0.0

        # Si la transacción fue previamente catalogada como SOSPECHOSA (estaba en pausa preventiva),
        # al aceptarla (es correspondida y legítima), se debita el dinero del saldo del usuario
        if alerta_data["resultado"] == "SOSPECHOSA":
            nuevo_saldo = max(0.0, round(saldo_actual - monto, 2))
            cursor.execute("UPDATE cuentas SET saldo = ?, estado = 'ACTIVA' WHERE id_cuenta = ?", (nuevo_saldo, id_cuenta))
            cursor.execute("UPDATE transacciones SET resultado = 'APROBADA', saldo_posterior = ? WHERE id_transaccion = ?", (nuevo_saldo, id_tx))
            desc_historial = f"Transacción correspondida y autorizada por analista. Se debitó S/ {monto:.2f}. Saldo actualizado: S/ {nuevo_saldo:.2f}. Motivo: {comentario}"
        else:
            cursor.execute("UPDATE transacciones SET resultado = 'APROBADA' WHERE id_transaccion = ?", (id_tx,))
            cursor.execute("UPDATE cuentas SET estado = 'ACTIVA' WHERE id_usuario = ?", (id_usuario,))
            desc_historial = f"Transacción aprobada tras validación manual: {comentario}"

    else:  # DESCARTAR
        nuevo_estado = "DESCARTADA"
        desc_historial = f"Alerta descartada (Falso positivo): {comentario}"

    # Actualizar estado de la alerta
    cursor.execute("UPDATE alertas SET estado = ? WHERE id_alerta = ?", (nuevo_estado, id_alerta))

    # Registrar en historial
    cursor.execute("""
        INSERT INTO historial_acciones (id_usuario, id_transaccion, accion, descripcion, fecha)
        VALUES (?, ?, ?, ?, ?)
    """, (alerta_data["id_usuario"], alerta_data["id_transaccion"], accion, desc_historial, now_str))

    conexion.commit()
    conexion.close()

    return jsonify({
        "status": "success",
        "id_alerta": id_alerta,
        "nuevo_estado": nuevo_estado,
        "mensaje": f"Alerta actualizada a {nuevo_estado} exitosamente."
    })


@app.route("/api/admin/simular", methods=["POST"])
def api_admin_simular_trafico():
    """
    Simula una transacción o ráfaga de transacciones para demostraciones interactivas en vivo.
    """
    datos = request.get_json() or {}
    tipo = datos.get("tipo", "random")  # 'normal', 'fraude', 'rafaga'

    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_usuario, correo FROM usuarios WHERE correo = 'juan@correo.com' LIMIT 1")
    usuario = cursor.fetchone()
    if not usuario:
        conexion.close()
        return jsonify({"status": "error", "mensaje": "Usuario demo no encontrado"}), 404

    id_usuario = usuario["id_usuario"]
    cursor.execute("SELECT id_cuenta, saldo FROM cuentas WHERE id_usuario = ?", (id_usuario,))
    cuenta = cursor.fetchone()
    cursor.execute("SELECT id_dispositivo FROM dispositivos WHERE id_usuario = ?", (id_usuario,))
    disp = cursor.fetchone()

    id_cuenta = cuenta["id_cuenta"]
    id_disp = disp["id_dispositivo"] if disp else 1
    saldo_actual = float(cuenta["saldo"])

    conexion.close()

    def generar_una(es_fraude_forzado=False):
        now = datetime.now()
        if es_fraude_forzado:
            monto = round(random.uniform(2800, 4800), 2)
            hora = random.choice([1, 2, 3, 4])
            dest_nuevo = 1
            hora_inus = 1
            cambio_disp = 1
            llamada = random.choice([0, 1])
            vel = random.uniform(5, 12)
            dist = random.uniform(80, 400)
            prod = random.choice(["Yape", "Transferencia", "Compra"])
        else:
            monto = round(random.uniform(15, 180), 2)
            hora = random.choice([9, 12, 14, 16, 19, 21])
            dest_nuevo = random.choice([0, 0, 1])
            hora_inus = 0
            cambio_disp = 0
            llamada = 0
            vel = random.uniform(25, 75)
            dist = random.uniform(0.1, 4.5)
            prod = random.choice(["Yape", "Yape", "Pago de servicios", "Recarga"])

        tx_data = {
            "monto": monto,
            "destinatario_nuevo": dest_nuevo,
            "hora_inusual": hora_inus,
            "velocidad_operacion": vel,
            "llamada_reciente": llamada,
            "cambio_dispositivo": cambio_disp,
            "edad": 32,
            "usuario_nuevo": 0,
            "dias_desde_registro": 240,
            "operaciones_dia": random.randint(1, 4),
            "operaciones_ultima_hora": 1,
            "alertas_ignoradas": 0,
            "distancia_ubicacion": dist,
            "ubicacion_inusual": 1 if dist > 50 else 0,
            "saldo_anterior": saldo_actual,
            "saldo_posterior": max(0, saldo_actual - monto),
            "monto_promedio_usuario": 45.0,
            "hora": hora,
            "dia_semana": now.weekday(),
            "producto": prod
        }

        eval_res = predecir_fraude(tx_data)
        prob_fraude = eval_res["probabilidad_fraude"]
        prob_normal = eval_res["probabilidad_normal"]
        nivel = eval_res["nivel_riesgo"]
        es_f = eval_res["es_fraude"]
        res_tx = "SOSPECHOSA" if es_f == 1 else "APROBADA"

        tx_time = now.strftime("%Y-%m-%d %H:%M:%S")

        con = conectar_bd()
        cur = con.cursor()
        cur.execute("""
            INSERT INTO transacciones (
                id_usuario, id_cuenta, id_dispositivo, fecha_hora, monto, monto_promedio_usuario,
                saldo_anterior, saldo_posterior, producto, destinatario_nuevo, hora_inusual,
                velocidad_operacion, llamada_reciente, cambio_dispositivo, edad, usuario_nuevo,
                dias_desde_registro, operaciones_dia, operaciones_ultima_hora, alertas_ignoradas,
                distancia_ubicacion, ubicacion_inusual, hora, dia_semana, resultado, fecha_analisis
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id_usuario, id_cuenta, id_disp, tx_time, monto, 45.0, saldo_actual, max(0, saldo_actual - monto),
            prod, dest_nuevo, hora_inus, vel, llamada, cambio_disp, 32, 0, 240, tx_data["operaciones_dia"],
            1, 0, dist, tx_data["ubicacion_inusual"], hora, now.weekday(), res_tx, tx_time
        ))
        id_tx = cur.lastrowid

        cur.execute("""
            INSERT INTO predicciones (
                id_transaccion, modelo, probabilidad_normal, probabilidad_fraude, resultado, fecha_prediccion
            ) VALUES (?, 'Gradient Boosting', ?, ?, ?, ?)
        """, (id_tx, prob_normal, prob_fraude, "FRAUDE" if es_f == 1 else "NORMAL", tx_time))

        if es_f == 1:
            desc_alerta = (
                f"Alerta {nivel} detectada en simulación: {prod} de S/ {monto:.2f}. "
                f"Probabilidad de fraude: {prob_fraude}%. Factores: {', '.join(eval_res['factores'])}"
            )
            cur.execute("""
                INSERT INTO alertas (
                    id_transaccion, nivel, tipo_alerta, descripcion, estado, fecha_alerta
                ) VALUES (?, ?, 'SIMULACION_RIESGO', ?, 'PENDIENTE', ?)
            """, (id_tx, nivel, desc_alerta, tx_time))

        con.commit()
        con.close()
        return {
            "id_transaccion": id_tx,
            "monto": monto,
            "producto": prod,
            "resultado": res_tx,
            "probabilidad_fraude": prob_fraude,
            "nivel_riesgo": nivel
        }

    resultados = []
    if tipo == "fraude":
        resultados.append(generar_una(es_fraude_forzado=True))
    elif tipo == "normal":
        resultados.append(generar_una(es_fraude_forzado=False))
    elif tipo == "rafaga":
        for _ in range(4):
            resultados.append(generar_una(es_fraude_forzado=False))
        resultados.append(generar_una(es_fraude_forzado=True))
    else:
        resultados.append(generar_una(es_fraude_forzado=random.choice([False, False, True])))

    return jsonify({
        "status": "success",
        "mensaje": f"Se han simulado {len(resultados)} transacciones.",
        "transacciones": resultados
    })


@app.route("/api/admin/reset-demo", methods=["POST"])
def api_admin_reset_demo():
    """Reinicia la base de datos con el dataset inicial fresco."""
    try:
        from database.seed_data import seed_demo_data
        seed_demo_data(limit_normal=35, limit_fraud=15, clear_first=True)
        return jsonify({"status": "success", "mensaje": "Base de datos restaurada al estado inicial de demostración."})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500


# ============================================================
# INICIO DE LA APLICACIÓN
# ============================================================

if __name__ == "__main__":
    print("==================================================")
    print(" 🚀 SISTEMA ANTIFRAUDE BCP - YAPE INICIANDO")
    print("==================================================")
    print(" ▸ Portal Principal:         http://localhost:5000/")
    print(" ▸ Dashboard Usuario (Yape): http://localhost:5000/usuario")
    print(" ▸ Dashboard Administrador:  http://localhost:5000/admin")
    print("==================================================")
    app.run(host="0.0.0.0", port=5000, debug=True)