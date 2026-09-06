import numpy as np
import pandas as pd
import joblib
from pathlib import Path


# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
MODELOS_DIR = BASE_DIR / "modelos"

RUTA_MODELO = MODELOS_DIR / "modelo_fraude.pkl"
RUTA_SCALER = MODELOS_DIR / "scaler_fraude.pkl"
RUTA_COLUMNAS = MODELOS_DIR / "columnas_modelo.pkl"


# ==========================================
# 2. CARGAR MODELO
# ==========================================

print("\n==============================================")
print("     SISTEMA DE DETECCIÓN DE FRAUDE")
print("             BCP - YAPE")
print("==============================================")

try:

    modelo = joblib.load(RUTA_MODELO)
    scaler = joblib.load(RUTA_SCALER)
    columnas_modelo = joblib.load(RUTA_COLUMNAS)

    print("\n✓ Modelo cargado correctamente.")
    print("✓ Scaler cargado correctamente.")
    print("✓ Columnas del modelo cargadas correctamente.")

except FileNotFoundError as e:

    print("\n❌ ERROR: No se encontró uno de los archivos necesarios.")
    print(e)

    print("\nVerifica que existan:")
    print(RUTA_MODELO)
    print(RUTA_SCALER)
    print(RUTA_COLUMNAS)

    exit()


# ==========================================
# 3. INGRESAR DATOS
# ==========================================

print("\n==============================================")
print("       DATOS DE LA TRANSACCIÓN")
print("==============================================")


try:

    monto = float(
        input("\nMonto de la transacción (S/): ")
    )

    monto_promedio_usuario = float(
        input("Monto promedio del usuario (S/): ")
    )

    saldo_anterior = float(
        input("Saldo anterior (S/): ")
    )

    saldo_posterior = saldo_anterior - monto

    destinatario_nuevo = int(
        input("¿Destinatario nuevo? (1=Sí / 0=No): ")
    )

    hora_inusual = int(
        input("¿Hora inusual? (1=Sí / 0=No): ")
    )

    velocidad_operacion = int(
        input("Velocidad de operación (5-180): ")
    )

    llamada_reciente = int(
        input("¿Llamada reciente? (1=Sí / 0=No): ")
    )

    cambio_dispositivo = int(
        input("¿Cambio de dispositivo? (1=Sí / 0=No): ")
    )

    edad = int(
        input("Edad del usuario: ")
    )

    usuario_nuevo = int(
        input("¿Usuario nuevo? (1=Sí / 0=No): ")
    )

    dias_desde_registro = int(
        input("Días desde el registro: ")
    )

    operaciones_dia = int(
        input("Cantidad de operaciones hoy: ")
    )

    operaciones_ultima_hora = int(
        input("Operaciones en la última hora: ")
    )

    alertas_ignoradas = int(
        input("Alertas ignoradas: ")
    )

    distancia_ubicacion = float(
        input("Distancia entre operaciones (km): ")
    )

    ubicacion_inusual = int(
        input("¿Ubicación inusual? (1=Sí / 0=No): ")
    )

    hora = int(
        input("Hora de la transacción (0-23): ")
    )

    dia_semana = int(
        input(
            "Día de la semana "
            "(0=Lun ... 6=Dom): "
        )
    )

    producto = input(
        "Producto "
        "(Yape/Pago de servicios/Recarga/Compra/Transferencia): "
    )


except ValueError:

    print("\n❌ ERROR: Ingresa valores numéricos válidos.")

    exit()


# ==========================================
# 4. VALIDACIONES
# ==========================================

variables_binarias = {
    "Destinatario nuevo": destinatario_nuevo,
    "Hora inusual": hora_inusual,
    "Llamada reciente": llamada_reciente,
    "Cambio de dispositivo": cambio_dispositivo,
    "Usuario nuevo": usuario_nuevo,
    "Ubicación inusual": ubicacion_inusual
}


for nombre, valor in variables_binarias.items():

    if valor not in [0, 1]:

        print(
            f"\n❌ ERROR: {nombre} debe ser 0 o 1."
        )

        exit()


if not 0 <= hora <= 23:

    print("\n❌ ERROR: La hora debe estar entre 0 y 23.")

    exit()


if not 0 <= dia_semana <= 6:

    print(
        "\n❌ ERROR: El día de la semana debe estar "
        "entre 0 y 6."
    )

    exit()


productos_validos = [
    "Yape",
    "Pago de servicios",
    "Recarga",
    "Compra",
    "Transferencia"
]


if producto not in productos_validos:

    print("\n❌ ERROR: Producto no válido.")

    print("\nProductos disponibles:")

    for p in productos_validos:
        print("-", p)

    exit()


# ==========================================
# 5. CREAR DATAFRAME
# ==========================================

datos = pd.DataFrame([{

    "monto": monto,

    "destinatario_nuevo":
        destinatario_nuevo,

    "hora_inusual":
        hora_inusual,

    "velocidad_operacion":
        velocidad_operacion,

    "llamada_reciente":
        llamada_reciente,

    "cambio_dispositivo":
        cambio_dispositivo,

    "edad":
        edad,

    "usuario_nuevo":
        usuario_nuevo,

    "dias_desde_registro":
        dias_desde_registro,

    "operaciones_dia":
        operaciones_dia,

    "operaciones_ultima_hora":
        operaciones_ultima_hora,

    "alertas_ignoradas":
        alertas_ignoradas,

    "distancia_ubicacion":
        distancia_ubicacion,

    "ubicacion_inusual":
        ubicacion_inusual,

    "saldo_anterior":
        saldo_anterior,

    "saldo_despues":
        saldo_posterior,

    "monto_promedio_usuario":
        monto_promedio_usuario,

    "hora":
        hora,

    "dia_semana":
        dia_semana,

    "producto":
        producto
}])


# ==========================================
# 6. CODIFICAR PRODUCTO
# ==========================================

datos = pd.get_dummies(
    datos,
    columns=["producto"],
    dtype=float
)


# ==========================================
# 7. ASEGURAR LAS MISMAS COLUMNAS
# ==========================================

datos = datos.reindex(
    columns=columnas_modelo,
    fill_value=0
)


# ==========================================
# 8. CONVERTIR A NUMÉRICO
# ==========================================

datos = datos.astype(float)


# ==========================================
# 9. NORMALIZAR
# ==========================================

datos_escalados = scaler.transform(datos)


# ==========================================
# 10. PREDICCIÓN
# ==========================================

prediccion = modelo.predict(
    datos_escalados
)[0]


# ==========================================
# 11. PROBABILIDADES
# ==========================================

probabilidades = modelo.predict_proba(
    datos_escalados
)[0]

probabilidad_normal = probabilidades[0] * 100
probabilidad_fraude = probabilidades[1] * 100


# ==========================================
# 12. RESULTADO
# ==========================================

print("\n==============================================")
print("             RESULTADO DEL ANÁLISIS")
print("==============================================")


if prediccion == 1:

    print("\n⚠️  TRANSACCIÓN SOSPECHOSA")

    print("\nPredicción: POSIBLE FRAUDE")

    print(
        f"Probabilidad de fraude: "
        f"{probabilidad_fraude:.2f}%"
    )

    print(
        f"Probabilidad de operación normal: "
        f"{probabilidad_normal:.2f}%"
    )

    print("\nRecomendación:")

    print(
        "Revisar la transacción antes de "
        "autorizarla."
    )

else:

    print("\n✅ TRANSACCIÓN NORMAL")

    print("\nPredicción: NORMAL")

    print(
        f"Probabilidad de operación normal: "
        f"{probabilidad_normal:.2f}%"
    )

    print(
        f"Probabilidad de fraude: "
        f"{probabilidad_fraude:.2f}%"
    )

    print("\nRecomendación:")

    print(
        "La transacción puede continuar."
    )


# ==========================================
# 13. FIN
# ==========================================

print("\n==============================================")
print("           ANÁLISIS FINALIZADO")
print("==============================================\n")