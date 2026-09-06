"""
Demo independiente del Módulo UI de Administración.
Permite visualizar y probar todas las vistas del panel de administración
con datos simulados sin requerir bases de datos ni modelos de ML.
Uso:
    pip install flask
    python demo_servidor.py
"""
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "admin_demo_secret_key"

@app.before_request
def fake_session():
    # Simular usuario Administrador en sesión
    if "id_usuario" not in session:
        session["id_usuario"] = 1
        session["nombre"] = "Administrador"
        session["tipo_usuario"] = "ADMIN"
        session["tema"] = "light"

@app.route("/")
def index():
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/dashboard")
def admin_dashboard():
    kpis = {
        "total_transacciones": 50000,
        "total_fraudes": 3222,
        "tasa_fraude": 6.44,
        "monto_total": 20169500.0,
        "monto_fraude": 1300250.0,
        "total_usuarios": 150,
        "usuarios_activos": 142
    }
    ultimas_transacciones = [
        {"id_transaccion": 5001, "nombre": "Carlos", "apellido": "Gomez", "producto": "Yape Directo", "monto": 850.0, "probabilidad_fraude": 0.89, "es_fraude": 1, "fecha_transaccion": "2026-09-05 21:00"},
        {"id_transaccion": 5002, "nombre": "Maria", "apellido": "Lopez", "producto": "Compra", "monto": 45.0, "probabilidad_fraude": 0.04, "es_fraude": 0, "fecha_transaccion": "2026-09-05 20:55"},
        {"id_transaccion": 5003, "nombre": "Juan", "apellido": "Perez", "producto": "Servicios", "monto": 120.0, "probabilidad_fraude": 0.08, "es_fraude": 0, "fecha_transaccion": "2026-09-05 20:48"},
        {"id_transaccion": 5004, "nombre": "Roberto", "apellido": "Diaz", "producto": "Transferencia", "monto": 3500.0, "probabilidad_fraude": 0.94, "es_fraude": 1, "fecha_transaccion": "2026-09-05 20:30"},
    ]
    return render_template("administrador/dashboard.html", kpis=kpis, transacciones=ultimas_transacciones)

@app.route("/admin/transacciones")
def admin_transacciones():
    lista = [
        {"id_transaccion": i, "id_usuario": 100+i, "nombre": f"Usuario {i}", "apellido": "Test", "monto": 150.0 + i*10, "producto": "Yape Directo", "es_fraude": 1 if i % 4 == 0 else 0, "probabilidad_fraude": 0.91 if i % 4 == 0 else 0.05, "estado": "BLOQUEADA" if i % 4 == 0 else "APROBADA", "fecha_transaccion": "2026-09-05 20:00"}
        for i in range(1, 25)
    ]
    return render_template("administrador/transacciones.html", transacciones=lista, pagina=1, total_paginas=5)

@app.route("/admin/usuarios")
def admin_usuarios():
    usuarios = [
        {"id_usuario": 1, "nombre": "Administrador", "apellido": "Sistema", "correo": "admin@bcp.com", "tipo_usuario": "ADMIN", "estado": "ACTIVO", "fecha_registro": "2026-01-10", "total_operaciones": 450},
        {"id_usuario": 2, "nombre": "Juan", "apellido": "Perez", "correo": "juan@correo.com", "tipo_usuario": "USUARIO", "estado": "ACTIVO", "fecha_registro": "2026-02-15", "total_operaciones": 89},
        {"id_usuario": 3, "nombre": "Ana", "apellido": "Torres", "correo": "ana@correo.com", "tipo_usuario": "USUARIO", "estado": "INACTIVO", "fecha_registro": "2026-03-01", "total_operaciones": 12},
    ]
    return render_template("administrador/usuarios.html", usuarios=usuarios)

@app.route("/admin/usuario/<int:id_usuario>/toggle", methods=["POST"])
def admin_toggle_usuario(id_usuario):
    return redirect(url_for("admin_usuarios"))

@app.route("/admin/estadisticas")
def admin_estadisticas():
    stats = [
        {"Variable": "monto", "count": 50000, "mean": 403.39, "std": 521.14, "min": 5.0, "25%": 75.0, "50%": 246.68, "75%": 520.0, "max": 9980.0},
        {"Variable": "velocidad_operacion", "count": 50000, "mean": 42.1, "std": 18.3, "min": 3.0, "25%": 28.0, "50%": 41.0, "75%": 56.0, "max": 180.0},
    ]
    return render_template("administrador/estadisticas.html", estadisticas=stats)

@app.route("/admin/productos")
def admin_productos():
    productos = [
        {"producto": "Compra", "total": 9945, "fraudes": 666, "tasa_fraude": 6.70, "monto_promedio": 380.5},
        {"producto": "Recarga", "total": 5024, "fraudes": 336, "tasa_fraude": 6.69, "monto_promedio": 45.2},
        {"producto": "Yape Directo", "total": 25010, "fraudes": 1590, "tasa_fraude": 6.36, "monto_promedio": 120.0},
        {"producto": "Servicios", "total": 10021, "fraudes": 630, "tasa_fraude": 6.29, "monto_promedio": 210.8},
    ]
    return render_template("administrador/productos.html", productos=productos)

@app.route("/admin/modelos")
def admin_modelos():
    modelos = [
        {"Modelo": "Gradient Boosting", "Accuracy": 0.9821, "Precision": 0.9412, "Recall": 0.9125, "F1-Score": 0.9266, "ROC-AUC": 0.9882, "Estado": "En Producción"},
        {"Modelo": "Red Neuronal PyTorch", "Accuracy": 0.9785, "Precision": 0.9230, "Recall": 0.8950, "F1-Score": 0.9088, "ROC-AUC": 0.9810, "Estado": "Evaluado"},
        {"Modelo": "Red Neuronal TensorFlow", "Accuracy": 0.9772, "Precision": 0.9180, "Recall": 0.8890, "F1-Score": 0.9033, "ROC-AUC": 0.9795, "Estado": "Evaluado"},
    ]
    return render_template("administrador/modelos.html", modelos=modelos)

@app.route("/admin/metricas")
def admin_metricas():
    return render_template("administrador/metricas.html")

@app.route("/admin/matrices")
def admin_matrices():
    matrices = {
        "gradient_boosting": [
            {"": "Real: Legítimo", "Pred: Legítimo": 9320, "Pred: Fraude": 36},
            {"": "Real: Fraude", "Pred: Legítimo": 56, "Pred: Fraude": 588}
        ]
    }
    return render_template("administrador/matrices.html", matrices=matrices)

@app.route("/admin/reportes")
def admin_reportes():
    return render_template("administrador/reportes.html")

@app.route("/api/tema", methods=["POST"])
def api_tema():
    data = request.get_json() or {}
    session["tema"] = data.get("tema", "light")
    return jsonify({"success": True, "tema": session["tema"]})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    print("Iniciando Demo UI Admin en http://localhost:5050 ...")
    app.run(host="0.0.0.0", port=5050, debug=True)
