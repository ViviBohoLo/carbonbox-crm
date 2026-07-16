# Reglas de precio — CarbonBox
# Huella de Carbono Organizacional

Última actualización: abril 2026  
Fuente: calculadora oficial del sitio web carbonbox.app

---

## Fórmula de cálculo

```
precio_final = round(base_sector * (1 + pct_empleados + pct_adicional))
```

Donde:
- `base_sector` = precio base del sector (ver tabla de sectores)
- `pct_empleados` = porcentaje adicional según tamaño de empresa (dentro del sector)
- `pct_adicional` = suma de porcentajes de los componentes incluidos según el plan

Para descuento ATICA: `precio_con_descuento = round(precio_final * 0.90)`

---

## Tabla de sectores — Precio base y porcentajes por tamaño

Los tamaños de empresa corresponden a las siguientes categorías de empleados:

| Tamaño | Interpretación |
|--------|----------------|
| `10 o menos` | Hasta 10 empleados |
| `50` | Hasta 50 empleados |
| `70` | Hasta 70 empleados |
| `100` | Hasta 100 empleados |
| `150` | Hasta 150 empleados |
| `200` | Hasta 200 empleados |
| `500` | Hasta 500 empleados |
| `1000` | Hasta 1.000 empleados |
| `1500` | Hasta 1.500 empleados |
| `2000` | Hasta 2.000 empleados |
| `>2000` | Más de 2.000 → cotización personalizada |

### Sectores con base $1.845 USD

**Minería (extracción de petróleo, gas y minerales)**

| Tamaño | pct_empleados |
|--------|--------------|
| 10 o menos | 0.00 |
| 50 | 0.05 |
| 70 | 0.10 |
| 100 | 0.20 |
| 150 | 0.30 |
| 200 | 0.35 |
| 500 | 0.40 |
| 1000 | 0.50 |
| 1500 | 0.55 |
| 2000 | 0.60 |

---

### Sectores con base $1.599 USD

**Industria manufacturera**

| Tamaño | pct_empleados |
|--------|--------------|
| 10 o menos | 0.00 |
| 50 | 0.05 |
| 70 | 0.10 |
| 100 | 0.20 |
| 150 | 0.30 |
| 200 | 0.35 |
| 500 | 0.40 |
| 1000 | 0.50 |
| 1500 | 0.55 |
| 2000 | 0.60 |

---

### Sectores con base $1.476 USD

**Construcción / Energía (transformación) / Agroindustria**

| Tamaño | pct_empleados |
|--------|--------------|
| 10 o menos | 0.00 |
| 50 | 0.05 |
| 70 | 0.10 |
| 100 | 0.20 |
| 150 | 0.30 |
| 200 | 0.35 |
| 500 | 0.40 |
| 1000 | 0.50 |
| 1500 | 0.55 |
| 2000 | 0.60 |

---

### Sectores con base $1.230 USD

**Agropecuario (agricultura y ganadería) / Silvicultura / Distribuidores (Retail) & E-commerce**

| Tamaño | pct_empleados |
|--------|--------------|
| 10 o menos | 0.00 |
| 50 | 0.03 |
| 70 | 0.07 |
| 100 | 0.15 |
| 150 | 0.25 |
| 200 | 0.30 |
| 500 | 0.35 |
| 1000 | 0.40 |
| 1500 | 0.45 |
| 2000 | 0.50 |

---

### Sectores con base $984 USD

**Turismo / Administración pública / Educación / Institucional / Salud / Tecnología / Transporte, movilidad y logística**

| Tamaño | pct_empleados |
|--------|--------------|
| 10 o menos | 0.00 |
| 50 | 0.02–0.03* |
| 70 | 0.05–0.07* |
| 100 | 0.10–0.15* |
| 150 | 0.20–0.25* |
| 200 | 0.25–0.30* |
| 500 | 0.30–0.35* |
| 1000 | 0.35–0.40* |
| 1500 | 0.40–0.45* |
| 2000 | 0.45–0.50* |

*Tecnología y Transporte usan pct ligeramente más alto (0.03/0.07/0.15/0.25/0.30/0.35/0.40/0.45/0.50).
Los demás usan (0.02/0.05/0.10/0.20/0.25/0.30/0.35/0.40/0.45).

---

### Sectores con base $861 USD

**Comunicaciones / Financiero y seguros**

| Tamaño | pct_empleados |
|--------|--------------|
| 10 o menos | 0.00 |
| 50 | 0.02 |
| 70 | 0.05 |
| 100 | 0.10 |
| 150 | 0.15–0.20* |
| 200 | 0.20–0.25* |
| 500 | 0.25–0.30* |
| 1000 | 0.30–0.35* |
| 1500 | 0.35–0.40* |
| 2000 | 0.40–0.45* |

*Financiero usa pct ligeramente más alto desde 150 empleados.

---

### Sectores con base $615 USD

**Entretenimiento y cultura / Consultoría y prestación de servicios**

| Tamaño | pct_empleados |
|--------|--------------|
| 10 o menos | 0.00 |
| 50 | 0.02 |
| 70 | 0.05 |
| 100 | 0.10 |
| 150 | 0.20 |
| 200 | 0.25 |
| 500 | 0.30 |
| 1000 | 0.35 |
| 1500 | 0.40 |
| 2000 | 0.45 |

---

### Sectores con base $369 USD

**Emprendimientos**

| Tamaño | pct_empleados |
|--------|--------------|
| 10 o menos | 0.00 |
| 50 | 0.02 |
| 70 | 0.05 |
| 100 | 0.07 |
| 150 | 0.10 |
| 200 | 0.15 |
| 500 | 0.20 |
| 1000 | 0.25 |
| 1500 | 0.30 |
| 2000 | 0.35 |

---

## Componentes adicionales por plan (pct_adicional)

Cada plan suma los siguientes componentes. Los porcentajes son sobre el precio base.

### Plan Esencial
- Informe ejecutivo
- Entrenamiento autogestionado
- Recomendaciones de reducción del sector

### Plan Pro
- Capacitación del equipo experto
- Informe técnico (no auditable)
- Experto 24 hr (2 hr/mes)
- Validación de datos
- Recomendaciones de reducción personalizadas

### Plan Experto
- Capacitación & taller de aprendizaje
- Reporte auditable ISO-GHG
- Experto Full (dedicación completa)
- Validación de datos & soportes
- Acompañamiento para auditoría
- Proyecciones, análisis y plan de reducción

---

## Tablas de porcentajes por componente

### Experto dedicado

| Tamaño | Experto Full | Experto 96hr | Experto 48hr | Experto 24hr |
|--------|-------------|-------------|-------------|-------------|
| 10 o menos | 0.35 | 0.30 | 0.20 | 0.10 |
| 50 | 0.35 | 0.30 | 0.20 | 0.10 |
| 70 | 0.40 | 0.30 | 0.20 | 0.10 |
| 100 | 0.40 | 0.40 | 0.30 | 0.20 |
| 150 | 0.50 | 0.40 | 0.30 | 0.20 |
| 200 | 0.50 | 0.40 | 0.30 | 0.20 |
| 500 | 0.70 | 0.50 | 0.40 | 0.30 |
| 1000 | 0.70 | 0.60 | 0.50 | 0.40 |
| 1500 | 0.70 | 0.60 | 0.50 | 0.40 |
| 2000 | 0.70 | 0.60 | 0.50 | 0.40 |

*Nota: "Experto 24hr" usa claves de rango ("71-100" en vez de "100") — en la calculadora web esto genera resultado 0 para tamaños estándar. Se recomienda usar el script calcular-precio.py para obtener valores exactos.*

---

### Tipo de reporte

| Tamaño | Auditable ISO-GHG | Auditable GHG | Informe técnico | Informe ejecutivo |
|--------|------------------|--------------|----------------|-----------------|
| 10 o menos | 0.35 | 0.25 | 0.20 | 0.10 |
| 50 | 0.35 | 0.30 | 0.20 | 0.10 |
| 70 | 0.40 | 0.30 | 0.25 | 0.10 |
| 100 | 0.40 | 0.35 | 0.25 | 0.15 |
| 150 | 0.45 | 0.35 | 0.25 | 0.15 |
| 200 | 0.45 | 0.40 | 0.30 | 0.15 |
| 500 | 0.50 | 0.40 | 0.30 | 0.20 |
| 1000 | 0.50 | 0.45 | 0.35 | 0.20 |
| 1500 | 0.55 | 0.45 | 0.35 | 0.25 |
| 2000 | 0.55 | 0.50 | 0.35 | 0.30 |

---

### Capacitación

| Tamaño | Autogestionada | Capacitación | Capacitación & Taller |
|--------|---------------|-------------|----------------------|
| 10 o menos | 0.20 | 0.23 | 0.25 |
| 50 | 0.20 | 0.23 | 0.25 |
| 70 | 0.20 | 0.28 | 0.30 |
| 100 | 0.20 | 0.28 | 0.30 |
| 150 | 0.20 | 0.30 | 0.32 |
| 200 | 0.25 | 0.30 | 0.35 |
| 500 | 0.25 | 0.30 | 0.35 |
| 1000 | 0.25 | 0.35 | 0.40 |
| 1500 | 0.25 | 0.35 | 0.40 |
| 2000 | 0.25 | 0.40 | 0.45 |

---

### Validación de datos

| Tamaño | Validación de datos | Validación de datos & soportes |
|--------|--------------------|---------------------------------|
| 10 o menos | 0.00 | 0.15 |
| 50 | 0.10 | 0.20 |
| 70 | 0.15 | 0.20 |
| 100 | 0.20 | 0.20 |
| 150 | 0.20 | 0.25 |
| 200 | 0.20 | 0.25 |
| 500 | 0.25 | 0.25 |
| 1000 | 0.25 | 0.30 |
| 1500 | 0.25 | 0.35 |
| 2000 | 0.30 | 0.40 |

---

### Gestión de reducciones

| Tamaño | Recomendaciones sector | Recomendaciones personalizadas | Proyecciones & plan |
|--------|----------------------|-------------------------------|---------------------|
| 10 o menos | 0.10 | 0.23 | 0.25 |
| 50 | 0.20 | 0.23 | 0.25 |
| 70 | 0.20 | 0.28 | 0.30 |
| 100 | 0.20 | 0.28 | 0.30 |
| 150 | 0.20 | 0.30 | 0.32 |
| 200 | 0.25 | 0.30 | 0.35 |
| 500 | 0.25 | 0.30 | 0.35 |
| 1000 | 0.25 | 0.35 | 0.34 |
| 1500 | 0.25 | 0.35 | 0.40 |
| 2000 | 0.25 | 0.40 | 0.40 |

---

### Acompañamiento para auditoría (solo Plan Experto)

| Tamaño | pct |
|--------|-----|
| 10 o menos | 0.20 |
| 50 | 0.20 |
| 70 | 0.30 |
| 100 | 0.30 |
| 150 | 0.40 |
| 200 | 0.40 |
| 500 | 0.45 |
| 1000 | 0.45 |
| 1500 | 0.45 |
| 2000 | 0.50 |

---

## Otras reglas de precio

### Descuento ATICA
- **Condición:** el cliente llega referido por ATICA o es cliente activo de ATICA.
- **Descuento:** 10% sobre el precio calculado.
- **Cálculo:** `precio_con_descuento = round(precio_final * 0.90)`

### Precio mensual equivalente
- `precio_mensual = round(precio_final / 12)`
- Siempre incluir en la slide de inversión.

### Fecha límite de la propuesta
- `fecha_limite = fecha_envio + 60 días calendario`
- Formato: "[día] de [mes] de [año]"

### Forma de pago
- Estándar: 50% al inicio, 50% al final.
- Salvo negociación especial.

### IVA
- Todos los servicios son **exentos de IVA**.
- Ortografía correcta: **"exentos"** (NO "excentos").

### Pago en pesos colombianos
- Se toma la TRM del día del primer pago.
- Mencionar solo si el cliente es colombiano o lo solicita.

### Exclusiones (notas al pie)
- El precio NO incluye pólizas de ser requeridas.
- El precio NO incluye viajes fuera de Bogotá (aplica principalmente para Plan Pro y Experto con capacitación presencial).

### Clientes con más de 2.000 empleados
- No se calcula con la fórmula estándar.
- Respuesta: "Contáctanos para una cotización personalizada."

---

## Uso del script de cálculo

Para calcular precios de forma exacta (replicando la calculadora web), usar:

```
python calcular-precio.py
```

El script acepta como parámetros: sector, tamaño (número de empleados), plan.
Devuelve: precio Esencial, precio Pro, precio Experto, precio con descuento ATICA.
