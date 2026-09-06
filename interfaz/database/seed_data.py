"""
Script para inicializar datos realistas en la base de datos de Fraude Yape.
Carga transacciones históricas, predicciones de Machine Learning y alertas.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import random

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "fraude_yape.db"
CSV_PATH = BASE_DIR.parent.parent / "datos" / "dataset_fraude_yape.csv"


def conectar():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def seed_demo_data(limit_normal=35, limit_fraud=15, clear_first=True):
    conexion = conectar()
    cursor = conexion.cursor()

    if clear_first:
        cursor.execute("DELETE FROM alertas")
        cursor.execute("DELETE FROM predicciones")
        cursor.execute("DELETE FROM historial_acciones")
        cursor.execute("DELETE FROM transacciones")
        conexion.commit()

    # Verificar usuario Juan Perez
    cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = 'juan@correo.com'")
    user_row = cursor.fetchone()
    if not user_row:
        cursor.execute("""
            INSERT INTO usuarios (nombre, apellido, correo, password, tipo_usuario, estado)
            VALUES ('Juan', 'Perez', 'juan@correo.com', '123456', 'USUARIO', 'ACTIVO')
        """)
        id_usuario = cursor.lastrowid
    else:
        id_usuario = user_row["id_usuario"]

    # Verificar cuenta
    cursor.execute("SELECT id_cuenta FROM cuentas WHERE id_usuario = ?", (id_usuario,))
    cuenta_row = cursor.fetchone()
    if not cuenta_row:
        cursor.execute("""
            INSERT INTO cuentas (id_usuario, numero_cuenta, tipo_cuenta, saldo, estado)
            VALUES (?, '001-9876543210', 'AHORROS', 5000.00, 'ACTIVA')
        """, (id_usuario,))
        id_cuenta = cursor.lastrowid
    else:
        id_cuenta = cuenta_row["id_cuenta"]
        # Resetear saldo para demo a 5000.00
        cursor.execute("UPDATE cuentas SET saldo = 5000.00, estado = 'ACTIVA' WHERE id_cuenta = ?", (id_cuenta,))

    # Verificar dispositivo
    cursor.execute("SELECT id_dispositivo FROM dispositivos WHERE id_usuario = ?", (id_usuario,))
    disp_row = cursor.fetchone()
    if not disp_row:
        cursor.execute("""
            INSERT INTO dispositivos (id_usuario, tipo_dispositivo, sistema_operativo, modelo, activo)
            VALUES (?, 'CELULAR', 'Android 14', 'Samsung Galaxy S24 Ultra', 1)
        """, (id_usuario,))
        id_dispositivo = cursor.lastrowid
    else:
        id_dispositivo = disp_row["id_dispositivo"]

    conexion.commit()

    # Cargar datos desde dataset_fraude_yape.csv si existe
    if CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH)
        df_normal = df[df["fraude"] == 0].sample(n=min(limit_normal, len(df[df["fraude"] == 0])), random_state=42)
        df_fraud = df[df["fraude"] == 1].sample(n=min(limit_fraud, len(df[df["fraude"] == 1])), random_state=42)
        sample_df = pd.concat([df_normal, df_fraud]).sample(frac=1, random_state=42).reset_index(drop=True)

        now = datetime.now()
        for idx, row in sample_df.iterrows():
            # Generar fechas distribuidas en las últimas 72 horas
            minutes_ago = int((len(sample_df) - idx) * 90 + random.randint(-15, 15))
            tx_time = (now - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d %H:%M:%S")

            es_fraude = int(row["fraude"])
            resultado_tx = "SOSPECHOSA" if es_fraude == 1 else "APROBADA"

            cursor.execute("""
                INSERT INTO transacciones (
                    id_usuario, id_cuenta, id_dispositivo, fecha_hora, monto, monto_promedio_usuario,
                    saldo_anterior, saldo_posterior, producto, destinatario_nuevo, hora_inusual,
                    velocidad_operacion, llamada_reciente, cambio_dispositivo, edad, usuario_nuevo,
                    dias_desde_registro, operaciones_dia, operaciones_ultima_hora, alertas_ignoradas,
                    distancia_ubicacion, ubicacion_inusual, hora, dia_semana, resultado, fecha_analisis
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                id_usuario,
                id_cuenta,
                id_dispositivo,
                tx_time,
                float(row["monto"]),
                float(row["monto_promedio_usuario"]),
                float(row["saldo_anterior"]),
                float(row["saldo_posterior"]),
                str(row["producto"]),
                int(row["destinatario_nuevo"]),
                int(row["hora_inusual"]),
                float(row["velocidad_operacion"]),
                int(row["llamada_reciente"]),
                int(row["cambio_dispositivo"]),
                int(row["edad"]),
                int(row["usuario_nuevo"]),
                int(row["dias_desde_registro"]),
                int(row["cantidad_operaciones_dia"]),
                int(row["operaciones_ultima_hora"]),
                int(row["alertas_ignoradas"]),
                float(row["distancia_operaciones"]),
                int(row["ubicacion_inusual"]),
                int(row["hora"]),
                int(row["dia_semana"]),
                resultado_tx,
                tx_time
            ))
            id_transaccion = cursor.lastrowid

            # Predicción ML
            if es_fraude == 1:
                prob_fraude = round(random.uniform(78.5, 99.4), 2)
                prob_normal = round(100.0 - prob_fraude, 2)
                res_pred = "FRAUDE"
            else:
                prob_normal = round(random.uniform(91.0, 99.8), 2)
                prob_fraude = round(100.0 - prob_normal, 2)
                res_pred = "NORMAL"

            cursor.execute("""
                INSERT INTO predicciones (
                    id_transaccion, modelo, probabilidad_normal, probabilidad_fraude, resultado, fecha_prediccion
                ) VALUES (?, 'Gradient Boosting', ?, ?, ?, ?)
            """, (id_transaccion, prob_normal, prob_fraude, res_pred, tx_time))

            # Si es fraude o riesgo medio/alto, generar alerta
            if es_fraude == 1:
                nivel = "CRITICO" if prob_fraude > 90 else "ALTO"
                tipo = "TRANSACCION_ANOMALA"
                desc = (
                    f"Riesgo {nivel}: Monto de S/ {float(row['monto']):.2f} "
                    f"supera el promedio (S/ {float(row['monto_promedio_usuario']):.2f}). "
                    f"Destinatario nuevo: {'Sí' if int(row['destinatario_nuevo']) == 1 else 'No'}. "
                    f"Hora inusual: {'Sí' if int(row['hora_inusual']) == 1 else 'No'}."
                )
                estados = ["PENDIENTE", "PENDIENTE", "REVISADA", "CONFIRMADA"]
                estado_alerta = random.choice(estados)

                cursor.execute("""
                    INSERT INTO alertas (
                        id_transaccion, nivel, tipo_alerta, descripcion, estado, fecha_alerta
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (id_transaccion, nivel, tipo, desc, estado_alerta, tx_time))

        conexion.commit()
        print(f"✓ Datos iniciales sembrados con éxito: {len(sample_df)} transacciones generadas.")

    conexion.close()


if __name__ == "__main__":
    seed_demo_data()
