import sqlite3
from pathlib import Path

# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "fraude_yape.db"


# ============================================================
# CONEXIÓN
# ============================================================

def conectar():
    """Conecta con la base de datos SQLite."""
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row

    # Activar claves foráneas
    conexion.execute("PRAGMA foreign_keys = ON")

    return conexion


# ============================================================
# CREAR TABLAS
# ============================================================

def crear_tablas():

    conexion = conectar()
    cursor = conexion.cursor()

    # --------------------------------------------------------
    # 1. USUARIOS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            correo TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            tipo_usuario TEXT NOT NULL DEFAULT 'USUARIO'
                CHECK(tipo_usuario IN ('ADMIN', 'USUARIO')),
            estado TEXT NOT NULL DEFAULT 'ACTIVO'
                CHECK(estado IN ('ACTIVO', 'INACTIVO')),
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------------------------
    # 2. CUENTAS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuentas (
            id_cuenta INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL,
            numero_cuenta TEXT NOT NULL UNIQUE,
            tipo_cuenta TEXT NOT NULL DEFAULT 'AHORROS',
            saldo REAL NOT NULL DEFAULT 0,
            estado TEXT NOT NULL DEFAULT 'ACTIVA'
                CHECK(estado IN ('ACTIVA', 'BLOQUEADA', 'CERRADA')),
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (id_usuario)
                REFERENCES usuarios(id_usuario)
                ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------------
    # 3. DISPOSITIVOS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dispositivos (
            id_dispositivo INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL,
            tipo_dispositivo TEXT NOT NULL,
            sistema_operativo TEXT,
            modelo TEXT,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            activo INTEGER NOT NULL DEFAULT 1
                CHECK(activo IN (0, 1)),

            FOREIGN KEY (id_usuario)
                REFERENCES usuarios(id_usuario)
                ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------------
    # 4. TRANSACCIONES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacciones (
            id_transaccion INTEGER PRIMARY KEY AUTOINCREMENT,

            id_usuario INTEGER NOT NULL,
            id_cuenta INTEGER,
            id_dispositivo INTEGER,

            fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,

            monto REAL NOT NULL,
            monto_promedio_usuario REAL,

            saldo_anterior REAL,
            saldo_posterior REAL,

            producto TEXT NOT NULL,

            destinatario_nuevo INTEGER DEFAULT 0,
            hora_inusual INTEGER DEFAULT 0,
            velocidad_operacion REAL,
            llamada_reciente INTEGER DEFAULT 0,
            cambio_dispositivo INTEGER DEFAULT 0,

            edad INTEGER,
            usuario_nuevo INTEGER DEFAULT 0,
            dias_desde_registro INTEGER,

            operaciones_dia INTEGER DEFAULT 0,
            operaciones_ultima_hora INTEGER DEFAULT 0,
            alertas_ignoradas INTEGER DEFAULT 0,

            distancia_ubicacion REAL,
            ubicacion_inusual INTEGER DEFAULT 0,

            hora INTEGER,
            dia_semana INTEGER,

            resultado TEXT,

            fecha_analisis DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (id_usuario)
                REFERENCES usuarios(id_usuario)
                ON DELETE CASCADE,

            FOREIGN KEY (id_cuenta)
                REFERENCES cuentas(id_cuenta)
                ON DELETE SET NULL,

            FOREIGN KEY (id_dispositivo)
                REFERENCES dispositivos(id_dispositivo)
                ON DELETE SET NULL
        )
    """)

    # --------------------------------------------------------
    # 5. PREDICCIONES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predicciones (
            id_prediccion INTEGER PRIMARY KEY AUTOINCREMENT,

            id_transaccion INTEGER NOT NULL,

            modelo TEXT NOT NULL,

            probabilidad_normal REAL NOT NULL,
            probabilidad_fraude REAL NOT NULL,

            resultado TEXT NOT NULL,

            fecha_prediccion DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (id_transaccion)
                REFERENCES transacciones(id_transaccion)
                ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------------
    # 6. ALERTAS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alertas (
            id_alerta INTEGER PRIMARY KEY AUTOINCREMENT,

            id_transaccion INTEGER NOT NULL,

            nivel TEXT NOT NULL
                CHECK(nivel IN ('BAJO', 'MEDIO', 'ALTO', 'CRITICO')),

            tipo_alerta TEXT NOT NULL,

            descripcion TEXT,

            estado TEXT NOT NULL DEFAULT 'PENDIENTE'
                CHECK(estado IN (
                    'PENDIENTE',
                    'REVISADA',
                    'CONFIRMADA',
                    'DESCARTADA'
                )),

            fecha_alerta DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (id_transaccion)
                REFERENCES transacciones(id_transaccion)
                ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------------
    # 7. HISTORIAL DE ACCIONES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_acciones (
            id_historial INTEGER PRIMARY KEY AUTOINCREMENT,

            id_usuario INTEGER NOT NULL,

            id_transaccion INTEGER,

            accion TEXT NOT NULL,

            descripcion TEXT,

            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (id_usuario)
                REFERENCES usuarios(id_usuario)
                ON DELETE CASCADE,

            FOREIGN KEY (id_transaccion)
                REFERENCES transacciones(id_transaccion)
                ON DELETE SET NULL
        )
    """)

    # --------------------------------------------------------
    # 8. MODELOS MACHINE LEARNING
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modelos_ml (
            id_modelo INTEGER PRIMARY KEY AUTOINCREMENT,

            nombre_modelo TEXT NOT NULL,

            tipo TEXT NOT NULL,

            accuracy REAL,
            precision REAL,
            recall REAL,
            f1_score REAL,

            estado TEXT NOT NULL DEFAULT 'EVALUADO'
                CHECK(estado IN (
                    'EVALUADO',
                    'SELECCIONADO',
                    'INACTIVO'
                )),

            fecha_entrenamiento DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------------------------
    # 9. CÓDIGOS DE VERIFICACIÓN (OTP REGISTRO GMAIL)
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS codigos_verificacion (
            id_codigo INTEGER PRIMARY KEY AUTOINCREMENT,
            correo TEXT NOT NULL,
            codigo TEXT NOT NULL,
            datos_json TEXT NOT NULL,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            expirado INTEGER DEFAULT 0
        )
    """)

    # ========================================================
    # ÍNDICES
    # ========================================================

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_transacciones_usuario
        ON transacciones(id_usuario)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_transacciones_fecha
        ON transacciones(fecha_hora)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_transacciones_resultado
        ON transacciones(resultado)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_alertas_estado
        ON alertas(estado)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_predicciones_transaccion
        ON predicciones(id_transaccion)
    """)

    # Guardar cambios
    conexion.commit()

    conexion.close()

    print("==========================================")
    print(" BASE DE DATOS CREADA CORRECTAMENTE")
    print("==========================================")
    print(f"Ubicación: {DB_PATH}")
    print()
    print("Tablas creadas:")
    print("1. usuarios")
    print("2. cuentas")
    print("3. dispositivos")
    print("4. transacciones")
    print("5. predicciones")
    print("6. alertas")
    print("7. historial_acciones")
    print("8. modelos_ml")
    print("==========================================")


# ============================================================
# INSERTAR USUARIO DE PRUEBA
# ============================================================

def crear_datos_iniciales():

    conexion = conectar()
    cursor = conexion.cursor()

    # --------------------------------------------------------
    # ADMINISTRADOR
    # --------------------------------------------------------

    cursor.execute("""
        INSERT OR IGNORE INTO usuarios
        (nombre, apellido, correo, password, tipo_usuario)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "Administrador",
        "Sistema",
        "admin@bcp.com",
        "admin123",
        "ADMIN"
    ))

    # --------------------------------------------------------
    # USUARIO DE PRUEBA
    # --------------------------------------------------------

    cursor.execute("""
        INSERT OR IGNORE INTO usuarios
        (nombre, apellido, correo, password, tipo_usuario)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "Juan",
        "Perez",
        "juan@correo.com",
        "123456",
        "USUARIO"
    ))

    conexion.commit()

    # --------------------------------------------------------
    # OBTENER ID DEL USUARIO
    # --------------------------------------------------------

    cursor.execute("""
        SELECT id_usuario
        FROM usuarios
        WHERE correo = ?
    """, ("juan@correo.com",))

    usuario = cursor.fetchone()

    if usuario:

        id_usuario = usuario["id_usuario"]

        # ----------------------------------------------------
        # CUENTA DE PRUEBA
        # ----------------------------------------------------

        cursor.execute("""
            INSERT OR IGNORE INTO cuentas
            (
                id_usuario,
                numero_cuenta,
                tipo_cuenta,
                saldo
            )
            VALUES (?, ?, ?, ?)
        """, (
            id_usuario,
            "001-1234567890",
            "AHORROS",
            5000.00
        ))

        # ----------------------------------------------------
        # DISPOSITIVO DE PRUEBA
        # ----------------------------------------------------

        cursor.execute("""
            INSERT INTO dispositivos
            (
                id_usuario,
                tipo_dispositivo,
                sistema_operativo,
                modelo
            )
            SELECT ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1
                FROM dispositivos
                WHERE id_usuario = ?
            )
        """, (
            id_usuario,
            "CELULAR",
            "Android",
            "Samsung Galaxy",
            id_usuario
        ))

    # --------------------------------------------------------
    # MODELOS MACHINE LEARNING
    # --------------------------------------------------------

    modelos = [
        (
            "Gradient Boosting",
            "Machine Learning",
            0.9865,
            0.9829,
            0.8043,
            0.8847,
            "SELECCIONADO"
        ),
        (
            "PyTorch",
            "Red Neuronal",
            0.9612,
            0.6301,
            0.9627,
            0.7617,
            "EVALUADO"
        ),
        (
            "TensorFlow / Keras",
            "Red Neuronal",
            0.9527,
            0.5807,
            0.9550,
            0.7223,
            "EVALUADO"
        ),
        (
            "Random Forest",
            "Machine Learning",
            0.9546,
            0.5971,
            0.9068,
            0.7201,
            "EVALUADO"
        ),
        (
            "Árbol de Decisión",
            "Machine Learning",
            0.9222,
            0.4473,
            0.8835,
            0.5939,
            "EVALUADO"
        ),
        (
            "Regresión Logística",
            "Machine Learning",
            0.9155,
            0.4274,
            0.9193,
            0.5835,
            "EVALUADO"
        )
    ]

    cursor.executemany("""
        INSERT INTO modelos_ml
        (
            nombre_modelo,
            tipo,
            accuracy,
            precision,
            recall,
            f1_score,
            estado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, modelos)

    conexion.commit()
    conexion.close()

    print("Datos iniciales insertados correctamente.")


# ============================================================
# MOSTRAR TABLAS
# ============================================================

def mostrar_tablas():

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """)

    tablas = cursor.fetchall()

    print("\nTABLAS DE LA BASE DE DATOS:")
    print("--------------------------------")

    for tabla in tablas:
        print("✓", tabla["name"])

    conexion.close()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    crear_tablas()
    crear_datos_iniciales()
    mostrar_tablas()