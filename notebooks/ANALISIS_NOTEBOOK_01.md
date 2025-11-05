# Análisis Completo del Notebook: 01_eda_clustering.ipynb

## Fecha de Análisis

2025-11-03

---

## 1. ANÁLISIS EXPLORATORIO DE DATOS (EDA)

### 1.1 Carga de Datos

**Resultados:**

- Dataset de Conductores: 350 registros con 14 columnas
- Dataset de Rutas: 150 registros con 11 columnas

**Análisis:**
Los datasets tienen un tamaño adecuado para el análisis. La proporción de 350 conductores para 150 rutas (ratio 2.33:1) sugiere que habrá competencia entre conductores por las rutas disponibles, lo cual es realista para un sistema de matching.

---

### 1.2 Análisis de Conductores

#### 1.2.1 Estadísticas Descriptivas de Conductores

**Métricas Clave:**

| Métrica                | Media  | Desv. Std | Min   | Max    |
| ---------------------- | ------ | --------- | ----- | ------ |
| Safety Score           | 78.08  | 8.63      | 47.50 | 95.07  |
| Efficiency Score       | 70.91  | 8.87      | 28.44 | 91.84  |
| Compliance Score       | 79.80  | 7.28      | 55.37 | 96.46  |
| Driving Aggressiveness | 30.74  | 16.53     | 1.16  | 74.77  |
| Energy Efficiency      | 81.17  | 13.74     | 41.53 | 100.00 |
| Driven KM              | 15,023 | 4,914     | 5,000 | 28,225 |
| Driver Score Base      | 76.00  | 5.55      | 55.38 | 87.19  |

**Análisis:**

1. **Safety Score (78.08 ± 8.63)**: La mayoría de conductores tienen un nivel de seguridad aceptable, con una distribución relativamente normal. La desviación estándar moderada indica cierta variabilidad en los comportamientos de seguridad.

2. **Efficiency Score (70.91 ± 8.87)**: Puntuación más baja que Safety y Compliance, sugiriendo que la eficiencia operativa es un área de mejora para muchos conductores.

3. **Compliance Score (79.80 ± 7.28)**: Alta puntuación media con baja desviación, indicando que la mayoría de conductores cumplen bien con las normativas.

4. **Driving Aggressiveness (30.74 ± 16.53)**: Alta variabilidad (desv. std ~54% de la media), lo que indica diferencias significativas en estilos de conducción.

5. **Energy Efficiency (81.17 ± 13.74)**: Buena puntuación general, aunque hay margen de mejora para algunos conductores.

6. **Driven KM**: Amplio rango (5,000 - 28,225 km), sugiriendo diferentes niveles de experiencia y disponibilidad.

#### 1.2.2 Distribución de Scores de Conductores

**Observaciones de los Histogramas:**

1. **Safety Score**: Distribución ligeramente sesgada a la izquierda, con concentración en valores altos (75-85). Indica que la mayoría de conductores son seguros.

2. **Efficiency Score**: Distribución más uniforme con ligero sesgo hacia valores medios-altos (65-75). Algunos outliers en el extremo bajo.

3. **Compliance Score**: Distribución concentrada en valores altos (75-85), con pocos conductores por debajo de 70. Excelente adherencia general a normativas.

4. **Driver Score Base**: Distribución normal centrada en 75-80, reflejando el promedio ponderado de las otras métricas.

#### 1.2.3 Matriz de Correlación de Conductores

**Correlaciones Significativas:**

- **Safety Score ↔ Efficiency Score**: Correlación positiva moderada (~0.45)
  - Conductores seguros tienden a ser más eficientes
- **Safety Score ↔ Driver Score Base**: Correlación fuerte (~0.75)
  - La seguridad es un componente importante del score general
- **Efficiency Score ↔ Driver Score Base**: Correlación fuerte (~0.70)
  - La eficiencia también pesa significativamente en el score final
- **Compliance Score ↔ Driver Score Base**: Correlación moderada (~0.50)

  - El cumplimiento contribuye al score pero con menor peso

- **Driven KM ↔ Otros scores**: Correlaciones débiles
  - La experiencia (km recorridos) no garantiza mejores scores

**Conclusión:** Los tres componentes principales (Safety, Efficiency, Compliance) contribuyen de manera equilibrada al Driver Score Base, con Safety y Efficiency teniendo mayor peso.

---

### 1.3 Análisis de Rutas

#### 1.3.1 Estadísticas Descriptivas de Rutas

**Métricas Clave:**

| Métrica                | Media  | Desv. Std | Min   | Max      |
| ---------------------- | ------ | --------- | ----- | -------- |
| Total Distance (km)    | 487.69 | 230.58    | 79.75 | 1,136.44 |
| Avg Speed (km/h)       | 69.46  | 12.66     | 34.76 | 96.26    |
| Navigation Steps       | 24.79  | 18.44     | 5     | 96       |
| Avg Compliance Index   | 1.37   | 0.12      | 1.06  | 1.65     |
| Time Variability (min) | 30.52  | 7.83      | 9.53  | 51.06    |
| Breakdown Rate         | 0.109  | 0.018     | 0.067 | 0.155    |
| Fuel Efficiency (L/km) | 0.347  | 0.056     | 0.220 | 0.509    |

**Análisis:**

1. **Total Distance**: Alta variabilidad (CV = 47%), indicando rutas muy diversas desde urbanas cortas hasta interurbanas largas.

2. **Avg Speed**: Media de 69.46 km/h sugiere mix de rutas urbanas y carretera. Desviación estándar moderada.

3. **Navigation Steps**: Altísima variabilidad (CV = 74%), diferenciando claramente rutas simples de complejas.

4. **Avg Compliance Index**: Valores > 1 indican que las rutas requieren más tiempo del estándar, posiblemente por tráfico o complejidad.

5. **Time Variability**: Media de 30.52 minutos indica incertidumbre significativa en tiempos de entrega.

6. **Breakdown Rate**: ~11% promedio, relativamente alto, sugiriendo necesidad de mantenimiento preventivo.

7. **Fuel Efficiency**: 0.347 L/km es razonable para vehículos de carga, con variación según tipo de ruta.

#### 1.3.2 Distribución de Métricas de Rutas

**Observaciones de los Histogramas:**

1. **Total Distance**: Distribución bimodal con picos en ~300km y ~600km, sugiriendo dos tipos principales de rutas.

2. **Avg Speed**: Distribución aproximadamente normal centrada en 65-70 km/h.

3. **Navigation Steps**: Distribución sesgada a la derecha, mayoría de rutas con <30 pasos, pero algunas muy complejas (>70).

4. **Avg Compliance Index**: Distribución normal estrecha, mayoría entre 1.2-1.5.

5. **Time Variability**: Distribución normal, mayoría entre 25-35 minutos.

6. **Breakdown Rate**: Distribución uniforme entre 0.08-0.13.

7. **Fuel Efficiency**: Distribución normal centrada en 0.34 L/km.

#### 1.3.3 Matriz de Correlación de Rutas

**Correlaciones Significativas:**

- **Total Distance ↔ Navigation Steps**: Correlación positiva fuerte (~0.65)
  - Rutas más largas tienden a ser más complejas
- **Avg Speed ↔ Navigation Steps**: Correlación negativa moderada (~-0.45)
  - Rutas complejas tienen velocidades más bajas (más urbanas)
- **Total Distance ↔ Fuel Efficiency**: Correlación positiva (~0.35)
  - Rutas más largas consumen más combustible por km (posiblemente por carga)
- **Time Variability ↔ Navigation Steps**: Correlación positiva (~0.40)
  - Rutas complejas tienen mayor incertidumbre en tiempos

**Conclusión:** Las rutas se pueden caracterizar principalmente por dos ejes: longitud/complejidad y velocidad promedio, que están inversamente relacionados.

---

## 2. CLUSTERING DE CONDUCTORES

### 2.1 Selección del Número Óptimo de Clusters

**Método del Codo:**

- La inercia disminuye rápidamente hasta k=2
- Después de k=2, la disminución es más gradual
- Sugiere que k=2 o k=3 son opciones razonables

**Silhouette Score:**

- **k=2: 0.254** (ÓPTIMO)
- k=3: 0.220
- k=4: 0.195
- Scores decrecientes después de k=2

**Decisión:** k=2 clusters para conductores basado en el mejor Silhouette Score.

### 2.2 Perfiles de Clusters de Conductores

#### Cluster 0: "Conductores Premium" (206 conductores - 58.9%)

| Métrica                | Valor     |
| ---------------------- | --------- |
| Safety Score           | 82.44     |
| Efficiency Score       | 74.52     |
| Compliance Score       | 79.94     |
| Driving Aggressiveness | 20.16     |
| Energy Efficiency      | 89.11     |
| Driven KM              | 15,642.94 |
| Driver Score Base      | 79.04     |

**Características:**

- Conductores de alta calidad en todas las métricas
- Baja agresividad al conducir (20.16)
- Alta eficiencia energética (89.11)
- Scores superiores al promedio general
- Representan la mayoría de la flota

#### Cluster 1: "Conductores Estándar" (144 conductores - 41.1%)

| Métrica                | Valor     |
| ---------------------- | --------- |
| Safety Score           | 71.83     |
| Efficiency Score       | 65.74     |
| Compliance Score       | 79.60     |
| Driving Aggressiveness | 45.88     |
| Energy Efficiency      | 69.81     |
| Driven KM              | 14,136.90 |
| Driver Score Base      | 71.64     |

**Características:**

- Conductores con desempeño aceptable pero mejorable
- Alta agresividad al conducir (45.88) - más del doble que Cluster 0
- Menor eficiencia energética (69.81)
- Scores por debajo del promedio general
- Menor experiencia (menos km recorridos)

### 2.3 Diferencias Clave Entre Clusters

**Diferencias Absolutas:**

- Safety: 10.61 puntos (14.8% diferencia)
- Efficiency: 8.78 puntos (13.4% diferencia)
- Aggressiveness: 25.72 puntos (127.6% diferencia) ⚠️
- Energy Efficiency: 19.30 puntos (27.6% diferencia)
- Driver Score: 7.40 puntos (10.3% diferencia)

**Análisis:**
La **Driving Aggressiveness** es el factor más discriminante entre clusters, con una diferencia de más del 127%. Esto sugiere que el estilo de conducción es el principal diferenciador entre conductores premium y estándar.

### 2.4 Visualizaciones de Clusters de Conductores

#### PCA (Principal Component Analysis):

- PC1 explica ~45% de la varianza
- PC2 explica ~25% de la varianza
- Total: ~70% de varianza explicada
- Separación clara entre clusters, con alguna superposición en la zona intermedia

#### t-SNE:

- Muestra separación más clara entre clusters
- Algunos conductores del Cluster 1 están cerca del Cluster 0, sugiriendo potencial de mejora
- Visualización confirma la validez de la segmentación

---

## 3. CLUSTERING DE RUTAS

### 3.1 Selección del Número Óptimo de Clusters

**Método del Codo:**

- Disminución pronunciada hasta k=2
- Cambio gradual después de k=2

**Silhouette Score:**

- **k=2: 0.247** (ÓPTIMO)
- k=3: 0.215
- k=4: 0.198

**Decisión:** k=2 clusters para rutas.

### 3.2 Perfiles de Clusters de Rutas

#### Cluster 0: "Rutas Rápidas y Simples" (70 rutas - 46.7%)

| Métrica              | Valor      |
| -------------------- | ---------- |
| Total Distance       | 444.95 km  |
| Avg Speed            | 79.64 km/h |
| Navigation Steps     | 15.19      |
| Avg Compliance Index | 1.31       |
| Time Variability     | 25.43 min  |
| Breakdown Rate       | 0.10       |
| Fuel Efficiency      | 0.32 L/km  |

**Características:**

- Rutas más cortas y directas
- Alta velocidad promedio (carretera/interurbanas)
- Pocas paradas/giros (navegación simple)
- Menor variabilidad de tiempo (más predecibles)
- Mejor eficiencia de combustible
- Menor tasa de averías

#### Cluster 1: "Rutas Complejas y Lentas" (80 rutas - 53.3%)

| Métrica              | Valor      |
| -------------------- | ---------- |
| Total Distance       | 525.08 km  |
| Avg Speed            | 60.56 km/h |
| Navigation Steps     | 33.20      |
| Avg Compliance Index | 1.42       |
| Time Variability     | 34.98 min  |
| Breakdown Rate       | 0.12       |
| Fuel Efficiency      | 0.37 L/km  |

**Características:**

- Rutas más largas y complejas
- Velocidad más baja (urbanas/tráfico)
- Muchas paradas/giros (navegación compleja)
- Mayor variabilidad de tiempo (menos predecibles)
- Peor eficiencia de combustible
- Mayor tasa de averías

### 3.3 Diferencias Clave Entre Clusters de Rutas

**Diferencias Absolutas:**

- Distance: 80.13 km (18.0% diferencia)
- Speed: 19.08 km/h (31.5% diferencia) ⚠️
- Navigation Steps: 18.01 pasos (118.6% diferencia) ⚠️
- Time Variability: 9.55 min (37.6% diferencia)
- Fuel Efficiency: 0.05 L/km (15.6% diferencia)

**Análisis:**
Los **Navigation Steps** y la **Avg Speed** son los factores más discriminantes. Las rutas se dividen claramente entre:

1. Rutas interurbanas rápidas y directas
2. Rutas urbanas/complejas lentas con muchas paradas

### 3.4 Visualizaciones de Clusters de Rutas

#### PCA:

- PC1 explica ~40% de la varianza
- PC2 explica ~28% de la varianza
- Total: ~68% de varianza explicada
- Separación moderada entre clusters

#### t-SNE:

- Muestra dos grupos relativamente distintos
- Algunas rutas en zona de transición
- Confirma la validez de la segmentación binaria

---

## 4. CONCLUSIONES GENERALES

### 4.1 Sobre los Conductores

1. **Segmentación Clara**: Los conductores se dividen naturalmente en dos grupos con características distintivas.

2. **Factor Clave**: La **agresividad al conducir** es el principal diferenciador, con impacto directo en seguridad y eficiencia energética.

3. **Oportunidad de Mejora**: El 41% de conductores (Cluster 1) tienen potencial de mejora significativo, especialmente en:

   - Reducir agresividad al conducir
   - Mejorar eficiencia energética
   - Aumentar scores de seguridad

4. **Distribución Favorable**: El 59% de conductores son "Premium", lo cual es positivo para la calidad del servicio.

### 4.2 Sobre las Rutas

1. **Dos Tipos Principales**: Las rutas se dividen claramente entre:

   - Interurbanas rápidas y simples (47%)
   - Urbanas complejas y lentas (53%)

2. **Complejidad vs Velocidad**: Existe una relación inversa clara entre complejidad (navigation steps) y velocidad promedio.

3. **Predictibilidad**: Las rutas simples son más predecibles (menor time variability), lo cual facilita la planificación.

4. **Eficiencia Operativa**: Las rutas complejas tienen:
   - Mayor consumo de combustible por km
   - Mayor tasa de averías
   - Mayor incertidumbre en tiempos de entrega

### 4.3 Implicaciones para el Matching

1. **Matching Óptimo**:

   - Conductores Premium (Cluster 0) → Rutas Complejas (Cluster 1)
     - Aprovecha sus habilidades superiores en rutas difíciles
   - Conductores Estándar (Cluster 1) → Rutas Simples (Cluster 0)
     - Minimiza riesgos en rutas más predecibles

2. **Desarrollo de Conductores**:

   - Entrenar conductores del Cluster 1 para reducir agresividad
   - Programas de mejora de eficiencia energética
   - Asignar rutas progresivamente más complejas según mejora

3. **Planificación de Rutas**:
   - Priorizar rutas simples cuando sea posible
   - Asignar tiempo extra para rutas complejas
   - Considerar mantenimiento preventivo más frecuente para rutas complejas

### 4.4 Métricas de Éxito del Clustering

**Conductores:**

- Silhouette Score: 0.254 (aceptable)
- Varianza explicada (PCA): 70%
- Separación clara en visualizaciones

**Rutas:**

- Silhouette Score: 0.247 (aceptable)
- Varianza explicada (PCA): 68%
- Separación moderada en visualizaciones

**Evaluación**: Los clusterings son válidos y útiles para el sistema de matching, aunque hay espacio para refinamiento con más features o métodos alternativos.

---

## 5. RECOMENDACIONES

### 5.1 Recomendaciones Operativas

1. **Implementar sistema de matching basado en clusters**

   - Priorizar asignaciones cruzadas (Premium → Complejo, Estándar → Simple)
   - Monitorear KPIs de satisfacción y eficiencia

2. **Programa de desarrollo de conductores**

   - Identificar conductores del Cluster 1 con potencial
   - Entrenamientos específicos en conducción eficiente
   - Incentivos para mejorar scores

3. **Optimización de rutas**
   - Analizar posibilidad de simplificar rutas del Cluster 1
   - Considerar horarios alternativos para evitar tráfico
   - Implementar mantenimiento preventivo diferenciado
