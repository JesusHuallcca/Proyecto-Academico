# ============================================================
# RED NEURONAL CON PYTORCH
# PROYECTO: DETECCIÓN DE FRAUDE EN YAPE
# ============================================================

import pandas as pd
import numpy as np
import joblib
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

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


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

SEED = 42

np.random.seed(SEED)
torch.manual_seed(SEED)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "datos"
MODELOS_DIR = BASE_DIR / "modelos"
RESULTADOS_DIR = BASE_DIR / "resultados"

MODELOS_DIR.mkdir(exist_ok=True)
RESULTADOS_DIR.mkdir(exist_ok=True)

DATASET = DATA_DIR / "dataset_fraude_yape.csv"


print("=" * 70)
print("RED NEURONAL CON PYTORCH")
print("DETECCIÓN DE FRAUDE - YAPE")
print("=" * 70)


# ============================================================
# 2. CARGAR DATASET
# ============================================================

print("\n[1] Cargando dataset...")

df = pd.read_csv(DATASET)

print(f"Registros totales : {len(df):,}")
print(f"Variables         : {df.shape[1]}")


# ============================================================
# 3. PREPARACIÓN DE VARIABLES
# ============================================================

print("\n[2] Preparando variables...")


# Convertir fecha_hora a variables numéricas
if "fecha_hora" in df.columns:

    df["fecha_hora"] = pd.to_datetime(
        df["fecha_hora"],
        errors="coerce"
    )

    df["hora"] = df["fecha_hora"].dt.hour
    df["dia_semana"] = df["fecha_hora"].dt.dayofweek


# Variables que NO deben entrar al modelo
# porque contienen información directa del resultado
COLUMNAS_EXCLUIR = [
    "id_transaccion",
    "fecha_hora",
    "puntaje_riesgo",
    "nivel_riesgo",
    "fraude"
]


# Eliminar solamente las columnas que existan
COLUMNAS_EXCLUIR = [
    columna
    for columna in COLUMNAS_EXCLUIR
    if columna in df.columns
]


X = df.drop(columns=COLUMNAS_EXCLUIR)
y = df["fraude"].astype(int)


# ============================================================
# 4. CODIFICAR VARIABLES CATEGÓRICAS
# ============================================================

print("\n[3] Codificando variables categóricas...")

X = pd.get_dummies(
    X,
    columns=X.select_dtypes(include=["object"]).columns,
    dtype=int
)

# Convertir todo a numérico
X = X.apply(pd.to_numeric, errors="coerce")

# Reemplazar valores faltantes
X = X.fillna(0)

X = X.astype(np.float32)

print(f"Variables utilizadas: {X.shape[1]}")


# Guardar columnas utilizadas
columnas_modelo = list(X.columns)

joblib.dump(
    columnas_modelo,
    MODELOS_DIR / "columnas_pytorch.pkl"
)


# ============================================================
# 5. DIVIDIR TRAIN / TEST
# ============================================================

print("\n[4] Dividiendo dataset...")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=SEED,
    stratify=y
)

print(f"Entrenamiento : {len(X_train):,}")
print(f"Prueba        : {len(X_test):,}")


# ============================================================
# 6. NORMALIZACIÓN
# ============================================================

print("\n[5] Normalizando variables...")

scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

joblib.dump(
    scaler,
    MODELOS_DIR / "scaler_pytorch.pkl"
)


# ============================================================
# 7. CONVERTIR A TENSORES
# ============================================================

X_train_tensor = torch.tensor(
    X_train_scaled,
    dtype=torch.float32
)

X_test_tensor = torch.tensor(
    X_test_scaled,
    dtype=torch.float32
)

y_train_tensor = torch.tensor(
    y_train.values,
    dtype=torch.float32
).view(-1, 1)

y_test_tensor = torch.tensor(
    y_test.values,
    dtype=torch.float32
).view(-1, 1)


# ============================================================
# 8. CREAR DATASET Y DATALOADER
# ============================================================

train_dataset = TensorDataset(
    X_train_tensor,
    y_train_tensor
)

train_loader = DataLoader(
    train_dataset,
    batch_size=256,
    shuffle=True
)


# ============================================================
# 9. DEFINIR RED NEURONAL
# ============================================================

class RedNeuronalFraude(nn.Module):

    def __init__(self, numero_variables):

        super().__init__()

        self.red = nn.Sequential(

            nn.Linear(numero_variables, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.30),

            nn.Linear(128, 64),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Dropout(0.25),

            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.20),

            nn.Linear(32, 16),
            nn.ReLU(),

            nn.Linear(16, 1)
        )

    def forward(self, x):

        return self.red(x)


numero_variables = X_train.shape[1]

modelo = RedNeuronalFraude(numero_variables)


print("\n[6] Arquitectura de la red:")
print(modelo)


# ============================================================
# 10. CONFIGURAR ENTRENAMIENTO
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

modelo = modelo.to(device)

print(f"\nDispositivo utilizado: {device}")


# ============================================================
# 11. BALANCE DE CLASES
# ============================================================

cantidad_normal = (y_train == 0).sum()
cantidad_fraude = (y_train == 1).sum()

pos_weight = cantidad_normal / cantidad_fraude

pos_weight_tensor = torch.tensor(
    [pos_weight],
    dtype=torch.float32
).to(device)


print("\n[7] Balance de clases:")
print(f"Operaciones normales : {cantidad_normal:,}")
print(f"Operaciones fraude   : {cantidad_fraude:,}")
print(f"Peso de fraude       : {pos_weight:.4f}")


# ============================================================
# 12. FUNCIÓN DE PÉRDIDA Y OPTIMIZADOR
# ============================================================

criterio = nn.BCEWithLogitsLoss(
    pos_weight=pos_weight_tensor
)

optimizador = torch.optim.Adam(
    modelo.parameters(),
    lr=0.001
)


# ============================================================
# 13. ENTRENAMIENTO
# ============================================================

print("\n[8] Entrenando red neuronal...")
print("-" * 70)


EPOCHS = 40

historial = []

for epoch in range(EPOCHS):

    modelo.train()

    perdida_total = 0

    for datos, etiquetas in train_loader:

        datos = datos.to(device)
        etiquetas = etiquetas.to(device)

        optimizador.zero_grad()

        salida = modelo(datos)

        perdida = criterio(
            salida,
            etiquetas
        )

        perdida.backward()

        optimizador.step()

        perdida_total += perdida.item()


    perdida_promedio = (
        perdida_total / len(train_loader)
    )

    historial.append({
        "epoch": epoch + 1,
        "loss": perdida_promedio
    })


    if (epoch + 1) % 5 == 0 or epoch == 0:

        print(
            f"Epoch {epoch + 1:02d}/{EPOCHS} "
            f"- Loss: {perdida_promedio:.4f}"
        )


# ============================================================
# 14. GUARDAR HISTORIAL
# ============================================================

historial_df = pd.DataFrame(historial)

historial_df.to_csv(
    RESULTADOS_DIR / "historial_pytorch.csv",
    index=False
)


# ============================================================
# 15. EVALUACIÓN
# ============================================================

print("\n[9] Evaluando modelo...")

modelo.eval()

with torch.no_grad():

    X_test_device = X_test_tensor.to(device)

    salidas = modelo(X_test_device)

    probabilidades = torch.sigmoid(
        salidas
    ).cpu().numpy().flatten()


# Umbral de clasificación
predicciones = (
    probabilidades >= 0.50
).astype(int)


# ============================================================
# 16. MÉTRICAS
# ============================================================

accuracy = accuracy_score(
    y_test,
    predicciones
)

precision = precision_score(
    y_test,
    predicciones,
    zero_division=0
)

recall = recall_score(
    y_test,
    predicciones,
    zero_division=0
)

f1 = f1_score(
    y_test,
    predicciones,
    zero_division=0
)


# ============================================================
# 17. MOSTRAR RESULTADOS
# ============================================================

print("\n" + "=" * 70)
print("RESULTADOS PYTORCH")
print("=" * 70)

print(f"Registros totales : {len(df):,}")
print(f"Variables         : {X.shape[1]}")
print(f"Accuracy          : {accuracy:.4f}")
print(f"Precision         : {precision:.4f}")
print(f"Recall            : {recall:.4f}")
print(f"F1-Score          : {f1:.4f}")


# ============================================================
# 18. GUARDAR MÉTRICAS
# ============================================================

metricas = pd.DataFrame({

    "Modelo": ["PyTorch"],

    "Accuracy": [accuracy],

    "Precision": [precision],

    "Recall": [recall],

    "F1-Score": [f1]
})


metricas.to_csv(
    RESULTADOS_DIR / "metricas_pytorch.csv",
    index=False
)


# ============================================================
# 19. MATRIZ DE CONFUSIÓN
# ============================================================

matriz = confusion_matrix(
    y_test,
    predicciones
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

matriz_df.to_csv(
    RESULTADOS_DIR / "matriz_confusion_pytorch.csv"
)


# ============================================================
# 20. REPORTE DE CLASIFICACIÓN
# ============================================================

reporte = classification_report(
    y_test,
    predicciones,
    target_names=[
        "Normal",
        "Fraude"
    ],
    zero_division=0
)

with open(
    RESULTADOS_DIR / "reporte_pytorch.txt",
    "w",
    encoding="utf-8"
) as archivo:

    archivo.write(reporte)


print("\nReporte de clasificación:")
print(reporte)


# ============================================================
# 21. GUARDAR MODELO
# ============================================================

ruta_modelo = MODELOS_DIR / "modelo_pytorch.pth"

torch.save(
    {
        "model_state_dict": modelo.state_dict(),
        "numero_variables": numero_variables,
        "columnas": columnas_modelo
    },
    ruta_modelo
)


print("=" * 70)
print("MODELO PYTORCH GUARDADO CORRECTAMENTE")
print("=" * 70)

print(f"\nModelo : {ruta_modelo}")
print(
    f"Métricas : "
    f"{RESULTADOS_DIR / 'metricas_pytorch.csv'}"
)

print("\nProceso finalizado.")