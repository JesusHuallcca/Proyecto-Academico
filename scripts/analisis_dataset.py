# ============================================================
# ANALISIS DEL DATASET - PROYECTO BCP / YAPE
# Detección de fraude con Machine Learning
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from pathlib import Path
from scipy import stats


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATOS_DIR = BASE_DIR / "datos"
GRAFICOS_DIR = BASE_DIR / "graficos"
RESULTADOS_DIR = BASE_DIR / "resultados"

GRAFICOS_DIR.mkdir(exist_ok=True)
RESULTADOS_DIR.mkdir(exist_ok=True)

RUTA_DATASET = DATOS_DIR / "dataset_fraude_yape.csv"

sns.set_theme(style="whitegrid")


# ============================================================
# 2. CARGAR DATASET
# ============================================================

print("\n" + "=" * 60)
print("        ANÁLISIS DEL DATASET DE TRANSACCIONES")
print("=" * 60)

if not RUTA_DATASET.exists():
    print("\nERROR: No se encontró el dataset.")
    print("Ruta esperada:")
    print(RUTA_DATASET)
    raise FileNotFoundError(RUTA_DATASET)

df = pd.read_csv(RUTA_DATASET)

print("\nDataset cargado correctamente.")
print(f"Registros : {len(df):,}")
print(f"Columnas  : {len(df.columns)}")


# ============================================================
# 3. INFORMACIÓN GENERAL
# ============================================================

print("\n" + "=" * 60)
print("INFORMACIÓN GENERAL")
print("=" * 60)

print("\nColumnas disponibles:")

for columna in df.columns:
    print(f" - {columna}")


print("\nTipos de datos:")
print(df.dtypes)


print("\nValores nulos por columna:")

nulos = df.isnull().sum()

print(nulos[nulos > 0])

if nulos.sum() == 0:
    print("No existen valores nulos.")


# ============================================================
# 4. ESTADÍSTICAS DESCRIPTIVAS
# ============================================================

print("\n" + "=" * 60)
print("ESTADÍSTICAS DESCRIPTIVAS")
print("=" * 60)

estadisticas = df.describe().T

estadisticas.to_csv(
    RESULTADOS_DIR / "estadisticas_descriptivas.csv"
)

print(
    estadisticas[
        ["count", "mean", "std", "min", "50%", "max"]
    ].round(2)
)


# ============================================================
# 5. ANÁLISIS DEL MONTO
# ============================================================

print("\n" + "=" * 60)
print("ANÁLISIS DE MONTOS")
print("=" * 60)

promedio_monto = df["monto"].mean()
mediana_monto = df["monto"].median()
minimo_monto = df["monto"].min()
maximo_monto = df["monto"].max()
desviacion_monto = df["monto"].std()

print(f"\nPromedio : S/ {promedio_monto:,.2f}")
print(f"Mediana  : S/ {mediana_monto:,.2f}")
print(f"Mínimo   : S/ {minimo_monto:,.2f}")
print(f"Máximo   : S/ {maximo_monto:,.2f}")
print(f"Desv. Std: S/ {desviacion_monto:,.2f}")


# ============================================================
# 6. DISTRIBUCIÓN DE MONTOS
# ============================================================

plt.figure(figsize=(10, 6))

plt.hist(
    df["monto"],
    bins=50
)

plt.axvline(
    promedio_monto,
    linestyle="--",
    label=f"Promedio: S/ {promedio_monto:.2f}"
)

plt.axvline(
    mediana_monto,
    linestyle=":",
    label=f"Mediana: S/ {mediana_monto:.2f}"
)

plt.title(
    "Distribución de montos de las transacciones"
)

plt.xlabel("Monto (S/)")
plt.ylabel("Cantidad de transacciones")

plt.legend()
plt.tight_layout()

plt.savefig(
    GRAFICOS_DIR / "01_distribucion_montos.png",
    dpi=150
)

plt.close()


# ============================================================
# 7. OPERACIONES NORMALES VS FRAUDE
# ============================================================

print("\n" + "=" * 60)
print("OPERACIONES NORMALES VS FRAUDE")
print("=" * 60)

conteo_fraude = df["fraude"].value_counts()

normales = conteo_fraude.get(0, 0)
fraudes = conteo_fraude.get(1, 0)

total = len(df)

porcentaje_normal = normales / total * 100
porcentaje_fraude = fraudes / total * 100

print(f"\nOperaciones normales : {normales:,} ({porcentaje_normal:.2f}%)")
print(f"Operaciones fraude   : {fraudes:,} ({porcentaje_fraude:.2f}%)")


resumen_fraude = pd.DataFrame({
    "Tipo": ["Normal", "Fraude"],
    "Cantidad": [normales, fraudes],
    "Porcentaje": [
        porcentaje_normal,
        porcentaje_fraude
    ]
})

resumen_fraude.to_csv(
    RESULTADOS_DIR / "resumen_fraude.csv",
    index=False
)


# ============================================================
# 8. GRÁFICO NORMAL VS FRAUDE
# ============================================================

plt.figure(figsize=(8, 5))

plt.bar(
    ["Normal", "Fraude"],
    [normales, fraudes]
)

plt.title(
    "Operaciones normales vs fraudulentas"
)

plt.xlabel("Tipo de operación")
plt.ylabel("Cantidad de transacciones")

plt.tight_layout()

plt.savefig(
    GRAFICOS_DIR / "02_operaciones_fraude.png",
    dpi=150
)

plt.close()


# ============================================================
# 9. NIVELES DE RIESGO
# ============================================================

print("\n" + "=" * 60)
print("NIVELES DE RIESGO")
print("=" * 60)

orden_riesgo = [
    "Bajo",
    "Medio",
    "Alto",
    "Critico"
]

niveles = (
    df["nivel_riesgo"]
    .value_counts()
    .reindex(
        orden_riesgo,
        fill_value=0
    )
)

print("\n", niveles)


# ============================================================
# 10. GRÁFICO DE NIVELES DE RIESGO
# ============================================================

plt.figure(figsize=(8, 5))

plt.bar(
    niveles.index,
    niveles.values
)

plt.title(
    "Distribución de niveles de riesgo"
)

plt.xlabel("Nivel de riesgo")
plt.ylabel("Cantidad de transacciones")

plt.tight_layout()

plt.savefig(
    GRAFICOS_DIR / "03_niveles_riesgo.png",
    dpi=150
)

plt.close()


# ============================================================
# 11. ANÁLISIS POR PRODUCTO
# ============================================================

print("\n" + "=" * 60)
print("ANÁLISIS POR PRODUCTO")
print("=" * 60)

if "producto" in df.columns:

    resumen_producto = (
        df.groupby("producto")
        .agg(
            operaciones=("id_transaccion", "count"),
            monto_promedio=("monto", "mean"),
            monto_mediana=("monto", "median"),
            fraudes=("fraude", "sum")
        )
        .reset_index()
    )

    resumen_producto["porcentaje_fraude"] = (
        resumen_producto["fraudes"]
        / resumen_producto["operaciones"]
        * 100
    )

    resumen_producto = resumen_producto.sort_values(
        "porcentaje_fraude",
        ascending=False
    )

    print(
        resumen_producto.round(2).to_string(
            index=False
        )
    )

    resumen_producto.to_csv(
        RESULTADOS_DIR / "analisis_por_producto.csv",
        index=False
    )

else:

    print(
        "La columna 'producto' no existe en el dataset."
    )


# ============================================================
# 12. GRÁFICO DE OPERACIONES POR PRODUCTO
# ============================================================

if "producto" in df.columns:

    operaciones_producto = (
        df["producto"]
        .value_counts()
    )

    plt.figure(figsize=(10, 6))

    plt.bar(
        operaciones_producto.index,
        operaciones_producto.values
    )

    plt.title(
        "Cantidad de operaciones por producto"
    )

    plt.xlabel("Producto")
    plt.ylabel("Cantidad de operaciones")

    plt.xticks(rotation=20)

    plt.tight_layout()

    plt.savefig(
        GRAFICOS_DIR / "04_operaciones_por_producto.png",
        dpi=150
    )

    plt.close()


# ============================================================
# 13. FRAUDES POR PRODUCTO
# ============================================================

if "producto" in df.columns:

    fraude_producto = (
        df.groupby("producto")["fraude"]
        .sum()
        .sort_values(
            ascending=False
        )
    )

    plt.figure(figsize=(10, 6))

    plt.bar(
        fraude_producto.index,
        fraude_producto.values
    )

    plt.title(
        "Cantidad de fraudes por producto"
    )

    plt.xlabel("Producto")
    plt.ylabel("Cantidad de fraudes")

    plt.xticks(rotation=20)

    plt.tight_layout()

    plt.savefig(
        GRAFICOS_DIR / "05_fraudes_por_producto.png",
        dpi=150
    )

    plt.close()


# ============================================================
# 14. FRAUDES SEGÚN CAMBIO DE DISPOSITIVO
# ============================================================

fraude_dispositivo = pd.crosstab(
    df["cambio_dispositivo"],
    df["fraude"]
)

plt.figure(figsize=(8, 5))

fraude_dispositivo.plot(
    kind="bar",
    ax=plt.gca()
)

plt.title(
    "Fraude según cambio de dispositivo"
)

plt.xlabel("Cambio de dispositivo")
plt.ylabel("Cantidad")

plt.xticks(
    [0, 1],
    ["No", "Sí"],
    rotation=0
)

plt.legend(
    ["Normal", "Fraude"]
)

plt.tight_layout()

plt.savefig(
    GRAFICOS_DIR / "06_cambio_dispositivo.png",
    dpi=150
)

plt.close()


# ============================================================
# 15. FRAUDES SEGÚN UBICACIÓN INUSUAL
# ============================================================

fraude_ubicacion = pd.crosstab(
    df["ubicacion_inusual"],
    df["fraude"]
)

plt.figure(figsize=(8, 5))

fraude_ubicacion.plot(
    kind="bar",
    ax=plt.gca()
)

plt.title(
    "Fraude según ubicación inusual"
)

plt.xlabel("Ubicación inusual")
plt.ylabel("Cantidad")

plt.xticks(
    [0, 1],
    ["No", "Sí"],
    rotation=0
)

plt.legend(
    ["Normal", "Fraude"]
)

plt.tight_layout()

plt.savefig(
    GRAFICOS_DIR / "07_ubicacion_inusual.png",
    dpi=150
)

plt.close()


# ============================================================
# 16. FRAUDES SEGÚN DESTINATARIO NUEVO
# ============================================================

fraude_destinatario = pd.crosstab(
    df["destinatario_nuevo"],
    df["fraude"]
)

plt.figure(figsize=(8, 5))

fraude_destinatario.plot(
    kind="bar",
    ax=plt.gca()
)

plt.title(
    "Fraude según destinatario nuevo"
)

plt.xlabel("Destinatario nuevo")
plt.ylabel("Cantidad")

plt.xticks(
    [0, 1],
    ["No", "Sí"],
    rotation=0
)

plt.legend(
    ["Normal", "Fraude"]
)

plt.tight_layout()

plt.savefig(
    GRAFICOS_DIR / "08_destinatario_nuevo.png",
    dpi=150
)

plt.close()


# ============================================================
# 17. FRAUDES SEGÚN LLAMADA RECIENTE
# ============================================================

fraude_llamada = pd.crosstab(
    df["llamada_reciente"],
    df["fraude"]
)

plt.figure(figsize=(8, 5))

fraude_llamada.plot(
    kind="bar",
    ax=plt.gca()
)

plt.title(
    "Fraude según llamada reciente"
)

plt.xlabel("Llamada reciente")
plt.ylabel("Cantidad")

plt.xticks(
    [0, 1],
    ["No", "Sí"],
    rotation=0
)

plt.legend(
    ["Normal", "Fraude"]
)

plt.tight_layout()

plt.savefig(
    GRAFICOS_DIR / "09_llamada_reciente.png",
    dpi=150
)

plt.close()


# ============================================================
# 18. FRAUDES SEGÚN HORA INUSUAL
# ============================================================

fraude_hora = pd.crosstab(
    df["hora_inusual"],
    df["fraude"]
)

plt.figure(figsize=(8, 5))

fraude_hora.plot(
    kind="bar",
    ax=plt.gca()
)

plt.title(
    "Fraude según hora inusual"
)

plt.xlabel("Hora inusual")
plt.ylabel("Cantidad")

plt.xticks(
    [0, 1],
    ["No", "Sí"],
    rotation=0
)

plt.legend(
    ["Normal", "Fraude"]
)

plt.tight_layout()

plt.savefig(
    GRAFICOS_DIR / "10_hora_inusual.png",
    dpi=150
)

plt.close()


# ============================================================
# 19. FRAUDES SEGÚN VELOCIDAD DE OPERACIÓN
# ============================================================

if "velocidad_operacion" in df.columns:

    plt.figure(figsize=(10, 6))

    sns.boxplot(
        data=df,
        x="fraude",
        y="velocidad_operacion"
    )

    plt.title(
        "Velocidad de operación según tipo de transacción"
    )

    plt.xlabel("Tipo de operación")
    plt.ylabel("Velocidad de operación")

    plt.xticks(
        [0, 1],
        ["Normal", "Fraude"]
    )

    plt.tight_layout()

    plt.savefig(
        GRAFICOS_DIR / "11_velocidad_fraude.png",
        dpi=150
    )

    plt.close()


# ============================================================
# 20. MATRIZ DE CORRELACIÓN
# ============================================================

print("\n" + "=" * 60)
print("MATRIZ DE CORRELACIÓN")
print("=" * 60)

columnas_numericas = df.select_dtypes(
    include=np.number
)

correlacion = columnas_numericas.corr()

print(
    "\nCorrelación con la variable fraude:"
)

if "fraude" in correlacion.columns:

    correlacion_fraude = (
        correlacion["fraude"]
        .sort_values(
            ascending=False
        )
    )

    print(
        correlacion_fraude.round(3)
    )


plt.figure(figsize=(15, 11))

sns.heatmap(
    correlacion,
    annot=True,
    fmt=".2f",
    cmap="Blues",
    linewidths=0.5
)

plt.title(
    "Matriz de correlación de variables"
)

plt.tight_layout()

plt.savefig(
    GRAFICOS_DIR / "12_correlacion.png",
    dpi=150
)

plt.close()


# ============================================================
# 21. PRUEBA ESTADÍSTICA: MONTO NORMAL VS FRAUDE
# ============================================================

print("\n" + "=" * 60)
print("ANÁLISIS ESTADÍSTICO")
print("=" * 60)

montos_normales = df.loc[
    df["fraude"] == 0,
    "monto"
]

montos_fraude = df.loc[
    df["fraude"] == 1,
    "monto"
]

resultado_ttest = stats.ttest_ind(
    montos_normales,
    montos_fraude,
    equal_var=False
)

print(
    f"\nPrueba t de Welch:"
)

print(
    f"Estadístico t : {resultado_ttest.statistic:.4f}"
)

print(
    f"Valor p       : {resultado_ttest.pvalue:.6f}"
)


# ============================================================
# 22. IMPORTANCIA DE VARIABLES
# ============================================================

print("\n" + "=" * 60)
print("ANÁLISIS FINAL DE VARIABLES")
print("=" * 60)

columnas_excluir = [
    "id_transaccion",
    "fecha_hora",
    "puntaje_riesgo",
    "nivel_riesgo",
    "fraude",
    "producto"
]

columnas_excluir = [
    columna
    for columna in columnas_excluir
    if columna in df.columns
]

X = df.drop(
    columns=columnas_excluir
)

# Convertir posibles variables categóricas
X = pd.get_dummies(
    X,
    drop_first=True
)

y = df["fraude"]


print(
    "\nVariables utilizadas para análisis:"
)

for columna in X.columns:
    print(f" - {columna}")


# ============================================================
# 23. CORRELACIÓN DE VARIABLES CON FRAUDE
# ============================================================

datos_correlacion = pd.concat(
    [X, y],
    axis=1
)

correlacion_modelo = (
    datos_correlacion
    .corr()["fraude"]
    .drop("fraude")
    .abs()
    .sort_values(
        ascending=False
    )
)

print(
    "\nVariables con mayor relación con fraude:"
)

print(
    correlacion_modelo.head(15).round(4)
)

correlacion_modelo.to_csv(
    RESULTADOS_DIR / "relacion_variables_fraude.csv"
)


# ============================================================
# 24. RESUMEN FINAL
# ============================================================

print("\n" + "=" * 60)
print("          ANÁLISIS FINALIZADO")
print("=" * 60)

print("\nResumen:")

print(
    f"• Total de transacciones : {len(df):,}"
)

print(
    f"• Operaciones normales   : {normales:,}"
)

print(
    f"• Operaciones fraudulentas: {fraudes:,}"
)

print(
    f"• Porcentaje de fraude   : {porcentaje_fraude:.2f}%"
)

print(
    f"• Monto promedio         : S/ {promedio_monto:.2f}"
)

print(
    f"• Monto mediano          : S/ {mediana_monto:.2f}"
)

print(
    f"• Monto máximo           : S/ {maximo_monto:.2f}"
)

print(
    "\nGráficos guardados en:"
)

print(
    GRAFICOS_DIR
)

print(
    "\nResultados estadísticos guardados en:"
)

print(
    RESULTADOS_DIR
)

print("\nProceso terminado correctamente.\n")