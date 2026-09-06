# ============================================================
# COMPARACIÓN FINAL DE MODELOS
# PROYECTO: DETECCIÓN DE FRAUDE EN YAPE
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTADOS_DIR = BASE_DIR / "resultados"
GRAFICOS_DIR = BASE_DIR / "graficos"

RESULTADOS_DIR.mkdir(exist_ok=True)
GRAFICOS_DIR.mkdir(exist_ok=True)


print("=" * 70)
print("COMPARACIÓN FINAL DE MODELOS")
print("DETECCIÓN DE FRAUDE - YAPE")
print("=" * 70)


# ============================================================
# 2. CARGAR RESULTADOS DE SCIKIT-LEARN
# ============================================================

print("\n[1] Cargando resultados de Scikit-learn...")

archivo_sklearn = RESULTADOS_DIR / "comparacion_modelos.csv"

if archivo_sklearn.exists():

    df_sklearn = pd.read_csv(archivo_sklearn)

    print("Resultados de Scikit-learn encontrados.")

else:

    print("ADVERTENCIA: No se encontró comparacion_modelos.csv")

    df_sklearn = pd.DataFrame()


# ============================================================
# 3. CARGAR RESULTADOS DE TENSORFLOW
# ============================================================

print("\n[2] Cargando resultado de TensorFlow...")

archivo_tensorflow = RESULTADOS_DIR / "metricas_tensorflow.csv"

if archivo_tensorflow.exists():

    df_tensorflow = pd.read_csv(archivo_tensorflow)

    print("Resultado de TensorFlow encontrado.")

else:

    print("ADVERTENCIA: No se encontró metricas_tensorflow.csv")

    df_tensorflow = pd.DataFrame()


# ============================================================
# 4. CARGAR RESULTADOS DE PYTORCH
# ============================================================

print("\n[3] Cargando resultado de PyTorch...")

archivo_pytorch = RESULTADOS_DIR / "metricas_pytorch.csv"

if archivo_pytorch.exists():

    df_pytorch = pd.read_csv(archivo_pytorch)

    print("Resultado de PyTorch encontrado.")

else:

    print("ADVERTENCIA: No se encontró metricas_pytorch.csv")

    df_pytorch = pd.DataFrame()


# ============================================================
# 5. NORMALIZAR NOMBRES DE COLUMNAS
# ============================================================

def preparar_dataframe(df):

    if df.empty:
        return df

    columnas = {
        "F1": "F1-Score",
        "F1_Score": "F1-Score",
        "f1": "F1-Score",
        "f1_score": "F1-Score",
        "Accuracy": "Accuracy",
        "Precision": "Precision",
        "Recall": "Recall"
    }

    df = df.rename(columns=columnas)

    columnas_necesarias = [
        "Modelo",
        "Accuracy",
        "Precision",
        "Recall",
        "F1-Score"
    ]

    columnas_existentes = [
        columna
        for columna in columnas_necesarias
        if columna in df.columns
    ]

    return df[columnas_existentes]


df_sklearn = preparar_dataframe(df_sklearn)
df_tensorflow = preparar_dataframe(df_tensorflow)
df_pytorch = preparar_dataframe(df_pytorch)


# ============================================================
# 6. UNIR TODOS LOS MODELOS
# ============================================================

print("\n[4] Uniendo resultados...")

dataframes = []

if not df_sklearn.empty:
    dataframes.append(df_sklearn)

if not df_tensorflow.empty:
    dataframes.append(df_tensorflow)

if not df_pytorch.empty:
    dataframes.append(df_pytorch)


if not dataframes:

    print("ERROR: No se encontraron resultados para comparar.")
    exit()


comparacion = pd.concat(
    dataframes,
    ignore_index=True
)


# ============================================================
# 7. ORDENAR POR F1-SCORE
# ============================================================

comparacion = comparacion.sort_values(
    by="F1-Score",
    ascending=False
).reset_index(drop=True)


# ============================================================
# 8. GUARDAR RESULTADOS
# ============================================================

archivo_final = (
    RESULTADOS_DIR /
    "comparacion_final_modelos.csv"
)

comparacion.to_csv(
    archivo_final,
    index=False
)


# ============================================================
# 9. MOSTRAR TABLA
# ============================================================

print("\n" + "=" * 70)
print("RESULTADOS DE TODOS LOS MODELOS")
print("=" * 70)

print(
    comparacion.to_string(
        index=False
    )
)


# ============================================================
# 10. DETERMINAR MEJOR MODELO
# ============================================================

mejor_modelo = comparacion.iloc[0]

print("\n" + "=" * 70)
print("MEJOR MODELO")
print("=" * 70)

print(
    f"\nModelo seleccionado: "
    f"{mejor_modelo['Modelo']}"
)

print(
    f"Accuracy : "
    f"{mejor_modelo['Accuracy']:.4f}"
)

print(
    f"Precision: "
    f"{mejor_modelo['Precision']:.4f}"
)

print(
    f"Recall   : "
    f"{mejor_modelo['Recall']:.4f}"
)

print(
    f"F1-Score : "
    f"{mejor_modelo['F1-Score']:.4f}"
)


# ============================================================
# 11. GRÁFICO DE COMPARACIÓN
# ============================================================

print("\n[5] Generando gráfico de comparación...")


metricas = [
    "Accuracy",
    "Precision",
    "Recall",
    "F1-Score"
]


for metrica in metricas:

    plt.figure(figsize=(12, 6))

    plt.bar(
        comparacion["Modelo"],
        comparacion[metrica]
    )

    plt.title(
        f"Comparación de modelos - {metrica}"
    )

    plt.ylabel(metrica)

    plt.xlabel("Modelo")

    plt.xticks(
        rotation=25,
        ha="right"
    )

    plt.ylim(0, 1)

    plt.tight_layout()

    nombre_archivo = (
        f"comparacion_{metrica.lower().replace('-', '_')}.png"
    )

    plt.savefig(
        GRAFICOS_DIR / nombre_archivo,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


# ============================================================
# 12. GRÁFICO GENERAL
# ============================================================

plt.figure(figsize=(14, 7))

ancho = 0.20

x = range(len(comparacion))

for i, metrica in enumerate(metricas):

    posiciones = [
        valor + (i - 1.5) * ancho
        for valor in x
    ]

    plt.bar(
        posiciones,
        comparacion[metrica],
        width=ancho,
        label=metrica
    )


plt.xticks(
    list(x),
    comparacion["Modelo"],
    rotation=25,
    ha="right"
)

plt.ylabel("Valor")

plt.xlabel("Modelo")

plt.title(
    "Comparación general de modelos de Machine Learning"
)

plt.ylim(0, 1)

plt.legend()

plt.tight_layout()

plt.savefig(
    GRAFICOS_DIR / "comparacion_general_modelos.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 13. GUARDAR MEJOR MODELO EN ARCHIVO TXT
# ============================================================

archivo_mejor = (
    RESULTADOS_DIR /
    "mejor_modelo.txt"
)

with open(
    archivo_mejor,
    "w",
    encoding="utf-8"
) as archivo:

    archivo.write(
        "MEJOR MODELO - DETECCIÓN DE FRAUDE\n"
    )

    archivo.write("=" * 50 + "\n\n")

    archivo.write(
        f"Modelo: {mejor_modelo['Modelo']}\n"
    )

    archivo.write(
        f"Accuracy: {mejor_modelo['Accuracy']:.4f}\n"
    )

    archivo.write(
        f"Precision: {mejor_modelo['Precision']:.4f}\n"
    )

    archivo.write(
        f"Recall: {mejor_modelo['Recall']:.4f}\n"
    )

    archivo.write(
        f"F1-Score: {mejor_modelo['F1-Score']:.4f}\n"
    )


# ============================================================
# 14. FINAL
# ============================================================

print("\n" + "=" * 70)
print("PROCESO COMPLETADO")
print("=" * 70)

print(
    f"\nTabla final: {archivo_final}"
)

print(
    f"Mejor modelo: {mejor_modelo['Modelo']}"
)

print(
    f"\nGráficos guardados en:"
    f"\n{GRAFICOS_DIR}"
)

print("\n")