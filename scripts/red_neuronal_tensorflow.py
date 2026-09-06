# ============================================================
# RED NEURONAL CON TENSORFLOW / KERAS
# PROYECTO BCP / YAPE - DETECCIÓN DE FRAUDE
# ============================================================

import pandas as pd
import numpy as np
import joblib
import tensorflow as tf

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    Dense,
    Dropout,
    BatchNormalization,
    Input
)

from tensorflow.keras.callbacks import (
    EarlyStopping,
    ReduceLROnPlateau,
    ModelCheckpoint
)


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATOS_DIR = BASE_DIR / "datos"
MODELOS_DIR = BASE_DIR / "modelos"
RESULTADOS_DIR = BASE_DIR / "resultados"
GRAFICOS_DIR = BASE_DIR / "graficos"

MODELOS_DIR.mkdir(exist_ok=True)
RESULTADOS_DIR.mkdir(exist_ok=True)
GRAFICOS_DIR.mkdir(exist_ok=True)

RUTA_DATASET = (
    DATOS_DIR /
    "dataset_fraude_yape.csv"
)


# ============================================================
# 2. CONFIGURACIÓN DE TENSORFLOW
# ============================================================

SEED = 42

np.random.seed(SEED)
tf.random.set_seed(SEED)


# ============================================================
# 3. PRESENTACIÓN
# ============================================================

print("\n" + "=" * 70)
print("       RED NEURONAL CON TENSORFLOW / KERAS")
print("          PROYECTO BCP / YAPE - FRAUDE")
print("=" * 70)

print(
    f"\nVersión de TensorFlow: {tf.__version__}"
)


# ============================================================
# 4. VERIFICAR DATASET
# ============================================================

if not RUTA_DATASET.exists():

    print("\nERROR: No se encontró el dataset.")

    print(
        "Ruta esperada:"
    )

    print(
        RUTA_DATASET
    )

    raise FileNotFoundError(
        f"No existe: {RUTA_DATASET}"
    )


# ============================================================
# 5. CARGAR DATASET
# ============================================================

print("\n" + "=" * 70)
print("1. CARGANDO DATASET")
print("=" * 70)

df = pd.read_csv(
    RUTA_DATASET
)

print(
    f"\nRegistros: {len(df):,}"
)

print(
    f"Columnas: {len(df.columns)}"
)


# ============================================================
# 6. VERIFICAR VARIABLE OBJETIVO
# ============================================================

if "fraude" not in df.columns:

    raise ValueError(
        "No existe la columna 'fraude'."
    )


y = df["fraude"].astype(int)


print("\nDistribución de fraude:")

print(
    y.value_counts()
)

print(
    f"\nOperaciones normales: {(y == 0).sum():,}"
)

print(
    f"Operaciones fraudulentas: {(y == 1).sum():,}"
)


# ============================================================
# 7. PREPARACIÓN DE VARIABLES
# ============================================================

print("\n" + "=" * 70)
print("2. PREPARANDO VARIABLES")
print("=" * 70)


# ------------------------------------------------------------
# Convertir fecha_hora
# ------------------------------------------------------------

if "fecha_hora" in df.columns:

    df["fecha_hora"] = pd.to_datetime(
        df["fecha_hora"],
        errors="coerce"
    )

    # Extraemos variables útiles
    df["hora"] = (
        df["fecha_hora"]
        .dt.hour
    )

    df["dia_semana"] = (
        df["fecha_hora"]
        .dt.dayofweek
    )


# ------------------------------------------------------------
# Columnas que NO deben utilizarse
# ------------------------------------------------------------

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


# ============================================================
# 8. CONVERTIR VARIABLES CATEGÓRICAS
# ============================================================

print("\nVariables antes del encoding:")

print(
    X.columns.tolist()
)


columnas_categoricas = (
    X.select_dtypes(
        include=["object", "category"]
    )
    .columns
    .tolist()
)


if columnas_categoricas:

    print(
        "\nVariables categóricas:"
    )

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
# 9. LIMPIAR VALORES NULOS
# ============================================================

print("\nVerificando valores nulos...")

nulos = X.isnull().sum().sum()

print(
    f"Valores nulos: {nulos}"
)


if nulos > 0:

    X = X.fillna(
        X.median(
            numeric_only=True
        )
    )


# Convertir todo a número
X = X.astype(float)


# ============================================================
# 10. GUARDAR COLUMNAS DEL MODELO
# ============================================================

columnas_modelo = X.columns.tolist()


ruta_columnas = (
    MODELOS_DIR /
    "columnas_tensorflow.pkl"
)


joblib.dump(
    columnas_modelo,
    ruta_columnas
)


print(
    f"\nVariables finales: {len(columnas_modelo)}"
)

print(
    "Columnas guardadas en:"
)

print(
    ruta_columnas
)


# ============================================================
# 11. DIVISIÓN TRAIN / TEST
# ============================================================

print("\n" + "=" * 70)
print("3. DIVISIÓN DE DATOS")
print("=" * 70)


X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,

    test_size=0.20,

    random_state=SEED,

    stratify=y
)


print(
    f"\nEntrenamiento: {len(X_train):,}"
)

print(
    f"Prueba: {len(X_test):,}"
)


# ============================================================
# 12. DIVISIÓN TRAIN / VALIDACIÓN
# ============================================================

X_train, X_val, y_train, y_val = train_test_split(

    X_train,
    y_train,

    test_size=0.20,

    random_state=SEED,

    stratify=y_train
)


print(
    f"\nEntrenamiento final: {len(X_train):,}"
)

print(
    f"Validación: {len(X_val):,}"
)

print(
    f"Prueba: {len(X_test):,}"
)


# ============================================================
# 13. NORMALIZACIÓN
# ============================================================

print("\n" + "=" * 70)
print("4. NORMALIZACIÓN")
print("=" * 70)


scaler = StandardScaler()


X_train_scaled = scaler.fit_transform(
    X_train
)


X_val_scaled = scaler.transform(
    X_val
)


X_test_scaled = scaler.transform(
    X_test
)


print(
    "\nStandardScaler aplicado correctamente."
)


# Guardar scaler específico de TensorFlow
ruta_scaler = (
    MODELOS_DIR /
    "scaler_tensorflow.pkl"
)


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
# 14. PESOS DE LAS CLASES
# ============================================================

print("\n" + "=" * 70)
print("5. BALANCE DE CLASES")
print("=" * 70)


cantidad_normal = (
    y_train == 0
).sum()


cantidad_fraude = (
    y_train == 1
).sum()


total_train = (
    len(y_train)
)


peso_normal = (
    total_train /
    (2 * cantidad_normal)
)


peso_fraude = (
    total_train /
    (2 * cantidad_fraude)
)


class_weight = {

    0: peso_normal,

    1: peso_fraude
}


print(
    f"\nPeso clase Normal : {peso_normal:.4f}"
)

print(
    f"Peso clase Fraude : {peso_fraude:.4f}"
)


# ============================================================
# 15. CREAR RED NEURONAL
# ============================================================

print("\n" + "=" * 70)
print("6. CREANDO RED NEURONAL")
print("=" * 70)


numero_variables = X_train_scaled.shape[1]


modelo = Sequential([

    Input(
        shape=(numero_variables,)
    ),

    Dense(
        128,
        activation="relu"
    ),

    BatchNormalization(),

    Dropout(
        0.30
    ),

    Dense(
        64,
        activation="relu"
    ),

    BatchNormalization(),

    Dropout(
        0.25
    ),

    Dense(
        32,
        activation="relu"
    ),

    Dropout(
        0.20
    ),

    Dense(
        16,
        activation="relu"
    ),

    Dense(
        1,
        activation="sigmoid"
    )
])


# ============================================================
# 16. COMPILAR MODELO
# ============================================================

modelo.compile(

    optimizer=tf.keras.optimizers.Adam(
        learning_rate=0.001
    ),

    loss="binary_crossentropy",

    metrics=[
        "accuracy"
    ]
)


print(
    "\nArquitectura de la red:"
)

modelo.summary()


# ============================================================
# 17. CALLBACKS
# ============================================================

ruta_modelo_temporal = (
    MODELOS_DIR /
    "mejor_red_tensorflow.keras"
)


early_stopping = EarlyStopping(

    monitor="val_loss",

    patience=10,

    restore_best_weights=True,

    verbose=1
)


reduce_lr = ReduceLROnPlateau(

    monitor="val_loss",

    factor=0.5,

    patience=5,

    min_lr=0.00001,

    verbose=1
)


checkpoint = ModelCheckpoint(

    filepath=str(
        ruta_modelo_temporal
    ),

    monitor="val_loss",

    save_best_only=True,

    verbose=1
)


# ============================================================
# 18. ENTRENAMIENTO
# ============================================================

print("\n" + "=" * 70)
print("7. ENTRENANDO RED NEURONAL")
print("=" * 70)


historial = modelo.fit(

    X_train_scaled,

    y_train,

    validation_data=(
        X_val_scaled,
        y_val
    ),

    epochs=50,

    batch_size=256,

    class_weight=class_weight,

    callbacks=[
        early_stopping,
        reduce_lr,
        checkpoint
    ],

    verbose=1
)


# ============================================================
# 19. EVALUACIÓN DEL MODELO
# ============================================================

print("\n" + "=" * 70)
print("8. EVALUACIÓN")
print("=" * 70)


loss_test, accuracy_keras = (
    modelo.evaluate(
        X_test_scaled,
        y_test,
        verbose=0
    )
)


print(
    f"\nLoss: {loss_test:.4f}"
)

print(
    f"Accuracy TensorFlow: "
    f"{accuracy_keras:.4f}"
)


# ============================================================
# 20. PREDICCIONES
# ============================================================

probabilidades = modelo.predict(
    X_test_scaled,
    verbose=0
).ravel()


# Umbral inicial
umbral = 0.50


y_pred = (
    probabilidades >= umbral
).astype(int)


# ============================================================
# 21. MÉTRICAS
# ============================================================

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


print("\n" + "=" * 70)
print("9. MÉTRICAS DE TENSORFLOW")
print("=" * 70)


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
# 22. GUARDAR MÉTRICAS
# ============================================================

metricas = pd.DataFrame({

    "Modelo": [
        "TensorFlow / Keras"
    ],

    "Accuracy": [
        round(
            accuracy,
            4
        )
    ],

    "Precision": [
        round(
            precision,
            4
        )
    ],

    "Recall": [
        round(
            recall,
            4
        )
    ],

    "F1-Score": [
        round(
            f1,
            4
        )
    ]
})


ruta_metricas = (
    RESULTADOS_DIR /
    "metricas_tensorflow.csv"
)


metricas.to_csv(
    ruta_metricas,
    index=False
)


print(
    "\nMétricas guardadas en:"
)

print(
    ruta_metricas
)


# ============================================================
# 23. MATRIZ DE CONFUSIÓN
# ============================================================

matriz = confusion_matrix(
    y_test,
    y_pred
)


print("\n" + "=" * 70)
print("10. MATRIZ DE CONFUSIÓN")
print("=" * 70)


print(
    "\n"
)

print(
    matriz
)


matriz_df = pd.DataFrame(

    matriz,

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
    "matriz_confusion_tensorflow.csv"
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
# 24. REPORTE DE CLASIFICACIÓN
# ============================================================

reporte = classification_report(

    y_test,

    y_pred,

    target_names=[
        "Normal",
        "Fraude"
    ],

    zero_division=0
)


print("\n" + "=" * 70)
print("11. REPORTE DE CLASIFICACIÓN")
print("=" * 70)


print(
    "\n"
)

print(
    reporte
)


ruta_reporte = (
    RESULTADOS_DIR /
    "reporte_tensorflow.txt"
)


with open(
    ruta_reporte,
    "w",
    encoding="utf-8"
) as archivo:

    archivo.write(
        "RED NEURONAL TENSORFLOW / KERAS\n"
    )

    archivo.write(
        f"\nUmbral utilizado: {umbral}\n"
    )

    archivo.write(
        f"\nAccuracy: {accuracy:.4f}\n"
    )

    archivo.write(
        f"Precision: {precision:.4f}\n"
    )

    archivo.write(
        f"Recall: {recall:.4f}\n"
    )

    archivo.write(
        f"F1-Score: {f1:.4f}\n\n"
    )

    archivo.write(
        reporte
    )


# ============================================================
# 25. GUARDAR MODELO FINAL
# ============================================================

ruta_modelo_final = (
    MODELOS_DIR /
    "modelo_tensorflow.keras"
)


modelo.save(
    ruta_modelo_final
)


print("\n" + "=" * 70)
print("12. GUARDANDO MODELO")
print("=" * 70)


print(
    "\nModelo TensorFlow guardado en:"
)

print(
    ruta_modelo_final
)


# ============================================================
# 26. GUARDAR HISTORIAL
# ============================================================

historial_df = pd.DataFrame(
    historial.history
)


ruta_historial = (
    RESULTADOS_DIR /
    "historial_tensorflow.csv"
)


historial_df.to_csv(
    ruta_historial,
    index=False
)


print(
    "\nHistorial de entrenamiento guardado en:"
)

print(
    ruta_historial
)


# ============================================================
# 27. RESUMEN FINAL
# ============================================================

print("\n" + "=" * 70)
print("       ENTRENAMIENTO TENSORFLOW COMPLETADO")
print("=" * 70)


print(
    f"\nRegistros totales : {len(df):,}"
)

print(
    f"Variables         : {numero_variables}"
)

print(
    f"Accuracy          : {accuracy:.4f}"
)

print(
    f"Precision         : {precision:.4f}"
)

print(
    f"Recall            : {recall:.4f}"
)

print(
    f"F1-Score          : {f1:.4f}"
)

print(
    "\nModelo:"
)

print(
    ruta_modelo_final
)

print(
    "\nResultados:"
)

print(
    RESULTADOS_DIR
)

print(
    "\nProceso finalizado correctamente."
)

print("=" * 70)