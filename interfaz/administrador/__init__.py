"""
Módulo Independiente de Administración Antifraude & Analítica Fintech.
Exportable y reutilizable en cualquier proyecto Flask, FastAPI (vía WSGI) o microservicio.
"""

from .blueprint import create_admin_blueprint
from .data_provider import BaseAdminDataProvider, MockAdminDataProvider, SQLiteAdminDataProvider
from .config import AdminConfig

__all__ = [
    "create_admin_blueprint",
    "BaseAdminDataProvider",
    "MockAdminDataProvider",
    "SQLiteAdminDataProvider",
    "AdminConfig"
]

__version__ = "1.0.0"
