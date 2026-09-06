"""
Configuración del Módulo Independiente de Administración
Permite personalizar marcas, temas, paginación y parámetros globales.
"""

import os

class AdminConfig:
    """Configuración predeterminada para el módulo de administración."""
    BRAND_NAME = os.environ.get("ADMIN_BRAND_NAME", "Yape Antifraude")
    BRAND_SUBTITLE = os.environ.get("ADMIN_BRAND_SUBTITLE", "Panel de Administración & IA")
    BRAND_LOGO_TEXT = os.environ.get("ADMIN_BRAND_LOGO_TEXT", "Y")
    THEME_PRIMARY = os.environ.get("ADMIN_THEME_PRIMARY", "#732282")
    THEME_ACCENT = os.environ.get("ADMIN_THEME_ACCENT", "#00D2B5")
    ITEMS_PER_PAGE = int(os.environ.get("ADMIN_ITEMS_PER_PAGE", 100))
    URL_PREFIX = os.environ.get("ADMIN_URL_PREFIX", "/admin")
    REQUIRE_AUTH = os.environ.get("ADMIN_REQUIRE_AUTH", "false").lower() in ("true", "1", "yes")
    SESSION_ROLE_KEY = os.environ.get("ADMIN_SESSION_ROLE_KEY", "tipo_usuario")
    ADMIN_ROLE_VALUE = os.environ.get("ADMIN_ROLE_VALUE", "ADMIN")
