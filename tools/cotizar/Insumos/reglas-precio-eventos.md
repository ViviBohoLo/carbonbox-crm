# Reglas de precio — CarbonBox
# Huella de Carbono de Eventos

Última actualización: julio 2026
Fuente: calculadora oficial del sitio web carbonbox.app (pestaña "Eventos" en /precios)

Este documento es el equivalente de `reglas-precio.md` pero para la huella de carbono
de **eventos** (congresos, reuniones empresariales, festivales, conciertos, eventos masivos),
NO para huella corporativa/organizacional. Úsalo cuando `tipo_servicio = evento`.

---

## Fórmula de cálculo

```
precio_final = round(precio_base_asistentes * (1 + pct_adicional))
```

Donde:
- `precio_base_asistentes` = precio base según tipo de evento y número de asistentes (ver tabla)
- `pct_adicional` = suma de porcentajes de los componentes incluidos según el plan

Para descuento ATICA: `precio_con_descuento = round(precio_final * 0.90)`

A diferencia de la huella organizacional, **no hay "sector" ni "% por tamaño de empresa"**:
el precio base depende directamente del tipo de evento y el número de asistentes.

---

## Tabla de precios base — por tipo de evento y número de asistentes

| Asistentes | Congresos y Reuniones empresariales | Festivales, Conciertos y Eventos Masivos |
|---|---|---|
| 50 o menos | $246 | $492 |
| 100 | $308 | $554 |
| 500 | $369 | $615 |
| 1.000 | $431 | $640 |
| 10.000 | $566 | $677 |
| 25.000 | $726 | $738 |
| 50.000 | $898 | $923 |
| 75.000 | $1.058 | $1.082 |
| 100.000 | $1.485 | $1.169 |
| 150.000 | $1.919 | $1.230 |
| 200.000 | $2.337 | $1.353 |
| > 200.000 | Contactar para cotización personalizada | Contactar para cotización personalizada |

**Nota sobre categorías:** el número de asistentes se normaliza a la categoría **igual o
inmediatamente superior** (ej: 20 personas → "50 o menos"; 80 personas → "100"; 180 personas → "500").
Usar `calcular-precio-eventos.py` para hacer esta normalización automáticamente.

---

## Componentes adicionales por plan (pct_adicional)

### Plan Esencial
- Informe ejecutivo
- Capacitación autogestionada
- Recomendaciones de reducción para el evento

### Plan Pro
- Capacitación del equipo organizador del evento
- Informe técnico (basado en GHG Protocol, no auditable)
- Experto dedicado 48 hr (4 hr/mes)
- Validación de datos
- Recomendaciones de reducción personalizadas
- Comunicación de carbono neutro

### Plan Experto
- Capacitación & taller de identificación de emisiones
- Reporte auditable ISO-GHG
- Experto Full (dedicación completa, hasta 156 hr)
- Validación de datos & soportes
- Proyecciones, análisis y plan de reducción
- Acompañamiento para auditoría
- Certificación del evento

---

## Tablas de porcentajes por componente

### Experto dedicado

| Asistentes | Experto Full | Experto 96hr (8hr/mes) | Experto 48hr (4hr/mes) | Experto 24hr (2hr/mes) |
|---|---|---|---|---|
| 50 o menos | 0.35 | 0.30 | 0.20 | 0.10 |
| 100 | 0.35 | 0.30 | 0.20 | 0.10 |
| 500 | 0.40 | 0.30 | 0.20 | 0.10 |
| 1.000 | 0.40 | 0.40 | 0.30 | 0.20 |
| 10.000 | 0.50 | 0.40 | 0.30 | 0.20 |
| 25.000 | 0.50 | 0.40 | 0.30 | 0.20 |
| 50.000 | 0.60 | 0.50 | 0.40 | 0.30 |
| 75.000 | 0.60 | 0.50 | 0.40 | 0.30 |
| 100.000 | 0.60 | 0.50 | 0.40 | 0.30 |
| 150.000 | 0.60 | 0.50 | 0.40 | 0.30 |
| 200.000 | 0.65 | 0.55 | 0.45 | 0.35 |

### Tipo de reporte

| Asistentes | Auditable ISO-GHG | Auditable GHG | Informe técnico | Informe ejecutivo |
|---|---|---|---|---|
| 50 o menos | 0.35 | 0.25 | 0.20 | 0.10 |
| 100 | 0.35 | 0.30 | 0.20 | 0.10 |
| 500 | 0.40 | 0.30 | 0.25 | 0.10 |
| 1.000 | 0.40 | 0.35 | 0.25 | 0.15 |
| 10.000 | 0.45 | 0.35 | 0.25 | 0.15 |
| 25.000 | 0.45 | 0.40 | 0.30 | 0.15 |
| 50.000 | 0.50 | 0.40 | 0.30 | 0.20 |
| 75.000 | 0.50 | 0.45 | 0.35 | 0.20 |
| 100.000 | 0.55 | 0.45 | 0.35 | 0.25 |
| 150.000 | 0.55 | 0.50 | 0.35 | 0.30 |
| 200.000 | 0.55 | 0.50 | 0.35 | 0.30 |

### Capacitación

| Asistentes | Autogestionada | Capacitación | Capacitación & taller |
|---|---|---|---|
| 50 o menos | 0.20 | 0.25 | 0.30 |
| 100 | 0.20 | 0.25 | 0.30 |
| 500 | 0.25 | 0.30 | 0.35 |
| 1.000 | 0.25 | 0.30 | 0.35 |
| 10.000 | 0.25 | 0.30 | 0.35 |
| 25.000 | 0.30 | 0.35 | 0.40 |
| 50.000 | 0.30 | 0.35 | 0.40 |
| 75.000 | 0.30 | 0.40 | 0.40 |
| 100.000 | 0.30 | 0.45 | 0.50 |
| 150.000 | 0.30 | 0.45 | 0.55 |
| 200.000 | 0.30 | 0.45 | 0.55 |

### Validación de datos

| Asistentes | Validación de datos | Validación de datos & soportes |
|---|---|---|
| 50 o menos | 0.10 | 0.15 |
| 100 | 0.13 | 0.20 |
| 500 | 0.20 | 0.23 |
| 1.000 | 0.20 | 0.23 |
| 10.000 | 0.20 | 0.25 |
| 25.000 | 0.20 | 0.30 |
| 50.000 | 0.25 | 0.35 |
| 75.000 | 0.25 | 0.40 |
| 100.000 | 0.25 | 0.45 |
| 150.000 | 0.30 | 0.50 |
| 200.000 | 0.35 | 0.55 |

### Gestión de reducciones

| Asistentes | Recomendaciones para el evento | Recomendaciones personalizadas | Proyecciones & plan de reducción |
|---|---|---|---|
| 50 o menos | 0.10 | 0.23 | 0.30 |
| 100 | 0.20 | 0.23 | 0.30 |
| 500 | 0.20 | 0.28 | 0.35 |
| 1.000 | 0.20 | 0.28 | 0.35 |
| 10.000 | 0.20 | 0.30 | 0.35 |
| 25.000 | 0.25 | 0.30 | 0.35 |
| 50.000 | 0.25 | 0.30 | 0.40 |
| 75.000 | 0.25 | 0.30 | 0.40 |
| 100.000 | 0.25 | 0.35 | 0.45 |
| 150.000 | 0.25 | 0.35 | 0.45 |
| 200.000 | 0.25 | 0.40 | 0.45 |

### Comunicación de carbono neutro (solo Plan Pro)

| Asistentes | pct |
|---|---|
| 50 o menos | 0.20 |
| 100 | 0.20 |
| 500 | 0.30 |
| 1.000 | 0.30 |
| 10.000 | 0.40 |
| 25.000 | 0.40 |
| 50.000 | 0.45 |
| 75.000 | 0.45 |
| 100.000 | 0.45 |
| 150.000 | 0.50 |
| 200.000 | 0.50 |

### Certificación del evento (solo Plan Experto)

| Asistentes | pct |
|---|---|
| 50 o menos | 0.30 |
| 100 | 0.30 |
| 500 | 0.40 |
| 1.000 | 0.40 |
| 10.000 | 0.50 |
| 25.000 | 0.50 |
| 50.000 | 0.55 |
| 75.000 | 0.55 |
| 100.000 | 0.55 |
| 150.000 | 0.60 |
| 200.000 | 0.60 |

### Acompañamiento para auditoría (solo Plan Experto)

| Asistentes | pct |
|---|---|
| 50 o menos | 0.20 |
| 100 | 0.20 |
| 500 | 0.30 |
| 1.000 | 0.30 |
| 10.000 | 0.40 |
| 25.000 | 0.40 |
| 50.000 | 0.45 |
| 75.000 | 0.45 |
| 100.000 | 0.45 |
| 150.000 | 0.50 |
| 200.000 | 0.55 |

---

## Otras reglas de precio (iguales a la huella organizacional)

### Descuento ATICA
- **Condición:** el cliente llega referido por ATICA o es cliente activo de ATICA.
- **Descuento:** 10% sobre el precio calculado.
- **Cálculo:** `precio_con_descuento = round(precio_final * 0.90)`

### Precio mensual equivalente
- `precio_mensual = round(precio_final / 12)`
- Siempre incluir en la slide de inversión.

### Fecha límite de la propuesta
- `fecha_limite = fecha_envio + 60 días calendario`

### Forma de pago
- Estándar: 50% al inicio, 50% al final.

### IVA
- Todos los servicios son **exentos de IVA**.

### Más de 200.000 asistentes
- No se calcula con la fórmula estándar.
- Respuesta: "Contáctanos para una cotización personalizada."

---

## Uso del script de cálculo

```
python calcular-precio-eventos.py --tipo-evento "Congresos y Reuniones empresariales" --num-asistentes 100 --plan pro
```

El script acepta: tipo de evento, número real de asistentes (se normaliza automáticamente
a la categoría más cercana) o la categoría exacta, y plan.
Devuelve: precio Esencial, Pro, Experto, y precio con descuento ATICA.

Ver también `Generadores/calcular-precio.py` para huella **organizacional** (empresas).
