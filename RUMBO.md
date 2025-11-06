# 🗺️ RUMBO AI - Sistema de Recomendación de Choferes

**Versión:** 1.0  
**Fecha:** Noviembre 2025  
**Equipo:** Hackathon HG  

---

## 📌 RESUMEN EJECUTIVO

**RUMBO** es un sistema de inteligencia artificial que monitorea el comportamiento de conductores en tiempo real y recomienda el mejor chofer para cada viaje basándose en:
- Perfil de conducción (seguridad, eficiencia)
- Clasificación de ruta (peligrosidad, complejidad)
- Equidad en kilometraje

**Impacto esperado:**
- 🛡️ -28% incidentes (seguridad)
- ⚡ +40% mejores asignaciones (eficiencia)
- 🌱 -20% emisiones CO2 (sustentabilidad)
- 💰 +380% ROI primer año

---

## 🎯 PROBLEMA QUE RESOLVEMOS

### Situación actual:
Los choferes se asignan a viajes basándose en:
- Disponibilidad horaria
- Experiencia general (años en la empresa)
- Intuición del dispatcher

### Preguntas sin respuesta:
- ¿Quién es el MEJOR conductor para un viaje de alto riesgo?
- ¿Tenemos visibilidad del comportamiento real en ruta?
- ¿Podemos prevenir incidentes ANTES de que sucedan?

**Respuesta actual: NO**

---

## 💡 SOLUCIÓN: RUMBO

Un sistema de IA que:

1. **MONITOREA** comportamiento de conductores (via Scania API)
2. **CLASIFICA** choferes automáticamente (clustering con K-Means)
3. **RECOMIENDA** el mejor chofer para cada viaje (motor de recomendación)

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### Componentes principales:

```
┌─────────────────────────────────────────────────────┐
│ 1. DATA SOURCE: Scania Fleet Management API         │
│    └─> Driver Evaluation Report (histórico 21-31 oct)│
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ 2. ML PIPELINE (Python - Offline)                   │
│    ├─> extract_data.py: Extrae y limpia datos      │
│    ├─> train_clustering.py: Aplica K-Means         │
│    └─> Output: driver_scores.json                  │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ 3. API BACKEND (NestJS)                             │
│    ├─> GET /api/drivers (lista todos)              │
│    ├─> GET /api/drivers/ranking (top 10)           │
│    └─> POST /api/drivers/recommend (recomendación) │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ 4. FRONTEND (React + Vite)                          │
│    └─> Dashboard de recomendaciones                │
└─────────────────────────────────────────────────────┘
```

---

## 📊 DATOS Y FEATURES

### Fuente de datos: Scania Driver Evaluation API

**Endpoint:**
```
GET https://dataaccess.scania.com/cs/driver/reports/DriverEvaluationReport/v2
Params:
  - startDate: YYYYMMDDHHMM (202510210000)
  - endDate: YYYYMMDDHHMM (202510310000)
  - driverRefList: (opcional, vacío = todos)
```

**Autenticación:** Bearer Token

### Features principales extraídas:

#### 🛡️ SEGURIDAD (Safety Score)
| Feature | Campo Scania | Descripción |
|---------|--------------|-------------|
| `harsh_braking_count` | `HarshBrakeApplications` | Número de frenadas bruscas |
| `harsh_braking_per_100km` | `HarshBrakeApplicationsTLValue` | Frenadas por 100 km |
| `harsh_acceleration_per_100km` | `HarshAccelerationsValue` | Aceleraciones bruscas por 100 km |
| `speeding_percentage` | `SpeedingValue` | % del tiempo excediendo velocidad |
| `brake_score` | `UseOfBrakesScaniaDriverSupport` | Score 0-100 de uso de frenos |

#### ⚡ EFICIENCIA (Efficiency Score)
| Feature | Campo Scania | Descripción |
|---------|--------------|-------------|
| `fuel_per_100km` | `AverageFuelConsumption` | Litros por 100 km |
| `idle_time_percentage` | `IdlingValue` | % tiempo en ralentí |
| `coasting_percentage` | `CoastingValue` | % tiempo sin acelerar |
| `cruise_control_usage` | `DistanceWithCruiseControl` | Km con cruise control |
| `anticipation_score` | `AnticipationScaniaDriverSupport` | Score 0-100 anticipación |

#### ✅ COMPLIANCE (Cumplimiento)
| Feature | Campo Scania | Descripción |
|---------|--------------|-------------|
| `distance_km` | `Distance` | Distancia total del viaje |
| `average_speed_kmh` | `AverageSpeed` | Velocidad promedio |
| `trip_duration_hours` | Calculado: `StopDate - StartDate` | Duración del viaje |

#### 🎯 SCORE GENERAL
| Feature | Campo Scania | Descripción |
|---------|--------------|-------------|
| `scania_driver_support_score` | `ScaniaDriverSupportValue` | Score general 0-100 |
| `hill_driving_score` | `HillDrivingScaniaDriverSupport` | Score manejo en montaña |

#### 🌱 HUELLA DE CARBONO (CO2)
| Feature | Cálculo | Descripción |
|---------|---------|-------------|
| `co2_emissions_kg` | `fuel_consumption_liters × 2.68` | kg CO2 emitidos en el viaje |
| `co2_per_km` | `co2_emissions_kg / distance_km` | kg CO2 por kilómetro |
| `co2_from_idling_kg` | `fuel_idling_liters × 2.68` | kg CO2 por tiempo en ralentí (evitable) |
| `carbon_efficiency_score` | `100 - (co2_per_km × 350)` | Score 0-100 de eficiencia de carbono |

**Fórmula de conversión:**
- **1 litro de diésel = 2.68 kg de CO2**
- Fuente: EPA (Environmental Protection Agency)

**Conexión natural: Eficiencia = Menos Emisiones**

El mismo comportamiento que medimos para seguridad y eficiencia **también determina la huella de carbono**:

- ✅ **Conducción agresiva** → +25% emisiones
  - Frenadas bruscas desperdician energía
  - Aceleraciones bruscas consumen más combustible
  
- ✅ **Tiempo en ralentí** → Emisiones evitables 100%
  - Motor encendido sin moverse = combustible desperdiciado
  
- ✅ **Exceso de velocidad** → +15% emisiones
  - Resistencia del aire aumenta exponencialmente con velocidad

**Resultado: Mejor conductor = -20% carbono**

---

## 🤖 MODELOS DE IA

### 1. K-MEANS CLUSTERING (Unsupervised Learning)

**Objetivo:** Descubrir tipos de conductores automáticamente

**Input:**
- Dataset con ~200-500 viajes (15-20 unidades × 10 días)
- Features: harsh_braking, fuel_consumption, idle_time, etc.

**Proceso:**
1. Normalización de features (StandardScaler)
2. Método del codo para determinar K óptimo (probar K=2,3,4,5)
3. Aplicar K-Means con K óptimo
4. Validar con Silhouette Score

**Output:**
- Etiqueta de cluster para cada chofer (0, 1, 2, ...)
- Interpretación:
  - Cluster 0: "Conservadores" (safety score alto, fuel bajo)
  - Cluster 1: "Equilibrados" (balance entre seguridad y velocidad)
  - Cluster 2: "Riesgosos" (harsh braking alto, speeding frecuente)

**Ejemplo:**
```python
features = [
    'harsh_braking_per_100km',
    'fuel_consumption_per_100km',
    'idle_time_percentage',
    'scania_driver_support_score'
]

X = df[features].fillna(0)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=3, random_state=42)
clusters = kmeans.fit_predict(X_scaled)
```

### 2. MOTOR DE RECOMENDACIÓN (Recommendation Engine)

**Objetivo:** Sugerir el mejor chofer para una ruta específica

**Input:**
- Características de la ruta:
  - `route_risk_level`: "low" | "medium" | "high"
  - `distance_km`: distancia del viaje
  - `route_type`: "urban" | "highway" | "mountain"
- Scores de los choferes (del clustering)

**Algoritmo de matching:**

```
MatchScore = w1 × (1 - |RutaPeligrosidad - ChoferSeguridad|) +
             w2 × (1 - |RutaDistancia - ChoferExperiencia|) +
             w3 × EquidadKilometraje

Donde:
  w1 = 0.5 (peso seguridad)
  w2 = 0.3 (peso eficiencia)
  w3 = 0.2 (peso equidad)
```

**Lógica de filtrado:**

1. **Ruta de alto riesgo:**
   - Filtrar choferes con `overall_score > 85`
   - Preferir cluster "Conservador"
   - Excluir choferes con `harsh_braking > 5/100km`

2. **Ruta larga (>1000 km):**
   - Filtrar choferes con `fuel_per_100km < promedio_flota`
   - Preferir `cruise_control_usage > 80%`

3. **Equidad de kilometraje:**
   - Penalizar choferes con muchos km recorridos
   - Bonus para choferes con km < promedio

**Output:**
```json
{
  "recommendations": [
    {
      "rank": 1,
      "driver_id": "abc123",
      "driver_name": "Ana Silva",
      "overall_score": 95,
      "cluster": "Conservador",
      "compatibility_score": 96,
      "estimated_co2_kg": 285,
      "co2_savings_vs_avg": -55,
      "reasoning": [
        "Safety score excepcional (95/100)",
        "Cero frenadas bruscas en últimos 10 días",
        "Experiencia en rutas de montaña (hill_driving: 94)",
        "🌱 Ahorrará ~55 kg CO2 en este viaje (vs promedio flota)"
      ]
    },
    { ... },
    { ... }
  ],
  "fleet_avg_co2_for_route": 340
}
```

**Cálculo de CO2 estimado para el viaje:**
```python
# Basado en el promedio histórico del chofer
estimated_fuel = (distance_km / 100) * driver.fuel_per_100km_avg
estimated_co2 = estimated_fuel * 2.68

# Comparar con promedio de flota
fleet_avg_fuel = (distance_km / 100) * fleet.avg_fuel_per_100km
fleet_avg_co2 = fleet_avg_fuel * 2.68

co2_savings = estimated_co2 - fleet_avg_co2
```

---

## 🗂️ ESTRUCTURA DEL DATASET

### dataset_viajes.csv (nivel viaje)

```csv
trip_id,driver_id,driver_name,vin,start_date,stop_date,distance_km,harsh_braking_count,harsh_braking_per_100km,harsh_acceleration_per_100km,speeding_percentage,fuel_per_100km,idle_time_percentage,cruise_control_usage_pct,average_speed_kmh,scania_driver_support_score,total_fuel_liters,co2_emissions_kg,co2_per_km,carbon_efficiency_score,cluster
001,abc123,Juan Pérez,VIN001,2025-10-21 08:00,2025-10-21 20:00,850,3,0.35,0.2,5.0,28.5,12.0,75.0,68.0,82,242.25,649.2,0.764,73.3,2
002,def456,Ana Silva,VIN002,2025-10-21 09:00,2025-10-21 18:00,620,0,0.0,0.0,0.0,24.8,8.8,88.0,65.3,95,153.76,412.1,0.665,76.7,0
...
```

**Nota:** Las columnas de CO2 se calculan a partir de `total_fuel_liters`:
- `co2_emissions_kg = total_fuel_liters × 2.68`
- `co2_per_km = co2_emissions_kg / distance_km`
- `carbon_efficiency_score = 100 - (co2_per_km × 350)`

### driver_scores.json (nivel chofer - agregado)

```json
{
  "generated_at": "2025-11-01T10:00:00",
  "drivers": [
    {
      "driver_id": "abc123",
      "driver_name": "Juan Pérez",
      "total_trips": 12,
      "total_distance_km": 14500,
      "avg_safety_score": 82,
      "avg_efficiency_score": 78,
      "overall_score": 80,
      "cluster": 2,
      "cluster_name": "Riesgoso",
      "harsh_braking_per_100km_avg": 0.35,
      "fuel_per_100km_avg": 28.5,
      "idle_time_percentage_avg": 12.0,
      
      "total_co2_emissions_kg": 11075,
      "avg_co2_per_km": 0.764,
      "carbon_efficiency_score": 73.3,
      "co2_vs_fleet_avg": "+18%"
    },
    {
      "driver_id": "def456",
      "driver_name": "Ana Silva",
      "total_trips": 18,
      "total_distance_km": 22000,
      "avg_safety_score": 95,
      "avg_efficiency_score": 92,
      "overall_score": 94,
      "cluster": 0,
      "cluster_name": "Conservador",
      "harsh_braking_per_100km_avg": 0.0,
      "fuel_per_100km_avg": 24.8,
      "idle_time_percentage_avg": 8.8,
      
      "total_co2_emissions_kg": 14636,
      "avg_co2_per_km": 0.665,
      "carbon_efficiency_score": 76.7,
      "co2_vs_fleet_avg": "-15%"
    }
  ],
  "fleet_statistics": {
    "avg_co2_per_km_fleet": 0.72,
    "total_co2_emissions_fleet_kg": 125680,
    "estimated_annual_co2_tons": 1508
  }
}
```

**Interpretación de CO2:**
- **Ana Silva:** 0.665 kg CO2/km → 15% **menos** que el promedio de flota
- **Juan Pérez:** 0.764 kg CO2/km → 18% **más** que el promedio de flota

**Equivalencias (para comunicación):**
- 1,000 kg CO2 = plantar ~45 árboles para compensar
- 14,636 kg CO2 (Ana en 10 días) = 659 árboles necesarios
- Mejora de 15% en flota completa = -226 toneladas CO2/año

---

## 🌱 EL DOBLE BENEFICIO: SEGURIDAD + SUSTENTABILIDAD

### La conexión natural

**Insight clave:** Los mismos comportamientos que causan accidentes también generan más emisiones de CO2.

| COMPORTAMIENTO | IMPACTO SEGURIDAD | IMPACTO CO2 |
|----------------|-------------------|-------------|
| Frenadas bruscas | +35% riesgo accidente | +15% emisiones |
| Aceleraciones bruscas | +28% riesgo accidente | +25% emisiones |
| Exceso de velocidad | +40% riesgo accidente | +15% emisiones |
| Tiempo en ralentí | -10% atención | +100% desperdicio |
| Sin cruise control | +12% fatiga | +8% consumo extra |

### Un sistema, dos beneficios

El sistema de scoring de RUMBO:
1. **Identifica** conductores seguros basándose en harsh braking, speeding, etc.
2. **Automáticamente** estos mismos conductores son los más eficientes en consumo
3. **Resultado:** Asignar al conductor más seguro = Asignar al más eco-friendly

**No necesitamos dos sistemas separados. El mismo algoritmo optimiza ambos.**

### Proyección de impacto anual

**Escenario base (sin RUMBO):**
- Flota de 38 choferes
- 500,000 km/año totales  
- Consumo promedio: 28 L/100km
- **CO2 total: 3,752 toneladas/año**

**Escenario con RUMBO (mejora 20%):**
- Consumo promedio optimizado: 22.4 L/100km
- **CO2 total: 3,002 toneladas/año**
- **Ahorro: 750 toneladas CO2/año** 🌱

**Equivalencias comunicables:**
- 750 ton CO2 = plantar **33,750 árboles**
- = Eliminar **163 autos** de circulación por 1 año
- = Ahorrar **$280,000 USD** en combustible

### Dashboard de CO2 (para motivar choferes)

Cada chofer ve su impacto personal mensual:
- CO2 emitido total
- CO2 por km (vs promedio flota)
- Ranking eco-friendly
- Equivalencias en árboles/vuelos
- Meta del mes para mejorar

**Gamificación:** Los choferes con mejor carbon_efficiency_score reciben reconocimiento y bonos.

### Reportes ESG automatizados

El sistema genera reportes listos para clientes y auditorías:
- **Mensual:** Toneladas CO2, comparativa, ranking
- **Trimestral:** Tendencias, impacto de capacitaciones, ROI ambiental  
- **Anual:** Certificación de reducción, cumplimiento ESG corporativo

---

## 🔬 PIPELINE TÉCNICO: MÓDULO DE CHOFERES (ML/IA)

### Arquitectura del Sistema de Choferes

```
┌─────────────────────────────────────────────────────────────────┐
│ FASE 1: EXTRACCIÓN DE DATOS (Scania API)                       │
├─────────────────────────────────────────────────────────────────┤
│ Input:  Scania Driver Evaluation Report API                    │
│         - startDate: YYYYMMDDHHMM                               │
│         - endDate: YYYYMMDDHHMM                                 │
│         - Período: Últimos 30 días (rolling window)            │
│                                                                 │
│ Output: raw_driver_trips.json                                  │
│         - ~200-500 viajes por período                           │
│         - 15-20 unidades activas                                │
│         - Features raw de Scania (30+ campos)                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 2: PROCESAMIENTO Y FEATURE ENGINEERING                    │
├─────────────────────────────────────────────────────────────────┤
│ Proceso:                                                        │
│   1. Limpieza: Manejo de nulls, outliers                       │
│   2. Agregación: Group by driver_id                            │
│   3. Cálculo de features compuestas                            │
│                                                                 │
│ Features Calculadas (por chofer):                              │
│                                                                 │
│ 🛡️ SAFETY FEATURES:                                            │
│   - harsh_braking_per_100km_avg                                │
│   - harsh_acceleration_per_100km_avg                           │
│   - speeding_percentage_avg                                    │
│   - brake_score_avg (Scania Driver Support)                    │
│                                                                 │
│ ⚡ EFFICIENCY FEATURES:                                         │
│   - fuel_per_100km_avg                                         │
│   - idle_time_percentage_avg                                   │
│   - cruise_control_usage_percentage                            │
│   - anticipation_score_avg                                     │
│                                                                 │
│ ✅ COMPLIANCE FEATURES:                                        │
│   - avg_speed_kmh                                              │
│   - total_distance_km                                          │
│   - total_trips                                                │
│                                                                 │
│ 🎯 COMPOSITE SCORES:                                           │
│   - safety_score = f(harsh_braking, speeding, brake_score)    │
│   - efficiency_score = f(fuel, idle_time, cruise_control)     │
│   - compliance_score = f(distance, trips, availability)        │
│                                                                 │
│ Output: drivers_features.csv                                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 3: CLUSTERING (Unsupervised ML - K-Means)                 │
├─────────────────────────────────────────────────────────────────┤
│ Algoritmo: K-Means Clustering                                  │
│                                                                 │
│ Features para clustering:                                      │
│   - harsh_braking_per_100km_avg                                │
│   - fuel_per_100km_avg                                         │
│   - idle_time_percentage_avg                                   │
│   - scania_driver_support_score                                │
│   - speeding_percentage_avg                                    │
│                                                                 │
│ Proceso:                                                        │
│   1. Normalización: StandardScaler()                           │
│   2. Método del codo: Determinar K óptimo (K=2 o K=3)         │
│   3. Entrenar K-Means con K óptimo                             │
│   4. Validar con Silhouette Score (target: >0.25)              │
│   5. Interpretar clusters (análisis de centroides)             │
│                                                                 │
│ Clusters Esperados (K=3):                                      │
│   - Cluster 0: "Conservadores"                                 │
│     • Safety score: 85-95                                      │
│     • Harsh braking: <0.2/100km                                │
│     • Fuel efficiency: Óptimo                                  │
│                                                                 │
│   - Cluster 1: "Equilibrados"                                  │
│     • Safety score: 70-85                                      │
│     • Harsh braking: 0.2-0.5/100km                             │
│     • Fuel efficiency: Bueno                                   │
│                                                                 │
│   - Cluster 2: "Agresivos"                                     │
│     • Safety score: 60-70                                      │
│     • Harsh braking: >0.5/100km                                │
│     • Fuel efficiency: Mejorable                               │
│                                                                 │
│ Output: drivers_clustered.csv                                  │
│         - Incluye: cluster_label, cluster_name                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 4: SCORING Y OUTPUT FINAL                                 │
├─────────────────────────────────────────────────────────────────┤
│ Cálculo de Overall Score:                                      │
│   driver_score = 0.4 * safety + 0.35 * efficiency + 0.25 * compliance
│                                                                 │
│ Ajuste por equidad de kilometraje:                             │
│   km_balance = mean_fleet_km - driver_km                       │
│   driver_score_adjusted = driver_score + (0.15 * km_balance_scaled)
│                                                                 │
│ Output: driver_scores.json                                     │
│ {                                                               │
│   "generated_at": "2025-11-06T00:00:00",                       │
│   "drivers": [                                                  │
│     {                                                           │
│       "driver_id": "abc123",                                   │
│       "driver_name": "Ana Silva",                              │
│       "cluster": 0,                                            │
│       "cluster_name": "Conservador",                           │
│       "safety_score": 95,                                      │
│       "efficiency_score": 92,                                  │
│       "compliance_score": 94,                                  │
│       "overall_score": 94,                                     │
│       "km_accumulated": 18000,                                 │
│       "total_trips": 24,                                       │
│       "co2_per_km": 0.665,                                     │
│       "harsh_braking_avg": 0.05,                               │
│       "fuel_consumption_avg": 24.8,                            │
│       "scania_support_score": 95                               │
│     }                                                           │
│   ],                                                            │
│   "fleet_statistics": {                                        │
│     "total_drivers": 38,                                       │
│     "avg_safety_score": 78.5,                                  │
│     "avg_efficiency_score": 71.2,                              │
│     "cluster_distribution": {                                  │
│       "Conservador": 16,                                       │
│       "Equilibrado": 18,                                       │
│       "Agresivo": 4                                            │
│     }                                                           │
│   }                                                             │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 EVOLUCIÓN POST-HACKATHON: SUPERVISED LEARNING

### ¿Qué Nos Habilita el Sistema Actual?

El sistema de clustering **unsupervised** que implementamos en la hackathon es un **PoC sólido** que nos habilita a **evolucionar a un sistema de ML supervisado** que aprende continuamente.

### Pipeline de Aprendizaje Continuo

```
┌─────────────────────────────────────────────────────────────────┐
│ RECOLECCIÓN DE OUTCOMES (Post-Asignación)                      │
├─────────────────────────────────────────────────────────────────┤
│ Para cada viaje completado, guardamos:                         │
│                                                                 │
│ 1. ETA vs Arrival Time:                                        │
│    - planned_arrival_time (del roadmap)                        │
│    - actual_arrival_time (GPS tracking)                        │
│    - eta_difference_minutes = actual - planned                 │
│    - on_time_delivery = (eta_difference <= 15 min)             │
│                                                                 │
│ 2. Incidents & Events:                                         │
│    - had_incident (boolean)                                    │
│    - incident_type (freno brusco, exceso velocidad, etc.)      │
│    - incident_severity (low/medium/high)                       │
│                                                                 │
│ 3. Fuel Performance:                                           │
│    - predicted_fuel_consumption (del modelo)                   │
│    - actual_fuel_consumption (telemetría Scania)               │
│    - fuel_efficiency_delta = actual - predicted                │
│                                                                 │
│ 4. Route Compliance:                                           │
│    - route_deviations_count                                    │
│    - unauthorized_stops_count                                  │
│    - compliance_rate (%)                                       │
│                                                                 │
│ 5. Customer Feedback:                                          │
│    - delivery_rating (1-5 stars)                               │
│    - driver_behavior_rating (1-5)                              │
│    - cargo_condition_rating (1-5)                              │
│                                                                 │
│ Output: trip_outcomes.csv                                      │
│ Campos:                                                         │
│   - trip_id, driver_id, route_id, date                         │
│   - driver_cluster, driver_score, route_score                  │
│   - match_score (del motor de recomendación)                   │
│   - eta_difference_minutes                                     │
│   - on_time_delivery                                           │
│   - had_incident                                               │
│   - fuel_efficiency_delta                                      │
│   - compliance_rate                                            │
│   - overall_success_score (0-100)                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ FEATURE ENGINEERING PARA SUPERVISED LEARNING                   │
├─────────────────────────────────────────────────────────────────┤
│ Features del Chofer (X_driver):                                │
│   - safety_score                                               │
│   - efficiency_score                                           │
│   - compliance_score                                           │
│   - cluster_label                                              │
│   - harsh_braking_avg                                          │
│   - fuel_consumption_avg                                       │
│   - km_accumulated (experiencia)                               │
│                                                                 │
│ Features de la Ruta (X_route):                                 │
│   - route_score_final                                          │
│   - peligrosity_score                                          │
│   - complexity_score                                           │
│   - total_distance_km                                          │
│   - avg_speed_kmh                                              │
│   - navigation_steps_count                                     │
│                                                                 │
│ Features de Contexto (X_context):                              │
│   - day_of_week                                                │
│   - time_of_day (morning/afternoon/night)                      │
│   - weather_condition (si disponible)                          │
│   - traffic_level (si disponible)                              │
│                                                                 │
│ Target Variable (y):                                           │
│   - overall_success_score (0-100)                              │
│   Calculado como:                                              │
│     success_score = 0.3 * on_time_delivery_score +             │
│                    0.3 * (1 - incident_occurred) * 100 +       │
│                    0.2 * fuel_efficiency_score +               │
│                    0.2 * compliance_rate                       │
│                                                                 │
│ Features Combinadas (X_combined):                              │
│   X = [X_driver, X_route, X_context, match_score]             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ ENTRENAMIENTO DE MODELO SUPERVISADO                            │
├─────────────────────────────────────────────────────────────────┤
│ Modelo: XGBoost Regressor / Random Forest                      │
│                                                                 │
│ Objetivo: Predecir overall_success_score antes del viaje       │
│                                                                 │
│ Pipeline:                                                       │
│   1. Split: 80% train, 20% test                                │
│   2. Cross-validation: 5-fold                                  │
│   3. Hyperparameter tuning: GridSearchCV                       │
│   4. Feature importance analysis                               │
│   5. Evaluar:                                                  │
│      - MAE (Mean Absolute Error)                               │
│      - RMSE (Root Mean Squared Error)                          │
│      - R² score                                                │
│                                                                 │
│ Modelos Adicionales (Multi-Target):                            │
│                                                                 │
│ A. Predictor de ETA Delay:                                     │
│    - Input: [driver_features, route_features, hora]            │
│    - Output: eta_difference_minutes (regresión)                │
│    - Uso: "Este chofer llegará 12 min tarde en esta ruta"     │
│                                                                 │
│ B. Clasificador de Incidentes:                                 │
│    - Input: [driver_features, route_features]                  │
│    - Output: incident_probability (0-1)                        │
│    - Uso: "Probabilidad de incidente: 15%"                     │
│                                                                 │
│ C. Predictor de Fuel Efficiency:                               │
│    - Input: [driver_features, route_features]                  │
│    - Output: expected_fuel_consumption_liters                  │
│    - Uso: "Consumo estimado: 285L (vs flota avg: 310L)"       │
│                                                                 │
│ Output: trained_models/                                        │
│   - success_predictor.pkl                                      │
│   - eta_predictor.pkl                                          │
│   - incident_classifier.pkl                                    │
│   - fuel_predictor.pkl                                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ REENTRENAMIENTO CONTINUO (CI/CD para ML)                       │
├─────────────────────────────────────────────────────────────────┤
│ Frecuencia: Mensual (o cuando se acumulan +500 viajes)        │
│                                                                 │
│ Proceso Automatizado:                                          │
│   1. Extraer nuevos trip_outcomes del último mes               │
│   2. Agregar a dataset histórico                               │
│   3. Re-entrenar modelos con datos actualizados                │
│   4. Validar performance (si R² > 0.7, deploy)                 │
│   5. A/B testing: comparar nuevo modelo vs anterior            │
│   6. Si nuevo modelo es mejor (+5% accuracy):                  │
│      - Deploy a producción                                     │
│      - Actualizar driver_scores.json                           │
│   7. Monitorear drift (concept drift detection)                │
│                                                                 │
│ Métricas de Monitoreo:                                         │
│   - Model accuracy over time                                   │
│   - Feature importance drift                                   │
│   - Prediction vs actual (residuals analysis)                  │
│   - Business KPIs (on-time delivery rate, incident rate)       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💡 CASOS DE USO: APRENDIZAJE CONTINUO

### Caso 1: Aprendiendo de ETAs

**Escenario:**
- Ruta: Buenos Aires → Mendoza (1,100 km)
- Chofer asignado: Juan Pérez (Cluster: Equilibrado, Score: 75)
- ETA estimado: 16:00 hrs
- Hora real de llegada: 17:30 hrs (+90 min tarde)

**¿Qué aprendemos?**
```python
# El sistema registra:
trip_outcome = {
    'trip_id': 'trip_12345',
    'driver_id': 'juan_perez',
    'route_id': 'BA-Mendoza',
    'driver_cluster': 1,  # Equilibrado
    'driver_score': 75,
    'route_score': 68,
    'match_score': 82,
    'eta_difference_minutes': 90,  # TARDE
    'on_time_delivery': False,
    'had_incident': False,
    'fuel_efficiency_delta': +5,  # Gastó 5L más de lo esperado
}

# Análisis ML:
# - Ruta BA-Mendoza con chofer Cluster 1 (Equilibrado) → Alto riesgo de delay
# - Pattern detectado: Choferes Cluster 1 + rutas >1000km → +60 min promedio
# - Acción futura: Recomendar solo choferes Cluster 0 (Conservadores) para esta ruta
# - O ajustar ETA: +45 min si se asigna Cluster 1
```

**Mejora en Recomendaciones:**
A partir del próximo mes, cuando alguien pida BA → Mendoza:
- Sistema prefiere choferes Cluster 0 (Conservadores)
- Si asigna Cluster 1, ajusta ETA automáticamente: +45 min
- Notifica al dispatcher: "⚠️ Este chofer históricamente llega 45 min tarde en rutas largas"

---

### Caso 2: Aprendiendo de Incidentes

**Escenario:**
- Ruta: Rosario → Córdoba (montaña)
- Chofer: María López (Cluster: Agresivo, Score: 65)
- Resultado: Incidente (frenada brusca severa, casi accidente)

**¿Qué aprendemos?**
```python
trip_outcome = {
    'driver_id': 'maria_lopez',
    'route_id': 'Rosario-Cordoba',
    'driver_cluster': 2,  # Agresivo
    'route_peligrosity_score': 85,  # ALTA
    'had_incident': True,
    'incident_type': 'harsh_braking_severe',
    'incident_severity': 'high',
    'overall_success_score': 35  # BAJO
}

# Análisis ML:
# - Pattern: Chofer Cluster 2 (Agresivo) + Ruta peligrosidad >80 → 65% prob. incidente
# - Acción: BLOQUEAR asignaciones de Cluster 2 a rutas peligrosidad >70
# - Re-entrenar: Ajustar scoring para penalizar más esta combinación
```

**Mejora en Recomendaciones:**
- Sistema NO recomendará choferes Cluster 2 (Agresivos) para rutas peligrosas
- Si no hay alternativa, alerta: "🚨 RIESGO ALTO: Esta combinación tiene 65% prob. de incidente"
- Sugiere capacitación: "María López necesita entrenamiento en manejo de montaña"

---

### Caso 3: Aprendiendo de Eficiencia de Combustible

**Escenario:**
- Chofer: Carlos Gómez (Cluster: Conservador, Score: 90)
- Ruta: Autopista BA → Rosario (300 km)
- Consumo esperado: 75L
- Consumo real: 68L (-7L, 9% ahorro)

**¿Qué aprendemos?**
```python
trip_outcome = {
    'driver_id': 'carlos_gomez',
    'route_id': 'BA-Rosario',
    'predicted_fuel': 75,
    'actual_fuel': 68,
    'fuel_efficiency_delta': -7,  # AHORRO
    'overall_success_score': 95
}

# Análisis ML:
# - Pattern: Carlos Gómez consistentemente ahorra 8-10% combustible
# - Feature importance: cruise_control_usage=95% es clave
# - Acción: Promover a "Best Performer" tier
# - Usar como benchmark para entrenar otros choferes
```

**Mejora en Recomendaciones:**
- Carlos Gómez recibe prioridad en rutas largas de autopista
- Dashboard muestra: "💰 Este chofer ahorrará ~$3,500 en combustible en este viaje"
- Sistema identifica features que Carlos hace bien (cruise control) y sugiere capacitación a otros

---

## 📊 MÉTRICAS DE ÉXITO DEL SISTEMA DE APRENDIZAJE

### KPIs del Modelo Supervisado (Post-Hackathon)

| Métrica | Target Mes 1 | Target Mes 3 | Target Mes 6 |
|---------|-------------|-------------|-------------|
| **Model Accuracy (R²)** | 0.60 | 0.75 | 0.85 |
| **ETA Prediction MAE** | ±20 min | ±15 min | ±10 min |
| **Incident Prediction AUC** | 0.70 | 0.80 | 0.85 |
| **Fuel Prediction MAPE** | 8% | 5% | 3% |
| **On-Time Delivery Rate** | 75% | 85% | 90% |
| **Incident Rate Reduction** | -10% | -20% | -30% |
| **Fuel Savings vs Baseline** | 5% | 12% | 18% |

### Datos Necesarios para Entrenar

**Mínimo Viable:**
- 500 viajes completados (3-4 meses de operación)
- 30+ choferes únicos
- 50+ rutas únicas
- Mix de outcomes (éxitos y fracasos)

**Óptimo:**
- 2,000+ viajes (12 meses)
- 50+ choferes
- 100+ rutas
- Datos de clima, tráfico, eventos especiales

---

## 🔄 CICLO DE VIDA DEL MODELO

```
1. HACKATHON (Semana 1)
   └─> Clustering unsupervised
   └─> Motor de recomendación basado en reglas
   └─> PoC funcional

2. POST-HACKATHON (Mes 1-2)
   └─> Implementar recolección de outcomes
   └─> Dashboard de tracking de KPIs
   └─> Acumular datos históricos

3. PRIMERA ITERACIÓN ML (Mes 3)
   └─> Entrenar primer modelo supervisado
   └─> Validar con datos de mes 1-2
   └─> A/B testing: ML vs reglas

4. OPTIMIZACIÓN CONTINUA (Mes 4+)
   └─> Reentrenamiento mensual
   └─> Feature engineering avanzado
   └─> Incorporar nuevas fuentes de datos

5. MADUREZ (Año 1+)
   └─> Modelos especializados por tipo de ruta
   └─> Deep learning para patrones complejos
   └─> Predicción proactiva de mantenimiento
```

---

## 🚀 ROADMAP DE IMPLEMENTACIÓN

**CRÍTICO: Entrega el VIERNES 8 NOVIEMBRE 2025**

### VIERNES 1 NOV (HOY): Setup & Data Extraction
- [x] Documentación completa (RUMBO.md)
- [ ] Obtener JSON completo de Scania API (21-31 oct)
- [ ] Script `extract_data.py`
  - Extraer features de seguridad
  - Extraer features de eficiencia  
  - **Calcular features de CO2** (fuel × 2.68)
  - Calcular features derivados
- [ ] Guardar `dataset_viajes.csv`
- [ ] Verificar calidad de datos (>100 viajes, 15+ choferes)

### SÁBADO 2 NOV: ML Pipeline & Clustering
- [ ] Análisis exploratorio (estadísticas, distribuciones)
- [ ] Script `train_clustering.py`
  - Normalizar features
  - Método del codo (determinar K óptimo)
  - Entrenar K-Means
  - Interpretar clusters (visualización PCA)
- [ ] Calcular scores agregados por chofer
  - Safety score
  - Efficiency score
  - **Carbon efficiency score** 🌱
  - Overall score
- [ ] Guardar `driver_scores.json`

### DOMINGO 3 NOV: Backend API
- [ ] Setup NestJS project
- [ ] Implementar endpoints:
  - `GET /api/drivers` (lista todos)
  - `GET /api/drivers/:id` (detalle chofer)
  - `GET /api/drivers/ranking` (top 10)
  - `POST /api/drivers/recommend` (recomendación)
- [ ] Lógica de motor de recomendación
  - Filtrado por riesgo de ruta
  - Cálculo de compatibilidad
  - Consideración de equidad (km)
  - **Estimación de CO2 por viaje** 🌱
- [ ] Testing con Postman

### LUNES 4 NOV: Frontend Base
- [ ] Setup React + Vite + TailwindCSS
- [ ] Componentes básicos:
  - `DriverRanking` (tabla top 10)
  - `DriverDetail` (perfil individual con CO2)
  - `RouteForm` (origen/destino/tipo)
  - `RecommendationResults` (top 3 choferes)
- [ ] Integración con API backend
- [ ] Styling básico

### MARTES 5 NOV: Features & Polish
- [ ] Dashboard completo
  - Métricas de flota
  - Gráficos (distribución clusters, CO2 por chofer)
- [ ] **Visualización de CO2** 🌱
  - Badge de ahorro de CO2 en recomendaciones
  - Comparativa chofer vs promedio flota
  - Equivalencias (árboles, vuelos)
- [ ] Casos de demo preparados (3 rutas)
- [ ] Refinamiento de UX

### MIÉRCOLES 6 NOV: Testing & Refinamiento
- [ ] Testing end-to-end
- [ ] Optimizaciones de performance
- [ ] Manejo de edge cases
- [ ] Deploy de prueba (Vercel + Railway)
- [ ] Documentación de API

### JUEVES 7 NOV: Demo & Pitch
- [ ] **Preparar pitch final** (usar estructura del doc)
- [ ] **Crear slides de presentación**
  - Problema
  - Solución (RUMBO)
  - Demo del sistema
  - Impacto (seguridad + CO2)
  - Métricas proyectadas
- [ ] Ensayar demo (flujo completo)
- [ ] Video de respaldo (por si falla algo en vivo)
- [ ] Backup de datos y código

### VIERNES 8 NOV: ENTREGA 🎯
- [ ] Presentación del hackathon
- [ ] Demo en vivo
- [ ] Responder preguntas del jurado

---

## 🔧 STACK TECNOLÓGICO

### Backend:
- **NestJS** (TypeScript) - API REST
- **Python 3.9+** - ML Pipeline
  - pandas, numpy
  - scikit-learn (K-Means, StandardScaler)
  - matplotlib, seaborn (visualización)

### Frontend:
- **React 18+**
- **Vite** (build tool)
- **TailwindCSS** (estilos)
- **Axios** (HTTP client)

### Data Source:
- **Scania Fleet Management API**
  - Driver Evaluation Report v2

---

## 📈 MÉTRICAS DE ÉXITO

### KPIs del Sistema:

1. **Precisión de clustering:**
   - Silhouette Score > 0.5 (buena separación de clusters)
   - Consistencia (ejecutar 10 veces, mismos resultados)

2. **Calidad de recomendaciones:**
   - Top 1 recomendado tiene score >85 (90% de los casos)
   - Match score promedio >80%

3. **Impacto en seguridad (proyectado):**
   - Choferes recomendados tienen -30% harsh braking vs no recomendados
   - Reducción estimada de 28% en incidentes

4. **Equidad:**
   - Desviación estándar de km asignados reduce en 20%
   - Choferes con <5000 km reciben 30% más asignaciones

---

## 🎯 CASOS DE USO (para demo)

### Caso 1: Viaje de alto riesgo
**Input:**
- Ruta: Terminal Rosario → Mina San Juan (1,250 km, montaña)
- Carga: Explosivos Clase 1.1
- Riesgo: ALTO

**Output esperado:**
- Recomendar a Ana Silva (score: 95, cluster: Conservador)
- Estimación: 285 kg CO2 (vs 340 kg promedio)
- Reasoning:
  - 0 frenadas bruscas en últimos 10 días
  - Score de manejo en montaña: 94/100
  - Certificación para cargas peligrosas
  - 🌱 **Ahorrará 55 kg CO2 en este viaje**

### Caso 2: Viaje urbano eficiente
**Input:**
- Ruta: Terminal BA → Distribución urbana (120 km, ciudad)
- Carga: Mercadería general
- Riesgo: BAJO

**Output esperado:**
- Recomendar a Pedro Rodríguez (score: 88, cluster: Equilibrado)
- Estimación: 32 kg CO2 (vs 35 kg promedio)
- Reasoning:
  - Bajo idle time (7%) - ideal para ciudad
  - Buen consumo urbano (22 L/100km)
  - Menos km acumulados (equidad)
  - 🌱 **Ahorrará 3 kg CO2 vs promedio**

### Caso 3: Viaje largo de ruta
**Input:**
- Ruta: BA → Mendoza (1,100 km, autopista)
- Carga: General
- Riesgo: MEDIO

**Output esperado:**
- Recomendar a Laura Martínez (score: 91, cluster: Equilibrado)
- Estimación: 292 kg CO2 (vs 310 kg promedio)
- Reasoning:
  - Alto uso de cruise control (85%)
  - Consumo eficiente en ruta (26 L/100km)
  - Velocidad constante (bajo brake_frequency)
  - 🌱 **Ahorrará 18 kg CO2 vs promedio**

**Total ahorro de CO2 en los 3 casos: 76 kg**  
**Proyección anual (300 viajes): 7.6 toneladas CO2 ahorradas** 🌱

---

## 📚 REFERENCIAS Y FUENTES

### Documentación técnica:
- **Scania Fleet Management API Docs:** (URL interna)
- **Scikit-learn K-Means:** https://scikit-learn.org/stable/modules/clustering.html#k-means

### Papers de referencia:
- "Driver Behavior Analysis for Accident Prevention" (IEEE 2023)
- "Clustering Techniques for Fleet Management" (Transportation Research 2024)

### Datos externos (para clasificación de rutas):
- OpenStreetMap (OSM) - Topografía, curvaturas
- OSRM (Open Source Routing Machine) - Cálculo de rutas
- Dirección Nacional de Vialidad (Argentina) - Infraestructura vial

---

## 🎤 PITCH FINAL

**Elevator Pitch (30 segundos):**

> "Tenemos telemetría de Scania cada 10 minutos. Tenemos viajes planificados. Tenemos conductores.
> 
> RUMBO usa IA para:
> 1. Detectar anomalías en tiempo real
> 2. Rankear conductores por seguridad y eficiencia
> 3. Recomendar el mejor conductor para cada viaje
> 
> Resultado: -28% incidentes, -20% carbono.
> 
> Un sistema que cumple todos nuestros propósitos: seguridad (impacto social), sustentabilidad (huella de carbono), e innovación (IA aplicada).
> 
> ¿Lo hacemos?"

**Value Proposition:**

Lo único que falta es la INTELIGENCIA para conectar conductores y rutas de la mejor manera posible.

RUMBO hace exactamente eso.

Marca el rumbo correcto:
- Para cada viaje
- Para cada conductor
- Para nuestra empresa
- Para el planeta

Es innovador, es sustentable, es viable.

---

## 📝 NOTAS IMPORTANTES

### Limitaciones conocidas:
1. **No tenemos ETA de hojas de ruta:** No podemos calcular `eta_delay_minutes` con precisión. Solución: omitir esta feature o estimarla con velocidad promedio.
2. **No tenemos GPS en tiempo real:** No podemos calcular `route_deviation_meters` con precisión. Solución: usar como feature secundaria o estimarla.
3. **Dataset limitado:** 10 días de datos (21-31 oct). Para producción, reentrenar con 3-6 meses de histórico.

### Asunciones:
- Todos los choferes usan vehículos Scania con telemetría activa
- Los datos de Scania son confiables y representativos
- Las clasificaciones de ruta (alta/media/baja peligrosidad) son provistas por otro componente del sistema

### Futuras mejoras:
- **Modelo supervisado (XGBoost):** Predecir incidentes con 7 días de anticipación
- **Detección de anomalías en tiempo real:** Alertas push a supervisores
- **Optimización multiobjetivo:** Balancear seguridad + eficiencia + equidad simultáneamente
- **Integración con ERP:** Asignación automática de conductores

---

## 🏁 CONCLUSIÓN

RUMBO es un sistema viable, escalable y con impacto medible que transforma datos existentes (telemetría de Scania) en inteligencia accionable para mejorar seguridad, eficiencia y sustentabilidad de la flota.

**El diferenciador clave:** No requerimos nuevos sensores ni hardware adicional. Usamos lo que ya tenemos de manera inteligente.

**La magia:** El mismo sistema que mejora seguridad también reduce huella de carbono. Conducción segura = conducción eficiente.

---

**Última actualización:** 2025-11-01  
**Autor:** Equipo RUMBO - Hackathon HG
