==============================================
       PRUEBAS DEL SISTEMA DE FRAUDE
              BCP - YAPE
==============================================


OBJETIVO
----------------------------------------------

Comprobar el funcionamiento del modelo de
Machine Learning mediante diferentes casos
de transacciones.


PRUEBA 01
----------------------------------------------

Tipo:
Transacción normal.

Resultado esperado:
NORMAL.

Resultado obtenido:
NORMAL.

Probabilidad normal:
99.95%

Probabilidad de fraude:
0.05%


PRUEBA 02
----------------------------------------------

Tipo:
Transacción sospechosa.

Resultado esperado:
POSIBLE FRAUDE.

Resultado obtenido:
POSIBLE FRAUDE.

Probabilidad normal:
0.00%

Probabilidad de fraude:
100.00%


CONCLUSIÓN
----------------------------------------------

Las pruebas realizadas muestran que el modelo
puede diferenciar entre una transacción con
características normales y una transacción con
múltiples señales de riesgo.

El modelo final utilizado es Gradient Boosting,
seleccionado por presentar el mejor desempeño
general en la comparación de modelos.


NOTA
----------------------------------------------

Los datos utilizados son sintéticos y fueron
generados con fines académicos. No representan
datos reales de clientes ni transacciones reales
de BCP o Yape.