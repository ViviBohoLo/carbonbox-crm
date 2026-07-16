# Formulario de Intake — HC Organizacional
# CarbonBox · Huella de Carbono de Empresas

> Llena este formulario antes de generar la cotización. Puedes completarlo directamente
> o pegarlo junto con la transcripción/notas de la llamada para que Claude extraiga los campos.

---

## CAMPOS OBLIGATORIOS

| Campo | Valor |
|-------|-------|
| `nombre_cliente` | |
| `sector_cliente` | *(ver lista de sectores en reglas-precio.md)* |
| `num_empleados` | *(número real, ej: 85 — se normaliza automáticamente a la categoría de precio)* |
| `plan_recomendado` | *(Esencial / Pro / Experto)* |
| `es_cliente_alianza_atica` | *(Sí / No)* |
| `fecha_envio` | *(fecha en que se enviará la cotización, ej: 30 de abril de 2026)* |

---

## CAMPOS IMPORTANTES (enriquecen mucho la propuesta)

| Campo | Valor |
|-------|-------|
| `pais_ciudad` | |
| `num_sedes` | *(si opera en más de una sede o planta)* |
| `años_operando` | *(opcional, da contexto sobre la empresa)* |
| `motivacion_principal` | *(¿por qué quieren medir su huella? clientes, regulación, marca, licitaciones...)* |
| `primera_vez_midiendo` | *(Sí / No)* |
| `stakeholders_clave` | *(¿a quién le presentarán los resultados? junta directiva, clientes, reguladores...)* |
| `decisor_real` | *(nombre y cargo de quien aprueba la compra)* |
| `contacto_reunion` | *(nombre y cargo de quien asistió a la reunión de ventas)* |

---

## CAMPO CONDICIONAL

| Campo | Valor | Cuándo aplica |
|-------|-------|--------------|
| `precio_con_descuento` | *(calcular: precio_base × 0.90)* | Solo si alianza ATICA = Sí |

---

## NOTAS / CONTEXTO ADICIONAL

*(Pega aquí cualquier información relevante de la llamada, CRM, o notas del vendedor)*

```
[espacio para notas libres]
```

---

## TRANSCRIPCIÓN O NOTAS DE LLAMADA

*(Opcional — si pegas la transcripción, Claude extrae automáticamente los campos anteriores)*

```
[pegar transcripción o notas aquí]
```

---
---

# ═══════════════════════════════════════
# EJEMPLO DILIGENCIADO — CLIENTE FICTICIO DE PRUEBA
# ═══════════════════════════════════════

## CAMPOS OBLIGATORIOS

| Campo | Valor |
|-------|-------|
| `nombre_cliente` | Ecopack Colombia S.A.S. |
| `sector_cliente` | Industria manufacturera |
| `num_empleados` | 95 |
| `plan_recomendado` | Pro |
| `es_cliente_alianza_atica` | No |
| `fecha_envio` | 30 de abril de 2026 |

## CAMPOS IMPORTANTES

| Campo | Valor |
|-------|-------|
| `pais_ciudad` | Bogotá, Colombia |
| `num_sedes` | 2 plantas en Bogotá |
| `años_operando` | 12 años |
| `motivacion_principal` | Clientes industriales en Europa exigen datos verificables de huella de carbono para renovar contratos. También quieren diferenciarse en licitaciones públicas con criterios ambientales. |
| `primera_vez_midiendo` | Sí |
| `stakeholders_clave` | Clientes industriales europeos, equipo de licitaciones, junta directiva |
| `decisor_real` | Camilo Restrepo, Gerente General |
| `contacto_reunion` | Valentina Ospina, Coordinadora de Sostenibilidad |

## NOTAS ADICIONALES

Fabrican empaques de cartón reciclado para sector alimentos e industrial. Valentina buscó la solución tras recibir una alerta de un cliente alemán que pidió datos de carbono antes de renovar el contrato. Camilo es el decisor final y necesita ver el ROI claramente. Reunión muy positiva. Siguiente paso: propuesta formal esta semana.
