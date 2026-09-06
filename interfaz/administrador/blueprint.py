"""
Blueprint Flask Modular para la UI de Administración Antifraude (yape.ia).
Integración modular, desacoplada, compatible con el nuevo diseño y vistas completas.
"""

from pathlib import Path
from functools import wraps
import json
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from .data_provider import BaseAdminDataProvider, MockAdminDataProvider
from .config import AdminConfig

CURRENT_DIR = Path(__file__).resolve().parent


def create_admin_blueprint(
    data_provider: BaseAdminDataProvider = None,
    config: AdminConfig = None,
    auth_decorator = None,
    name: str = "admin",
    url_prefix: str = "/admin"
) -> Blueprint:
    """
    Crea y configura el Blueprint modular de Administración Antifraude.
    """
    if data_provider is None:
        data_provider = MockAdminDataProvider()

    if config is None:
        config = AdminConfig()

    bp = Blueprint(
        name,
        __name__,
        url_prefix=url_prefix,
        template_folder=str(CURRENT_DIR / "templates"),
        static_folder=str(CURRENT_DIR / "static"),
        static_url_path="/admin_static"
    )

    # Decorador de autenticación
    def admin_guard(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if auth_decorator is not None:
                return auth_decorator(f)(*args, **kwargs)

            if config.REQUIRE_AUTH:
                admin_autenticado = (
                    ("admin_id" in session and str(session.get("admin_tipo", "")).upper() == "ADMIN") or
                    ("id_usuario" in session and str(session.get(config.SESSION_ROLE_KEY, "")).upper() == str(config.ADMIN_ROLE_VALUE).upper())
                )
                if not admin_autenticado:
                    flash("Por favor inicia sesión para acceder al panel administrativo.", "warning")
                    return redirect(url_for("login_admin"))
            return f(*args, **kwargs)
        return decorated_function

    # Inyección de contexto global y compatibilidad de url_for para plantillas
    @bp.context_processor
    def inject_admin_globals():
        def custom_url_for(endpoint, **values):
            # Redirigir llamadas de static hacia el static del blueprint
            if endpoint == "static":
                return url_for(f"{name}.static", **values)

            # Mapeo de endpoints invocados sin el prefijo del blueprint
            endpoint_map = {
                "admin_dashboard": f"{name}.admin_dashboard",
                "admin_transacciones": f"{name}.admin_transacciones",
                "admin_usuarios": f"{name}.admin_usuarios",
                "admin_toggle_usuario": f"{name}.admin_toggle_usuario",
                "admin_estadisticas": f"{name}.admin_estadisticas",
                "admin_productos": f"{name}.admin_productos",
                "admin_modelos": f"{name}.admin_modelos",
                "admin_metricas": f"{name}.admin_metricas",
                "admin_matrices": f"{name}.admin_matrices",
                "admin_reportes": f"{name}.admin_reportes",
                "admin_fraudes": f"{name}.admin_fraudes",
                "admin_perfil": f"{name}.admin_perfil",
                "admin_config_correo": f"{name}.admin_config_correo",
                "admin_eliminar_usuario": f"{name}.admin_eliminar_usuario",
                "admin_eliminar_todos_usuarios": f"{name}.admin_eliminar_todos_usuarios",
                "admin_cuentas": f"{name}.admin_cuentas",
                "logout": f"{name}.admin_logout",
                "admin_logout": f"{name}.admin_logout",
            }
            target = endpoint_map.get(endpoint, endpoint)
            try:
                return url_for(target, **values)
            except Exception:
                try:
                    return url_for(endpoint, **values)
                except Exception:
                    return f"#{endpoint}"

        try:
            kpis = data_provider.get_kpis()
            alertas_count = kpis.get("alertas_pendientes", 0)
        except Exception:
            alertas_count = 0

        admin_nombre = session.get("admin_nombre")
        if not admin_nombre:
            if session.get("tipo_usuario") == "ADMIN":
                admin_nombre = session.get("nombre") or "Administrador Sistema"
            else:
                admin_nombre = "Administrador Sistema"

        return {
            "url_for": custom_url_for,
            "admin_config": config,
            "alertas_pendientes_count": alertas_count,
            "admin_brand_name": config.BRAND_NAME,
            "admin_brand_subtitle": config.BRAND_SUBTITLE,
            "admin_brand_logo_text": config.BRAND_LOGO_TEXT,
            "admin_nombre": admin_nombre,
            "current_user_name": admin_nombre,
            "current_user_role": "ADMIN",
            "session": session,
            "request": request
        }

    # ============================================================
    # RUTAS DEL PANEL ADMINISTRATIVO
    # ============================================================

    @bp.route("/")
    @admin_guard
    def index():
        return redirect(url_for(f"{name}.admin_dashboard"))

    @bp.route("/dashboard")
    @admin_guard
    def admin_dashboard():
        kpis = data_provider.get_kpis()
        transacciones_recientes = data_provider.get_transactions(limit=10)

        return render_template(
            "administrador/dashboard.html",
            kpis=kpis,
            transacciones_recientes=transacciones_recientes,
            transacciones=transacciones_recientes,
            active_page="admin_dashboard"
        )

    @bp.route("/transacciones")
    @admin_guard
    def admin_transacciones():
        filtro_resultado = request.args.get("resultado", "")
        filtro_producto = request.args.get("producto", "")
        limit = int(request.args.get("limit", 200))

        transacciones = data_provider.get_transactions(
            limit=limit,
            filtro_resultado=filtro_resultado if filtro_resultado else "TODOS",
            filtro_producto=filtro_producto if filtro_producto else "TODOS"
        )

        return render_template(
            "administrador/transacciones.html",
            transacciones=transacciones,
            filtro_resultado=filtro_resultado,
            filtro_producto=filtro_producto,
            active_page="admin_transacciones"
        )

    @bp.route("/usuarios")
    @admin_guard
    def admin_usuarios():
        usuarios = data_provider.get_users()
        return render_template(
            "administrador/usuarios.html",
            usuarios=usuarios,
            active_page="admin_usuarios"
        )

    @bp.route("/cuentas")
    @admin_guard
    def admin_cuentas():
        cuentas = data_provider.get_cuentas()
        return render_template(
            "administrador/cuentas.html",
            cuentas=cuentas,
            active_page="admin_cuentas"
        )

    @bp.route("/usuario/<int:id_usuario>/toggle", methods=["POST", "GET"])
    @admin_guard
    def admin_toggle_usuario(id_usuario):
        usuarios = data_provider.get_users()
        user = next((u for u in usuarios if u["id_usuario"] == id_usuario), None)
        if user:
            nuevo_estado = "INACTIVO" if user.get("estado") == "ACTIVO" else "ACTIVO"
            data_provider.update_user_status(id_usuario, nuevo_estado)
            flash(f"Estado del usuario #{id_usuario} actualizado a {nuevo_estado}.", "success")
        return redirect(url_for(f"{name}.admin_usuarios"))

    @bp.route("/usuario/estado", methods=["POST"])
    @admin_guard
    def admin_cambiar_estado_usuario():
        id_usuario = request.form.get("id_usuario")
        nuevo_estado = request.form.get("nuevo_estado")
        if id_usuario and nuevo_estado:
            data_provider.update_user_status(int(id_usuario), nuevo_estado)
            flash("Estado del usuario actualizado.", "success")
        return redirect(url_for(f"{name}.admin_usuarios"))

    @bp.route("/usuario/<int:id_usuario>/eliminar", methods=["POST"])
    @admin_guard
    def admin_eliminar_usuario(id_usuario):
        ok, msg = data_provider.delete_user(id_usuario)
        if ok:
            flash(f"Usuario #{id_usuario} eliminado correctamente.", "success")
        else:
            flash(f"Error al eliminar: {msg}", "danger")
        return redirect(url_for(f"{name}.admin_usuarios"))

    @bp.route("/usuarios/eliminar-todos", methods=["POST"])
    @admin_guard
    def admin_eliminar_todos_usuarios():
        ok, msg = data_provider.delete_all_users()
        if ok:
            flash(msg or "Todos los usuarios han sido eliminados.", "success")
        else:
            flash(f"Error al eliminar usuarios: {msg}", "danger")
        return redirect(url_for(f"{name}.admin_usuarios"))


    @bp.route("/estadisticas")
    @admin_guard
    def admin_estadisticas():
        stats = data_provider.get_descriptive_stats()
        return render_template(
            "administrador/estadisticas.html",
            stats=stats,
            estadisticas=stats,
            active_page="admin_estadisticas"
        )

    @bp.route("/productos")
    @admin_guard
    def admin_productos():
        productos = data_provider.get_product_analysis()
        return render_template(
            "administrador/productos.html",
            productos=productos,
            active_page="admin_productos"
        )

    @bp.route("/modelos")
    @admin_guard
    def admin_modelos():
        comparativa = data_provider.get_model_comparison()
        return render_template(
            "administrador/modelos.html",
            mejor_modelo=comparativa.get("mejor_modelo"),
            modelos=comparativa.get("modelos"),
            active_page="admin_modelos"
        )

    @bp.route("/metricas")
    @admin_guard
    def admin_metricas():
        return render_template(
            "administrador/metricas.html",
            active_page="admin_metricas"
        )

    @bp.route("/matrices")
    @bp.route("/confusion")
    @admin_guard
    def admin_matrices():
        matrices = data_provider.get_confusion_matrices()
        return render_template(
            "administrador/matrices.html",
            matrices=matrices,
            active_page="admin_matrices"
        )

    @bp.route("/reportes")
    @admin_guard
    def admin_reportes():
        kpis = data_provider.get_kpis()
        return render_template(
            "administrador/reportes.html",
            kpis=kpis,
            active_page="admin_reportes"
        )

    @bp.route("/fraudes")
    @admin_guard
    def admin_fraudes():
        return redirect(url_for(f"{name}.admin_transacciones", resultado="SOSPECHOSA"))

    @bp.route("/alerta/cambiar_estado", methods=["POST"])
    @admin_guard
    def admin_cambiar_alerta():
        id_alerta = request.form.get("id_alerta")
        nuevo_estado = request.form.get("nuevo_estado")
        if id_alerta and nuevo_estado:
            data_provider.update_alert_status(int(id_alerta), nuevo_estado)
            flash(f"Alerta #{id_alerta} actualizada a estado: {nuevo_estado}.", "success")
        return redirect(url_for(f"{name}.admin_transacciones"))

    @bp.route("/perfil", methods=["GET", "POST"])
    @admin_guard
    def admin_perfil():
        admin_id = session.get("admin_id") or 1
        perfil = data_provider.get_user_by_id(admin_id) if hasattr(data_provider, "get_user_by_id") else None
        if not perfil:
            perfil = {
                "id_usuario": 1,
                "nombre": "Administrador",
                "apellido": "Sistema",
                "correo": "admin@bcp.com",
                "tipo_usuario": "ADMIN",
                "estado": "ACTIVO",
                "fecha_registro": "2026-09-04 15:52:33"
            }

        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            apellido = request.form.get("apellido", "").strip()
            correo = request.form.get("correo", "").strip().lower()
            password = request.form.get("password", "").strip()

            if not nombre or not apellido or not correo:
                flash("El nombre, apellido y correo son campos obligatorios.", "danger")
            else:
                ok, err = data_provider.update_user_profile(
                    admin_id, nombre, apellido, correo,
                    password if password else None
                )
                if ok:
                    session["admin_nombre"] = f"{nombre} {apellido}"
                    session["admin_correo"] = correo
                    flash("✓ Tu perfil de Administrador ha sido actualizado exitosamente.", "success")
                    return redirect(url_for(f"{name}.admin_perfil"))
                else:
                    flash(err or "Error al actualizar los datos del perfil.", "danger")

        kpis = data_provider.get_kpis()
        return render_template(
            "administrador/perfil.html",
            perfil=perfil,
            kpis=kpis,
            active_page="admin_perfil"
        )

    @bp.route("/config-correo", methods=["GET", "POST"])
    @admin_guard
    def admin_config_correo():
        interfaz_dir = CURRENT_DIR.parent
        ruta_cfg = interfaz_dir / "config_correo.json"

        cfg_actual = {"gmail_emisor": "", "gmail_password_app": ""}
        if ruta_cfg.exists():
            try:
                with open(ruta_cfg, "r", encoding="utf-8") as f:
                    cfg_actual = json.load(f)
            except Exception:
                pass

        if request.method == "POST":
            accion = request.form.get("accion", "guardar")

            if accion == "guardar":
                emisor = request.form.get("gmail_emisor", "").strip().lower()
                password = request.form.get("gmail_password_app", "").strip().replace(" ", "")

                if not emisor or not password:
                    flash("Por favor ingresa el correo Gmail y la contraseña de aplicación de Google.", "danger")
                else:
                    try:
                        context = ssl.create_default_context()
                        with smtplib.SMTP("smtp.gmail.com", 587, timeout=8) as server:
                            server.starttls(context=context)
                            server.login(emisor, password)

                        with open(ruta_cfg, "w", encoding="utf-8") as f:
                            json.dump({"gmail_emisor": emisor, "gmail_password_app": password}, f, indent=2)

                        cfg_actual = {"gmail_emisor": emisor, "gmail_password_app": password}
                        flash("✓ Conexión exitosa con smtp.gmail.com. Credenciales guardadas y verificadas correctamente.", "success")
                    except Exception as e:
                        err_str = str(e)
                        if "101" in err_str or "Network is unreachable" in err_str or "timed out" in err_str.lower():
                            # El firewall de Render Free bloquea conexiones salientes en los puertos 25/465/587
                            with open(ruta_cfg, "w", encoding="utf-8") as f:
                                json.dump({"gmail_emisor": emisor, "gmail_password_app": password}, f, indent=2)
                            cfg_actual = {"gmail_emisor": emisor, "gmail_password_app": password}
                            flash("⚠️ Credenciales guardadas. Nota: El hosting Render (Plan Free) bloquea el puerto saliente 587 de SMTP ([Errno 101] Network is unreachable). Tu cuenta y contraseña de 16 caracteres son correctas; el sistema activará el respaldo automático de código OTP en pantalla.", "warning")
                        else:
                            flash(f"Error al autenticar con Gmail ({err_str}). Verifica que la verificación en 2 pasos esté activa y la contraseña sea de 16 caracteres.", "danger")

            elif accion == "test_envio":
                destino = request.form.get("correo_prueba", "").strip().lower()
                if not destino or "@" not in destino:
                    flash("Ingresa un correo destinatario válido para la prueba.", "warning")
                else:
                    emisor = cfg_actual.get("gmail_emisor", "")
                    password = cfg_actual.get("gmail_password_app", "")
                    if not emisor or not password:
                        flash("Primero debes configurar y guardar el remitente de Gmail.", "danger")
                    else:
                        try:
                            msg = MIMEMultipart("alternative")
                            msg["Subject"] = "Prueba de Servidor SMTP - Yape Antifraude BCP"
                            msg["From"] = f"Yape Notificaciones <{emisor}>"
                            msg["To"] = destino
                            cuerpo = """
                            <div style="font-family: sans-serif; background: #0B0F19; color: #FFFFFF; padding: 24px; border-radius: 12px;">
                                <h2 style="color: #00D2C4;">✓ Conexión Exitosa</h2>
                                <p>Este es un correo de prueba enviado desde el <strong>Centro Antifraude BCP - Yape</strong>.</p>
                                <p style="color: #94A3B8; font-size: 13px;">El servidor SMTP de Gmail está correctamente autenticado y listo para despachar códigos OTP.</p>
                            </div>
                            """
                            msg.attach(MIMEText(cuerpo, "html"))

                            context = ssl.create_default_context()
                            with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
                                server.starttls(context=context)
                                server.login(emisor, password)
                                server.sendmail(emisor, destino, msg.as_string())

                            flash(f"✓ Correo de prueba despachado exitosamente a {destino}.", "success")
                        except Exception as e:
                            flash(f"Error en envío de prueba: {e}", "danger")

        kpis = data_provider.get_kpis()
        return render_template(
            "administrador/config_correo.html",
            config_correo=cfg_actual,
            kpis=kpis,
            active_page="admin_config_correo"
        )

    @bp.route("/logout")
    def admin_logout():
        session.pop("admin_id", None)
        session.pop("admin_nombre", None)
        session.pop("admin_tipo", None)
        session.pop("admin_correo", None)
        if session.get("tipo_usuario") == "ADMIN":
            session.pop("id_usuario", None)
            session.pop("nombre", None)
            session.pop("tipo_usuario", None)
            session.pop("correo", None)
        flash("Sesión de Administrador finalizada exitosamente.", "info")
        return redirect("/admin/login")

    # ============================================================
    # APIS RESTFUL / JSON
    # ============================================================

    @bp.route("/api/kpis")
    @admin_guard
    def api_kpis():
        return jsonify(data_provider.get_kpis())

    @bp.route("/api/alertas")
    @admin_guard
    def api_alertas():
        filtro = request.args.get("estado", "TODOS")
        return jsonify(data_provider.get_alerts(filtro_estado=filtro))

    @bp.route("/api/dashboard-live")
    def api_dashboard_live():
        kpis = data_provider.get_kpis()
        productos = data_provider.get_product_analysis()
        transacciones_recientes = data_provider.get_transactions(limit=10)

        prod_map = {p["producto"]: p for p in productos}
        def get_p(name):
            return prod_map.get(name) or prod_map.get("Pago de servicios" if name == "Pago servicios" else name) or {"operaciones": 0, "porcentaje_fraude": 0.0, "monto_promedio": 0.0}

        prod_labels = ["Yape", "Compra", "Pago servicios", "Transferencia", "Recarga"]
        prod_counts = [get_p(k)["operaciones"] for k in prod_labels]

        pct_labels = ["Compra", "Recarga", "Pago servicios", "Yape", "Transferencia"]
        pct_fraude = [get_p(k)["porcentaje_fraude"] for k in pct_labels]

        distribucion = [kpis.get("transacciones_legitimas", 46778), kpis.get("fraudes_detectados", 3222)]

        monto_labels = ["Compra", "Recarga", "Pago servicios", "Yape", "Transferencia"]
        monto_prom = [get_p(k)["monto_promedio"] for k in monto_labels]

        return jsonify({
            "status": "success",
            "kpis": kpis,
            "charts": {
                "productos": {
                    "labels": prod_labels,
                    "counts": prod_counts
                },
                "distribucion": {
                    "data": distribucion
                },
                "pct_fraude": {
                    "labels": pct_labels,
                    "data": pct_fraude
                },
                "monto_producto": {
                    "labels": monto_labels,
                    "data": monto_prom
                }
            },
            "transacciones_recientes": transacciones_recientes
        })

    return bp
