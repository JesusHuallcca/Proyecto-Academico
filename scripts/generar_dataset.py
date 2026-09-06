# ============================================================
# PROYECTO BCP - YAPE
# GENERADOR DE DATASET PARA DETECCIÓN DE FRAUDE
# ============================================================

import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# 1. CONFIGURACIÓN DE RUTAS
# ============================================================

# Carpeta principal del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Carpeta donde se guardará el dataset
DATOS_DIR = BASE_DIR / "datos"

# Crear carpeta si no existe
DATOS_DIR.mkdir(exist_ok=True)


# ============================================================
# 2. CONFIGURACIÓN GENERAL
# ============================================================

# Semilla para que los resultados sean reproducibles
np.random.seed(42)

# Cantidad de transacciones
cantidad_registros = 50000


# ============================================================
# 3. ID DE TRANSACCIÓN
# ============================================================

id_transaccion = np.arange(
    1,
    cantidad_registros + 1
)


# ============================================================
# 4. FECHA Y HORA
# ============================================================

fecha_hora = pd.date_range(
    start="2026-01-01",
    periods=cantidad_registros,
    freq="10min"
)

# Extraemos información temporal
hora = fecha_hora.hour

dia_semana = fecha_hora.dayofweek

# 0 = lunes
# 6 = domingo


# ============================================================
# 5. PRODUCTO / TIPO DE OPERACIÓN
# ============================================================

productos = [
    "Yape",
    "Pago de servicios",
    "Recarga",
    "Compra",
    "Transferencia"
]

producto = np.random.choice(
    productos,
    size=cantidad_registros,
    p=[
        0.40,  # Yape
        0.15,  # Pago de servicios
        0.10,  # Recarga
        0.20,  # Compra
        0.15   # Transferencia
    ]
)


# ============================================================
# 6. MONTO DE LA TRANSACCIÓN
# ============================================================

monto = np.round(
    np.random.lognormal(
        mean=5.5,
        sigma=1.0,
        size=cantidad_registros
    ),
    2
)

# Limitar los montos
monto = np.clip(
    monto,
    5,
    5000
)


# ============================================================
# 7. MONTO PROMEDIO DEL USUARIO
# ============================================================

monto_promedio_usuario = np.round(
    np.random.uniform(
        50,
        1000,
        cantidad_registros
    ),
    2
)


# ============================================================
# 8. SALDO DEL USUARIO
# ============================================================

saldo_anterior = np.round(
    np.random.uniform(
        20,
        10000,
        cantidad_registros
    ),
    2
)

# Aseguramos que el saldo pueda cubrir la operación
saldo_anterior = np.maximum(
    saldo_anterior,
    monto
)

saldo_posterior = np.round(
    saldo_anterior - monto,
    2
)


# ============================================================
# 9. VARIABLES DE COMPORTAMIENTO
# ============================================================

# Destinatario nuevo
destinatario_nuevo = np.random.binomial(
    1,
    0.30,
    cantidad_registros
)

# Operación realizada en horario inusual
hora_inusual = np.random.binomial(
    1,
    0.20,
    cantidad_registros
)

# Tiempo entre operaciones en segundos/minutos simulados
velocidad_operacion = np.random.randint(
    5,
    181,
    cantidad_registros
)

# Llamada reciente antes de la operación
llamada_reciente = np.random.binomial(
    1,
    0.18,
    cantidad_registros
)

# Cambio reciente de dispositivo
cambio_dispositivo = np.random.binomial(
    1,
    0.12,
    cantidad_registros
)


# ============================================================
# 10. DATOS DEL USUARIO
# ============================================================

edad = np.random.randint(
    18,
    81,
    cantidad_registros
)

usuario_nuevo = np.random.binomial(
    1,
    0.10,
    cantidad_registros
)

dias_desde_registro = np.random.randint(
    1,
    3000,
    cantidad_registros
)


# ============================================================
# 11. ACTIVIDAD DEL USUARIO
# ============================================================

cantidad_operaciones_dia = np.random.poisson(
    4,
    cantidad_registros
)

operaciones_ultima_hora = np.random.poisson(
    1,
    cantidad_registros
)


# ============================================================
# 12. ALERTAS
# ============================================================

alertas_ignoradas = np.random.poisson(
    0.4,
    cantidad_registros
)

alertas_ignoradas = np.clip(
    alertas_ignoradas,
    0,
    4
)


# ============================================================
# 13. DISTANCIA ENTRE OPERACIONES
# ============================================================

distancia_operaciones = np.round(
    np.random.exponential(
        scale=5,
        size=cantidad_registros
    ),
    2
)


# ============================================================
# 14. UBICACIÓN
# ============================================================

ubicacion_inusual = np.random.binomial(
    1,
    0.08,
    cantidad_registros
)


# ============================================================
# 15. CREAR DATAFRAME
# ============================================================

df = pd.DataFrame({

    "id_transaccion":
        id_transaccion,

    "fecha_hora":
        fecha_hora,

    "hora":
        hora,

    "dia_semana":
        dia_semana,

    "producto":
        producto,

    "monto":
        monto,

    "monto_promedio_usuario":
        monto_promedio_usuario,

    "saldo_anterior":
        saldo_anterior,

    "saldo_posterior":
        saldo_posterior,

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

    "cantidad_operaciones_dia":
        cantidad_operaciones_dia,

    "operaciones_ultima_hora":
        operaciones_ultima_hora,

    "alertas_ignoradas":
        alertas_ignoradas,

    "distancia_operaciones":
        distancia_operaciones,

    "ubicacion_inusual":
        ubicacion_inusual
})


# ============================================================
# 16. CALCULAR PUNTAJE DE RIESGO
# ============================================================

riesgo = (

    # --------------------------------------------------------
    # Monto elevado
    # --------------------------------------------------------

    (df["monto"] > 1500).astype(int) * 2

    # --------------------------------------------------------
    # Monto muy superior al promedio del usuario
    # --------------------------------------------------------

    + (
        df["monto"] >
        df["monto_promedio_usuario"] * 3
    ).astype(int) * 2

    # --------------------------------------------------------
    # Destinatario nuevo
    # --------------------------------------------------------

    + df["destinatario_nuevo"]

    # --------------------------------------------------------
    # Horario inusual
    # --------------------------------------------------------

    + df["hora_inusual"]

    # --------------------------------------------------------
    # Llamada reciente
    # --------------------------------------------------------

    + df["llamada_reciente"]

    # --------------------------------------------------------
    # Cambio de dispositivo
    # --------------------------------------------------------

    + df["cambio_dispositivo"] * 2

    # --------------------------------------------------------
    # Velocidad sospechosa
    # --------------------------------------------------------

    + (
        df["velocidad_operacion"] < 20
    ).astype(int)

    + (
        df["velocidad_operacion"] > 150
    ).astype(int)

    # --------------------------------------------------------
    # Muchas operaciones durante el día
    # --------------------------------------------------------

    + (
        df["cantidad_operaciones_dia"] > 10
    ).astype(int)

    # --------------------------------------------------------
    # Muchas operaciones en la última hora
    # --------------------------------------------------------

    + (
        df["operaciones_ultima_hora"] > 4
    ).astype(int) * 2

    # --------------------------------------------------------
    # Alertas ignoradas
    # --------------------------------------------------------

    + (
        df["alertas_ignoradas"] >= 2
    ).astype(int)

    # --------------------------------------------------------
    # Distancia elevada entre operaciones
    # --------------------------------------------------------

    + (
        df["distancia_operaciones"] > 10
    ).astype(int)

    # --------------------------------------------------------
    # Ubicación inusual
    # --------------------------------------------------------

    + df["ubicacion_inusual"] * 2

    # --------------------------------------------------------
    # Usuario nuevo
    # --------------------------------------------------------

    + df["usuario_nuevo"]
)


# ============================================================
# 17. GUARDAR PUNTAJE DE RIESGO
# ============================================================

df["puntaje_riesgo"] = riesgo


# ============================================================
# 18. NIVEL DE RIESGO
# ============================================================

df["nivel_riesgo"] = pd.cut(
    df["puntaje_riesgo"],
    bins=[
        -1,
        2,
        4,
        6,
        20
    ],
    labels=[
        "Bajo",
        "Medio",
        "Alto",
        "Critico"
    ]
)


# ============================================================
# 19. CREAR VARIABLE OBJETIVO: FRAUDE
# ============================================================

# 0 = operación normal
# 1 = operación fraudulenta

df["fraude"] = (
    df["puntaje_riesgo"] >= 5
).astype(int)


# ============================================================
# 20. INFORMACIÓN DEL DATASET
# ============================================================

print("\n" + "=" * 60)
print("DATASET DE DETECCIÓN DE FRAUDE - BCP / YAPE")
print("=" * 60)

print("\nPrimeros registros:")
print(df.head(10))

print("\nCantidad total de registros:")
print(len(df))

print("\nCantidad de columnas:")
print(len(df.columns))

print("\nColumnas:")
for columna in df.columns:
    print(" -", columna)


# ============================================================
# 21. CONTEO DE TRANSACCIONES
# ============================================================

print("\n" + "=" * 60)
print("CONTEO DE TRANSACCIONES")
print("=" * 60)

conteo_fraude = df["fraude"].value_counts()

print(conteo_fraude)

operaciones_normales = (
    df["fraude"] == 0
).sum()

operaciones_fraudulentas = (
    df["fraude"] == 1
).sum()

print("\nOperaciones normales:")
print(operaciones_normales)

print("\nOperaciones fraudulentas:")
print(operaciones_fraudulentas)


# ============================================================
# 22. PORCENTAJES
# ============================================================

porcentaje_fraude = (
    df["fraude"].mean() * 100
)

porcentaje_normal = (
    (df["fraude"] == 0).mean() * 100
)

print("\n" + "=" * 60)
print("PORCENTAJES")
print("=" * 60)

print(
    f"\nOperaciones normales: "
    f"{porcentaje_normal:.2f}%"
)

print(
    f"Operaciones fraudulentas: "
    f"{porcentaje_fraude:.2f}%"
)


# ============================================================
# 23. NIVELES DE RIESGO
# ============================================================

print("\n" + "=" * 60)
print("NIVELES DE RIESGO")
print("=" * 60)

print(
    df["nivel_riesgo"].value_counts()
)


# ============================================================
# 24. RESUMEN DE PRODUCTOS
# ============================================================

print("\n" + "=" * 60)
print("OPERACIONES POR PRODUCTO")
print("=" * 60)

print(
    df["producto"].value_counts()
)


# ============================================================
# 25. PROMEDIO DE MONTO POR PRODUCTO
# ============================================================

print("\n" + "=" * 60)
print("PROMEDIO DE MONTO POR PRODUCTO")
print("=" * 60)

promedio_producto = (
    df.groupby("producto")["monto"]
    .mean()
    .sort_values(ascending=False)
)

print(
    promedio_producto.round(2)
)


# ============================================================
# 26. MEDIANA DE MONTO POR PRODUCTO
# ============================================================

print("\n" + "=" * 60)
print("MEDIANA DE MONTO POR PRODUCTO")
print("=" * 60)

mediana_producto = (
    df.groupby("producto")["monto"]
    .median()
    .sort_values(ascending=False)
)

print(
    mediana_producto.round(2)
)


# ============================================================
# 27. FRAUDES POR PRODUCTO
# ============================================================

print("\n" + "=" * 60)
print("FRAUDES POR PRODUCTO")
print("=" * 60)

fraudes_producto = (
    df.groupby("producto")["fraude"]
    .sum()
    .sort_values(ascending=False)
)

print(
    fraudes_producto
)


# ============================================================
# 28. PROMEDIO GENERAL
# ============================================================

print("\n" + "=" * 60)
print("ESTADÍSTICAS GENERALES DEL MONTO")
print("=" * 60)

print(
    f"\nPromedio: S/ {df['monto'].mean():.2f}"
)

print(
    f"Mediana: S/ {df['monto'].median():.2f}"
)

print(
    f"Mínimo: S/ {df['monto'].min():.2f}"
)

print(
    f"Máximo: S/ {df['monto'].max():.2f}"
)

print(
    f"Desviación estándar: "
    f"S/ {df['monto'].std():.2f}"
)


# ============================================================
# 29. GUARDAR DATASET
# ============================================================

ruta_dataset = (
    DATOS_DIR /
    "dataset_fraude_yape.csv"
)

df.to_csv(
    ruta_dataset,
    index=False
)


# ============================================================
# 30. CONFIRMACIÓN
# ============================================================

print("\n" + "=" * 60)
print("DATASET GUARDADO CORRECTAMENTE")
print("=" * 60)

print("\nUbicación:")
print(ruta_dataset)

print("\nCantidad de registros:")
print(len(df))

print("\nCantidad de columnas:")
print(len(df.columns))


# ============================================================
# 31. MUESTRA DE OPERACIONES NORMALES
# ============================================================

print("\n" + "=" * 60)
print("EJEMPLO DE OPERACIONES NORMALES")
print("=" * 60)

print(
    df[df["fraude"] == 0].head(5)
)


# ============================================================
# 32. MUESTRA DE OPERACIONES FRAUDULENTAS
# ============================================================

print("\n" + "=" * 60)
print("EJEMPLO DE OPERACIONES FRAUDULENTAS")
print("=" * 60)

print(
    df[df["fraude"] == 1].head(5)
)


# ============================================================
# 33. FINAL
# ============================================================

print("\n" + "=" * 60)
print("PROCESO FINALIZADO")
print("=" * 60)

print(
    "\nDataset de fraude Yape generado correctamente."
)

print(
    "Ahora puede ser utilizado para el análisis "
    "estadístico y Machine Learning."
)