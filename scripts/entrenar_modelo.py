# ============================================================
# ENTRENAMIENTO DE MODELOS DE MACHINE LEARNING
# PROYECTO BCP / YAPE - DETECCIÓN DE FRAUDE
# ============================================================

import pandas as pd
import numpy as np
import joblib

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier
)

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


# ============================================================
# 1. CONFIGURACIÓN DE RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATOS_DIR = BASE_DIR / "datos"
MODELOS_DIR = BASE_DIR / "modelos"
RESULTADOS_DIR = BASE_DIR / "resultados"
GRAFICOS_DIR = BASE_DIR / "graficos"

MODELOS_DIR.mkdir(exist_ok=True)
RESULTADOS_DIR.mkdir(exist_ok=True)
GRAFICOS_DIR.mkdir(exist_ok=True)

RUTA_DATASET = DATOS_DIR / "dataset_fraude_yape.csv"


# ============================================================
# 2. PRESENTACIÓN
# ============================================================

print("\n" + "=" * 70)
print("       ENTRENAMIENTO DE MODELOS DE MACHINE LEARNING")
print("             PROYECTO BCP / YAPE - FRAUDE")
print("=" * 70)


# ============================================================
# 3. VERIFICAR DATASET
# ============================================================

if not RUTA_DATASET.exists():

    print("\nERROR: No se encontró el dataset.")

    print("Ruta esperada:")
    print(RUTA_DATASET)

    raise FileNotFoundError(
        f"No existe el archivo: {RUTA_DATASET}"
    )


# ============================================================
# 4. CARGAR DATASET
# ============================================================

print("\n" + "=" * 70)
print("1. CARGANDO DATASET")
print("=" * 70)

df = pd.read_csv(RUTA_DATASET)

print("\nDataset cargado correctamente.")

print(
    f"Registros : {len(df):,}"
)

print(
    f"Columnas  : {len(df.columns)}"
)


# ============================================================
# 5. VERIFICAR VARIABLE OBJETIVO
# ============================================================

if "fraude" not in df.columns:

    raise ValueError(
        "La columna 'fraude' no existe en el dataset."
    )


print("\nDistribución de la variable objetivo:")

print(
    df["fraude"].value_counts()
)


# ============================================================
# 6. CREAR VARIABLES A PARTIR DE FECHA
# ============================================================

print("\n" + "=" * 70)
print("2. PREPARANDO VARIABLES")
print("=" * 70)


# Convertir fecha_hora a datetime si existe
if "fecha_hora" in df.columns:

    df["fecha_hora"] = pd.to_datetime(
        df["fecha_hora"],
        errors="coerce"
    )

    # Extraer información útil
    df["hora"] = df["fecha_hora"].dt.hour
    df["dia_semana"] = df["fecha_hora"].dt.dayofweek


# ============================================================
# 7. DEFINIR VARIABLES
# ============================================================

# Estas variables NO deben entrar al modelo.
#
# puntaje_riesgo y nivel_riesgo se excluyen porque fueron
# utilizados para generar la variable fraude.
#
# id_transaccion no aporta información predictiva.
#
# fecha_hora se reemplaza por hora y dia_semana.

columnas_excluir = [
    "id_transaccion",
    "fecha_hora",
    "puntaje_riesgo",
    "nivel_riesgo",
    "fraude"
]


columnas_excluir = [
    columna
    for columna in columnas_excluir
    if columna in df.columns
]


X = df.drop(
    columns=columnas_excluir
)

y = df["fraude"]


# ============================================================
# 8. CONVERTIR VARIABLES CATEGÓRICAS
# ============================================================

print("\nVariables originales:")

print(
    X.columns.tolist()
)


# One-Hot Encoding
#
# Ejemplo:
#
# producto
# Yape
# Compra
# Recarga
#
# se convierte en columnas numéricas.

columnas_categoricas = X.select_dtypes(
    include=["object", "category"]
).columns.tolist()


if columnas_categoricas:

    print("\nVariables categóricas encontradas:")

    for columna in columnas_categoricas:

        print(
            f" - {columna}"
        )

    X = pd.get_dummies(
        X,
        columns=columnas_categoricas,
        drop_first=False,
        dtype=int
    )


# ============================================================
# 9. LIMPIEZA DE DATOS
# ============================================================

print("\nVerificando valores faltantes...")

valores_nulos = X.isnull().sum().sum()

print(
    f"Valores nulos encontrados: {valores_nulos}"
)


if valores_nulos > 0:

    print(
        "Se reemplazarán los valores nulos por la mediana."
    )

    X = X.fillna(
        X.median(numeric_only=True)
    )


# Convertir todo a valores numéricos
X = X.astype(float)


print(
    f"\nCantidad final de variables: {X.shape[1]}"
)


print("\nVariables utilizadas por los modelos:")

for columna in X.columns:

    print(
        f" - {columna}"
    )


# ============================================================
# 10. GUARDAR LISTA DE VARIABLES
# ============================================================

columnas_modelo = X.columns.tolist()

joblib.dump(
    columnas_modelo,
    MODELOS_DIR / "columnas_modelo.pkl"
)

print(
    "\nLista de variables guardada en:"
)

print(
    MODELOS_DIR / "columnas_modelo.pkl"
)


# ============================================================
# 11. DIVISIÓN TRAIN / TEST
# ============================================================

print("\n" + "=" * 70)
print("3. DIVISIÓN TRAIN / TEST")
print("=" * 70)


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


print(
    f"\nDatos de entrenamiento: {len(X_train):,}"
)

print(
    f"Datos de prueba       : {len(X_test):,}"
)


print(
    f"\nPorcentaje entrenamiento: "
    f"{len(X_train) / len(X) * 100:.0f}%"
)

print(
    f"Porcentaje prueba       : "
    f"{len(X_test) / len(X) * 100:.0f}%"
)


# ============================================================
# 12. NORMALIZACIÓN
# ============================================================

print("\n" + "=" * 70)
print("4. NORMALIZACIÓN CON STANDARD SCALER")
print("=" * 70)


scaler = StandardScaler()


# IMPORTANTE:
# El scaler solamente aprende con los datos de entrenamiento.

X_train_scaled = scaler.fit_transform(
    X_train
)


X_test_scaled = scaler.transform(
    X_test
)


print(
    "\nStandardScaler aplicado correctamente."
)


# Guardar scaler
ruta_scaler = MODELOS_DIR / "scaler_fraude.pkl"

joblib.dump(
    scaler,
    ruta_scaler
)


print(
    "Scaler guardado en:"
)

print(
    ruta_scaler
)


# ============================================================
# 13. CREAR MODELOS
# ============================================================

print("\n" + "=" * 70)
print("5. CREANDO MODELOS")
print("=" * 70)


modelos = {

    "Regresión Logística":
        LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42
        ),

    "Árbol de Decisión":
        DecisionTreeClassifier(
            max_depth=8,
            min_samples_split=10,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42
        ),

    "Random Forest":
        RandomForestClassifier(
            n_estimators=250,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        ),

    "Gradient Boosting":
        GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=5,
            min_samples_split=10,
            random_state=42
        )
}


print("\nModelos preparados:")

for nombre in modelos:

    print(
        f" - {nombre}"
    )


# ============================================================
# 14. ENTRENAMIENTO
# ============================================================

print("\n" + "=" * 70)
print("6. ENTRENAMIENTO DE MODELOS")
print("=" * 70)


resultados = []

matrices_confusion = {}

reportes = {}

modelos_entrenados = {}


for nombre, modelo in modelos.items():

    print("\n" + "-" * 70)

    print(
        f"ENTRENANDO: {nombre}"
    )

    print("-" * 70)


    # --------------------------------------------------------
    # Entrenamiento
    # --------------------------------------------------------

    modelo.fit(
        X_train_scaled,
        y_train
    )


    # --------------------------------------------------------
    # Predicción
    # --------------------------------------------------------

    y_pred = modelo.predict(
        X_test_scaled
    )


    # --------------------------------------------------------
    # Métricas
    # --------------------------------------------------------

    accuracy = accuracy_score(
        y_test,
        y_pred
    )

    precision = precision_score(
        y_test,
        y_pred,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        y_pred,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        y_pred,
        zero_division=0
    )


    # --------------------------------------------------------
    # Matriz de confusión
    # --------------------------------------------------------

    matriz = confusion_matrix(
        y_test,
        y_pred
    )


    # --------------------------------------------------------
    # Guardar resultados
    # --------------------------------------------------------

    resultados.append({

        "Modelo": nombre,

        "Accuracy": round(
            accuracy,
            4
        ),

        "Precision": round(
            precision,
            4
        ),

        "Recall": round(
            recall,
            4
        ),

        "F1-Score": round(
            f1,
            4
        )
    })


    matrices_confusion[nombre] = matriz

    reportes[nombre] = classification_report(
        y_test,
        y_pred,
        target_names=[
            "Normal",
            "Fraude"
        ],
        zero_division=0
    )


    modelos_entrenados[nombre] = modelo


    # --------------------------------------------------------
    # Mostrar métricas
    # --------------------------------------------------------

    print(
        f"\nAccuracy : {accuracy:.4f}"
    )

    print(
        f"Precision: {precision:.4f}"
    )

    print(
        f"Recall   : {recall:.4f}"
    )

    print(
        f"F1-Score : {f1:.4f}"
    )


# ============================================================
# 15. COMPARACIÓN DE MODELOS
# ============================================================

print("\n" + "=" * 70)
print("7. COMPARACIÓN DE MODELOS")
print("=" * 70)


resultados_df = pd.DataFrame(
    resultados
)


# Ordenar por F1-Score
resultados_df = resultados_df.sort_values(
    by="F1-Score",
    ascending=False
).reset_index(
    drop=True
)


print("\n")

print(
    resultados_df.to_string(
        index=False
    )
)


# ============================================================
# 16. GUARDAR COMPARACIÓN
# ============================================================

ruta_comparacion = (
    RESULTADOS_DIR /
    "comparacion_modelos.csv"
)


resultados_df.to_csv(
    ruta_comparacion,
    index=False
)


print(
    "\nComparación guardada en:"
)

print(
    ruta_comparacion
)


# ============================================================
# 17. SELECCIONAR MEJOR MODELO
# ============================================================

mejor_nombre = resultados_df.iloc[0]["Modelo"]

mejor_f1 = resultados_df.iloc[0]["F1-Score"]

mejor_modelo = modelos_entrenados[
    mejor_nombre
]


print("\n" + "=" * 70)
print("8. MEJOR MODELO")
print("=" * 70)


print(
    f"\nModelo seleccionado: {mejor_nombre}"
)

print(
    f"F1-Score: {mejor_f1:.4f}"
)


# ============================================================
# 18. GUARDAR MEJOR MODELO
# ============================================================

ruta_modelo = (
    MODELOS_DIR /
    "modelo_fraude.pkl"
)


joblib.dump(
    mejor_modelo,
    ruta_modelo
)


print(
    "\nMejor modelo guardado en:"
)

print(
    ruta_modelo
)


# ============================================================
# 19. MATRIZ DE CONFUSIÓN DEL MEJOR MODELO
# ============================================================

print("\n" + "=" * 70)
print("9. MATRIZ DE CONFUSIÓN")
print("=" * 70)


y_pred_mejor = mejor_modelo.predict(
    X_test_scaled
)


matriz_mejor = confusion_matrix(
    y_test,
    y_pred_mejor
)


print(
    "\nMatriz de confusión:"
)

print(
    matriz_mejor
)


# Guardar matriz
matriz_df = pd.DataFrame(

    matriz_mejor,

    index=[
        "Real_Normal",
        "Real_Fraude"
    ],

    columns=[
        "Pred_Normal",
        "Pred_Fraude"
    ]
)


ruta_matriz = (
    RESULTADOS_DIR /
    "matriz_confusion.csv"
)


matriz_df.to_csv(
    ruta_matriz
)


print(
    "\nMatriz guardada en:"
)

print(
    ruta_matriz
)


# ============================================================
# 20. REPORTE DE CLASIFICACIÓN
# ============================================================

print("\n" + "=" * 70)
print("10. REPORTE DE CLASIFICACIÓN")
print("=" * 70)


reporte = classification_report(

    y_test,

    y_pred_mejor,

    target_names=[
        "Normal",
        "Fraude"
    ],

    zero_division=0
)


print(
    "\n"
)

print(
    reporte
)


ruta_reporte = (
    RESULTADOS_DIR /
    "reporte_clasificacion.txt"
)


with open(
    ruta_reporte,
    "w",
    encoding="utf-8"
) as archivo:

    archivo.write(
        f"MODELO: {mejor_nombre}\n\n"
    )

    archivo.write(
        reporte
    )


print(
    "Reporte guardado en:"
)

print(
    ruta_reporte
)


# ============================================================
# 21. GUARDAR RESULTADOS COMPLETOS
# ============================================================

print("\n" + "=" * 70)
print("11. RESULTADOS COMPLETOS")
print("=" * 70)


resultados_completos = pd.DataFrame(
    resultados
)


ruta_resultados = (
    RESULTADOS_DIR /
    "metricas_modelos.csv"
)


resultados_completos.to_csv(
    ruta_resultados,
    index=False
)


print(
    "\nMétricas guardadas en:"
)

print(
    ruta_resultados
)


# ============================================================
# 22. RESUMEN FINAL
# ============================================================

print("\n" + "=" * 70)
print("              ENTRENAMIENTO COMPLETADO")
print("=" * 70)


print(
    f"\nTotal de registros utilizados: {len(df):,}"
)

print(
    f"Variables utilizadas         : {X.shape[1]}"
)

print(
    f"Modelos entrenados           : {len(modelos)}"
)

print(
    f"\nMEJOR MODELO:"
)

print(
    f"   {mejor_nombre}"
)

print(
    f"\nF1-Score:"
)

print(
    f"   {mejor_f1:.4f}"
)

print(
    "\nArchivos principales:"
)

print(
    f"   Modelo : {ruta_modelo}"
)

print(
    f"   Scaler : {ruta_scaler}"
)

print(
    f"   Variables: "
    f"{MODELOS_DIR / 'columnas_modelo.pkl'}"
)

print(
    f"\nResultados:"
)

print(
    f"   {RESULTADOS_DIR}"
)

print("\n" + "=" * 70)