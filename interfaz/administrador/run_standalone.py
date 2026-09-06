"""
Servidor Standalone / Demostración del Módulo de Administración.
Permite ejecutar y previsualizar toda la UI del Administrador de forma 100% independiente.

Uso:
    python run_standalone.py
    (Abrir en navegador: http://127.0.0.1:5050)
"""

import os
import sys
from pathlib import Path
from flask import Flask, redirect, url_for

# Asegurar importación del paquete actual
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))
sys.path.insert(0, str(CURRENT_DIR.parent))

try:
    from blueprint import create_admin_blueprint
    from data_provider import MockAdminDataProvider, SQLiteAdminDataProvider
    from config import AdminConfig
except Exception:
    from administrador.blueprint import create_admin_blueprint
    from administrador.data_provider import MockAdminDataProvider, SQLiteAdminDataProvider
    from administrador.config import AdminConfig

def create_standalone_app():
    app = Flask(__name__)
    app.secret_key = "admin_standalone_demo_secret_key_2026"

    # Verificar si existe base de datos SQLite en rutas típicas o usar Mock
    db_candidates = [
        CURRENT_DIR.parent / "database" / "fraude_yape.db",
        CURRENT_DIR.parent / "interfaz" / "database" / "fraude_yape.db",
        CURRENT_DIR / "fraude_yape.db"
    ]
    
    db_path = next((p for p in db_candidates if p.exists()), None)

    if db_path:
        print(f"[*] Conectado a base de datos SQLite: {db_path}")
        provider = SQLiteAdminDataProvider(str(db_path))
    else:
        print("[*] Usando MockAdminDataProvider (Modo Demo con datos simulados)")
        provider = MockAdminDataProvider()

    config = AdminConfig()
    config.REQUIRE_AUTH = False  # En modo standalone no requerimos login previo

    # Registrar el Blueprint en la raíz o en /admin
    admin_bp = create_admin_blueprint(
        data_provider=provider,
        config=config,
        url_prefix="/admin"
    )
    app.register_blueprint(admin_bp)

    @app.route("/")
    def root():
        return redirect(url_for("admin.admin_dashboard"))

    return app

if __name__ == "__main__":
    app = create_standalone_app()
    port = int(os.environ.get("PORT", 5050))
    print("\n" + "=" * 65)
    print("  PANEL DE ADMINISTRACION INDEPENDIENTE - INICIADO")
    print(f"  Accede en tu navegador: http://127.0.0.1:{port}")
    print("=" * 65 + "\n")
    app.run(debug=True, host="0.0.0.0", port=port)
