#!/usr/bin/env python3
"""
Calculadora de precios CarbonBox — Huella de Carbono Organizacional
Replica exactamente la lógica de la calculadora del sitio web carbonbox.app

Uso:
    python calcular-precio.py
    → Muestra tabla de precios para todos los planes

    python calcular-precio.py --sector "Industria manufacturera" --tamano 100 --plan pro
    → Calcula precio específico

    python calcular-precio.py --listar-sectores
    → Lista todos los sectores disponibles
"""

import argparse
import math
import sys
import json as _json

# ─────────────────────────────────────────────────────────────────────────────
# BASE DE DATOS DE PRECIOS (replicada del JS de carbonbox.app)
# ─────────────────────────────────────────────────────────────────────────────

SECTORES = {
    "Agropecuario (agricultura y ganaderia)": {
        "base": 1230,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.03, "70": 0.07, "100": 0.15,
            "150": 0.25, "200": 0.3, "500": 0.35, "1000": 0.4,
            "1500": 0.45, "2000": 0.5
        }
    },
    "Silvicultura (aprovechamiento forestal)": {
        "base": 1230,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.03, "70": 0.07, "100": 0.15,
            "150": 0.25, "200": 0.3, "500": 0.35, "1000": 0.4,
            "1500": 0.45, "2000": 0.5
        }
    },
    "Mineria (extracción de petroleo, gas y minerales)": {
        "base": 1845,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.05, "70": 0.1, "100": 0.2,
            "150": 0.3, "200": 0.35, "500": 0.4, "1000": 0.5,
            "1500": 0.55, "2000": 0.6
        }
    },
    "Industria manufacturera": {
        "base": 1599,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.05, "70": 0.1, "100": 0.2,
            "150": 0.3, "200": 0.35, "500": 0.4, "1000": 0.5,
            "1500": 0.55, "2000": 0.6
        }
    },
    "Construcción": {
        "base": 1476,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.05, "70": 0.1, "100": 0.2,
            "150": 0.3, "200": 0.35, "500": 0.4, "1000": 0.5,
            "1500": 0.55, "2000": 0.6
        }
    },
    "Energia (transformación de la energía)": {
        "base": 1476,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.05, "70": 0.1, "100": 0.2,
            "150": 0.3, "200": 0.35, "500": 0.4, "1000": 0.5,
            "1500": 0.55, "2000": 0.6
        }
    },
    "Agroindustria": {
        "base": 1476,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.05, "70": 0.1, "100": 0.2,
            "150": 0.3, "200": 0.35, "500": 0.4, "1000": 0.5,
            "1500": 0.55, "2000": 0.6
        }
    },
    "Comunicaciones": {
        "base": 861,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.02, "70": 0.05, "100": 0.1,
            "150": 0.15, "200": 0.2, "500": 0.25, "1000": 0.3,
            "1500": 0.35, "2000": 0.4
        }
    },
    "Financiero y seguros": {
        "base": 861,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.02, "70": 0.05, "100": 0.1,
            "150": 0.2, "200": 0.25, "500": 0.3, "1000": 0.35,
            "1500": 0.4, "2000": 0.45
        }
    },
    "Turismo": {
        "base": 984,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.02, "70": 0.05, "100": 0.1,
            "150": 0.2, "200": 0.25, "500": 0.3, "1000": 0.35,
            "1500": 0.4, "2000": 0.45
        }
    },
    "Entretenimiento y cultura": {
        "base": 615,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.02, "70": 0.05, "100": 0.1,
            "150": 0.2, "200": 0.25, "500": 0.3, "1000": 0.35,
            "1500": 0.4, "2000": 0.45
        }
    },
    "Administración pública": {
        "base": 984,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.02, "70": 0.05, "100": 0.1,
            "150": 0.2, "200": 0.25, "500": 0.3, "1000": 0.35,
            "1500": 0.4, "2000": 0.45
        }
    },
    "Educación": {
        "base": 984,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.02, "70": 0.05, "100": 0.1,
            "150": 0.2, "200": 0.25, "500": 0.3, "1000": 0.35,
            "1500": 0.4, "2000": 0.45
        }
    },
    "Institucional": {
        "base": 984,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.02, "70": 0.05, "100": 0.1,
            "150": 0.2, "200": 0.25, "500": 0.3, "1000": 0.35,
            "1500": 0.4, "2000": 0.45
        }
    },
    "Salud": {
        "base": 984,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.02, "70": 0.05, "100": 0.1,
            "150": 0.2, "200": 0.25, "500": 0.3, "1000": 0.35,
            "1500": 0.4, "2000": 0.45
        }
    },
    "Tecnología": {
        "base": 984,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.03, "70": 0.07, "100": 0.15,
            "150": 0.25, "200": 0.3, "500": 0.35, "1000": 0.4,
            "1500": 0.45, "2000": 0.5
        }
    },
    "Distribuidores (Retail) & E-commerce": {
        "base": 1230,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.03, "70": 0.07, "100": 0.15,
            "150": 0.25, "200": 0.3, "500": 0.35, "1000": 0.4,
            "1500": 0.45, "2000": 0.5
        }
    },
    "Transporte, movilidad y logística": {
        "base": 984,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.03, "70": 0.07, "100": 0.15,
            "150": 0.25, "200": 0.3, "500": 0.35, "1000": 0.4,
            "1500": 0.45, "2000": 0.5
        }
    },
    "Consultoría y prestación de servicios": {
        "base": 615,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.02, "70": 0.05, "100": 0.1,
            "150": 0.2, "200": 0.25, "500": 0.3, "1000": 0.35,
            "1500": 0.4, "2000": 0.45
        }
    },
    "Emprendimientos": {
        "base": 369,
        "pct_empleados": {
            "10 o menos": 0.0, "50": 0.02, "70": 0.05, "100": 0.07,
            "150": 0.1, "200": 0.15, "500": 0.2, "1000": 0.25,
            "1500": 0.3, "2000": 0.35
        }
    }
}

EXPERTO_DEDICADO = {
    "Experto Full": {
        "10 o menos": 0.35, "50": 0.35, "70": 0.4, "100": 0.4,
        "150": 0.5, "200": 0.5, "500": 0.7, "1000": 0.7,
        "1500": 0.7, "2000": 0.7
    },
    "Experto 96hr": {
        "10 o menos": 0.3, "50": 0.3, "70": 0.3, "100": 0.4,
        "150": 0.4, "200": 0.4, "500": 0.5, "1000": 0.6,
        "1500": 0.6, "2000": 0.6
    },
    "Experto 48hr": {
        "10 o menos": 0.2, "50": 0.2, "70": 0.2, "100": 0.3,
        "150": 0.3, "200": 0.3, "500": 0.4, "1000": 0.5,
        "1500": 0.5, "2000": 0.5
    },
    # Nota: en el JS original "Experto 24hr" usa claves de rango ("71-100")
    # que no coinciden con las claves estándar → retorna 0 para tamaños estándar.
    # Aquí se mantiene ese comportamiento para fidelidad exacta.
    "Experto 24hr": {
        "0-10": 0.1, "11-50": 0.1, "51-70": 0.1, "71-100": 0.2,
        "101-150": 0.2, "151-200": 0.2, "201-500": 0.3,
        "501-1000": 0.4, "1001-1500": 0.4, "1501-2000": 0.4
    }
}

TIPO_REPORTE = {
    "Auditable ISO-GHG": {
        "10 o menos": 0.35, "50": 0.35, "70": 0.4, "100": 0.4,
        "150": 0.45, "200": 0.45, "500": 0.5, "1000": 0.5,
        "1500": 0.55, "2000": 0.55
    },
    "Auditable GHG": {
        "10 o menos": 0.25, "50": 0.3, "70": 0.3, "100": 0.35,
        "150": 0.35, "200": 0.4, "500": 0.4, "1000": 0.45,
        "1500": 0.45, "2000": 0.5
    },
    "Informe técnico": {
        "10 o menos": 0.2, "50": 0.2, "70": 0.25, "100": 0.25,
        "150": 0.25, "200": 0.3, "500": 0.3, "1000": 0.35,
        "1500": 0.35, "2000": 0.35
    },
    "Informe ejecutivo": {
        "10 o menos": 0.1, "50": 0.1, "70": 0.1, "100": 0.15,
        "150": 0.15, "200": 0.15, "500": 0.2, "1000": 0.2,
        "1500": 0.25, "2000": 0.3
    }
}

CAPACITACION = {
    "Autogestionada": {
        "10 o menos": 0.2, "50": 0.2, "70": 0.2, "100": 0.2,
        "150": 0.2, "200": 0.25, "500": 0.25, "1000": 0.25,
        "1500": 0.25, "2000": 0.25
    },
    "Capacitación": {
        "10 o menos": 0.23, "50": 0.23, "70": 0.28, "100": 0.28,
        "150": 0.3, "200": 0.3, "500": 0.3, "1000": 0.35,
        "1500": 0.35, "2000": 0.4
    },
    "Capacitación & taller": {
        "10 o menos": 0.25, "50": 0.25, "70": 0.3, "100": 0.3,
        "150": 0.32, "200": 0.35, "500": 0.35, "1000": 0.4,
        "1500": 0.4, "2000": 0.45
    }
}

VALIDACION_DATOS = {
    "Validación de datos": {
        "10 o menos": 0.0, "50": 0.1, "70": 0.15, "100": 0.2,
        "150": 0.2, "200": 0.2, "500": 0.25, "1000": 0.25,
        "1500": 0.25, "2000": 0.3
    },
    "Validación de datos & soportes": {
        "10 o menos": 0.15, "50": 0.2, "70": 0.2, "100": 0.2,
        "150": 0.25, "200": 0.25, "500": 0.25, "1000": 0.3,
        "1500": 0.35, "2000": 0.4
    }
}

GESTION_REDUCCIONES = {
    # NOTA: este componente usa claves de rango en el JS original ("0-10", "501-1000", etc.)
    # que nunca coinciden con las claves estándar del dropdown → siempre retorna 0.
    # Se mantiene el comportamiento exacto de la web (bug incluido).
    "Recomendaciones de reducción del sector": {
        "0-10": 0.1, "11-50": 0.2, "51-70": 0.2, "71-100": 0.2,
        "101-150": 0.2, "151-200": 0.25, "201-500": 0.25,
        "501-1000": 0.25, "1001-1500": 0.25, "1501-2000": 0.25
    },
    # NOTA: mezcla claves estándar (hasta "500") con una clave de rango ("501-1000").
    # Para tamano "1000", retorna 0 porque no existe esa clave estándar.
    # Para "1500" y "2000" sí tiene claves estándar y retorna el valor correcto.
    "Recomendaciones de reducción personalizadas": {
        "10 o menos": 0.23, "50": 0.23, "70": 0.28, "100": 0.28,
        "150": 0.3, "200": 0.3, "500": 0.3, "501-1000": 0.35,
        "1500": 0.35, "2000": 0.4
    },
    "Proyecciones, análisis y plan de reducción": {
        "10 o menos": 0.25, "50": 0.25, "70": 0.3, "100": 0.3,
        "150": 0.32, "200": 0.35, "500": 0.35, "1000": 0.34,
        "1500": 0.4, "2000": 0.4
    }
}

ACOMPANAMIENTO_AUDITORIA = {
    "10 o menos": 0.2, "50": 0.2, "70": 0.3, "100": 0.3,
    "150": 0.4, "200": 0.4, "500": 0.45, "1000": 0.45,
    "1500": 0.45, "2000": 0.5
}

# Tamaños válidos (en el mismo orden que la web)
TAMANOS_VALIDOS = ["10 o menos", "50", "70", "100", "150", "200", "500", "1000", "1500", "2000"]

# Códigos del campo `sectorCarbonbox` (Company, CRM Twenty) → nombre del sector en SECTORES.
# Twenty NO admite comas en las etiquetas de un SELECT, así que sus etiquetas no pueden ser
# idénticas a las de aquí. Pasar el CÓDIGO evita traducir a mano en cada cotización, que es
# donde antes se colaban errores de precio silenciosos.
# Mantener sincronizado con las opciones del campo sectorCarbonbox.
SECTOR_CRM = {
    "MINERIA": "Mineria (extracción de petroleo, gas y minerales)",
    "INDUSTRIA_MANUFACTURERA": "Industria manufacturera",
    "CONSTRUCCION": "Construcción",
    "ENERGIA": "Energia (transformación de la energía)",
    "AGROINDUSTRIA": "Agroindustria",
    "AGROPECUARIO": "Agropecuario (agricultura y ganaderia)",
    "SILVICULTURA": "Silvicultura (aprovechamiento forestal)",
    "RETAIL_ECOMMERCE": "Distribuidores (Retail) & E-commerce",
    "TURISMO": "Turismo",
    "ADMIN_PUBLICA": "Administración pública",
    "EDUCACION": "Educación",
    "INSTITUCIONAL": "Institucional",
    "SALUD": "Salud",
    "TECNOLOGIA": "Tecnología",
    "TRANSPORTE": "Transporte, movilidad y logística",
    "COMUNICACIONES": "Comunicaciones",
    "FINANCIERO": "Financiero y seguros",
    "ENTRETENIMIENTO": "Entretenimiento y cultura",
    "CONSULTORIA": "Consultoría y prestación de servicios",
    "EMPRENDIMIENTOS": "Emprendimientos",
}


def resolver_sector(sector: str) -> str:
    """Acepta el código del CRM (`sectorCarbonbox`, ej. 'MINERIA') o el nombre literal
    del sector. Devuelve siempre el nombre que entiende SECTORES."""
    if not sector:
        return sector
    return SECTOR_CRM.get(sector.strip().upper(), sector)


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL DE CÁLCULO
# ─────────────────────────────────────────────────────────────────────────────

def calcular_precio(plan: str, sector: str, tamano: str) -> dict:
    """
    Calcula el precio según el plan, sector y tamaño.
    Replica exactamente la función calcularPrecio() del JS de carbonbox.app.

    Args:
        plan: "esencial", "pro" o "experto"
        sector: nombre del sector (ver SECTORES) o código del CRM (ver SECTOR_CRM)
        tamano: categoría de tamaño (ver TAMANOS_VALIDOS)

    Returns:
        dict con precio_base, precio_mensual, precio_atica, desglose
    """
    if tamano == ">2000":
        return {"error": "Más de 2.000 empleados → Cotización personalizada. Contactar al equipo comercial."}

    sector = resolver_sector(sector)
    sector_data = SECTORES.get(sector)
    if not sector_data:
        sectores_disponibles = "\n  ".join(SECTORES.keys())
        return {"error": f"Sector no encontrado: '{sector}'\nSectores disponibles:\n  {sectores_disponibles}"}

    base_price = sector_data["base"]
    pct_empleados = sector_data["pct_empleados"].get(tamano, 0)
    adicional_pct = 0
    desglose = {"base": base_price, "pct_empleados": pct_empleados, "componentes": {}}

    plan = plan.lower()

    if plan == "esencial":
        componentes = {
            "Informe ejecutivo": TIPO_REPORTE["Informe ejecutivo"].get(tamano, 0),
            "Entrenamiento autogestionado": CAPACITACION["Autogestionada"].get(tamano, 0),
            "Recomendaciones de reducción del sector": GESTION_REDUCCIONES["Recomendaciones de reducción del sector"].get(tamano, 0),
        }

    elif plan == "pro":
        componentes = {
            "Capacitación del equipo": CAPACITACION["Capacitación"].get(tamano, 0),
            "Informe técnico": TIPO_REPORTE["Informe técnico"].get(tamano, 0),
            "Experto 24hr (2hr/mes)": EXPERTO_DEDICADO["Experto 24hr"].get(tamano, 0),
            "Validación de datos": VALIDACION_DATOS["Validación de datos"].get(tamano, 0),
            "Recomendaciones personalizadas": GESTION_REDUCCIONES["Recomendaciones de reducción personalizadas"].get(tamano, 0),
        }

    elif plan == "experto":
        componentes = {
            "Capacitación & taller": CAPACITACION["Capacitación & taller"].get(tamano, 0),
            "Reporte auditable ISO-GHG": TIPO_REPORTE["Auditable ISO-GHG"].get(tamano, 0),
            "Experto Full": EXPERTO_DEDICADO["Experto Full"].get(tamano, 0),
            "Validación de datos & soportes": VALIDACION_DATOS["Validación de datos & soportes"].get(tamano, 0),
            "Acompañamiento auditoría": ACOMPANAMIENTO_AUDITORIA.get(tamano, 0),
            "Proyecciones & plan de reducción": GESTION_REDUCCIONES["Proyecciones, análisis y plan de reducción"].get(tamano, 0),
        }

    else:
        return {"error": f"Plan no reconocido: '{plan}'. Usar: esencial, pro, experto"}

    adicional_pct = sum(componentes.values())
    precio_final = round(base_price * (1 + pct_empleados + adicional_pct))
    precio_mensual = round(precio_final / 12)
    precio_atica = round(precio_final * 0.90)
    precio_mensual_atica = round(precio_atica / 12)

    return {
        "plan": plan.capitalize(),
        "sector": sector,
        "tamano": tamano,
        "precio_final": precio_final,
        "precio_mensual": precio_mensual,
        "precio_atica": precio_atica,
        "precio_mensual_atica": precio_mensual_atica,
        "desglose": {
            "base": base_price,
            "pct_empleados": pct_empleados,
            "componentes": componentes,
            "adicional_total": adicional_pct,
            "multiplicador": round(1 + pct_empleados + adicional_pct, 4)
        }
    }


def normalizar_tamano(num_empleados: int) -> str:
    """
    Convierte un número real de empleados a la categoría de tamaño más cercana.
    """
    if num_empleados <= 10:
        return "10 o menos"
    elif num_empleados <= 50:
        return "50"
    elif num_empleados <= 70:
        return "70"
    elif num_empleados <= 100:
        return "100"
    elif num_empleados <= 150:
        return "150"
    elif num_empleados <= 200:
        return "200"
    elif num_empleados <= 500:
        return "500"
    elif num_empleados <= 1000:
        return "1000"
    elif num_empleados <= 1500:
        return "1500"
    elif num_empleados <= 2000:
        return "2000"
    else:
        return ">2000"


def calcular_todos_los_planes(sector: str, tamano: str) -> None:
    """Imprime tabla con los 3 planes para un sector y tamaño dados."""
    print(f"\n{'═'*65}")
    print(f"  CarbonBox — Calculadora de Precios HC Organizacional")
    print(f"{'═'*65}")
    print(f"  Sector : {sector}")
    print(f"  Tamaño : {tamano} empleados")
    print(f"{'─'*65}")
    print(f"  {'Plan':<12} {'Precio USD':>12} {'Mensual':>10} {'Con ATICA (−10%)':>18}")
    print(f"{'─'*65}")

    for plan in ["esencial", "pro", "experto"]:
        r = calcular_precio(plan, sector, tamano)
        if "error" in r:
            print(f"  {plan:<12} {r['error']}")
        else:
            print(f"  {r['plan']:<12} ${r['precio_final']:>10,} USD   ${r['precio_mensual']:>6,}/mes   ${r['precio_atica']:>8,} USD")

    print(f"{'═'*65}\n")


# ─────────────────────────────────────────────────────────────────────────────
# INTERFAZ DE LÍNEA DE COMANDOS
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calculadora de precios CarbonBox — HC Organizacional"
    )
    parser.add_argument("--sector", help="Nombre del sector")
    parser.add_argument("--tamano", help="Categoría de tamaño (ej: 100)")
    parser.add_argument("--empleados", type=int, help="Número real de empleados (se normaliza automáticamente)")
    parser.add_argument("--plan", choices=["esencial", "pro", "experto"], help="Plan específico")
    parser.add_argument("--listar-sectores", action="store_true", help="Lista todos los sectores disponibles")
    parser.add_argument("--desglose", action="store_true", help="Mostrar desglose de componentes")
    parser.add_argument("--json", action="store_true", help="Salida JSON (una línea) para consumir desde otros scripts")

    args = parser.parse_args()

    if args.json:
        tamano = args.tamano or (normalizar_tamano(args.empleados) if args.empleados else None)
        if not (args.sector and tamano and args.plan):
            print(_json.dumps({"error": "faltan --sector, --plan y --tamano/--empleados"}))
            sys.exit(1)
        r = calcular_precio(args.plan, args.sector, tamano)
        if "error" in r:
            print(_json.dumps({"error": r["error"]}, ensure_ascii=False))
            sys.exit(1)
        print(_json.dumps({
            "precio_final": r["precio_final"], "precio_mensual": r["precio_mensual"],
            "precio_atica": r["precio_atica"], "precio_mensual_atica": r["precio_mensual_atica"],
            "plan": r["plan"], "sector": r["sector"], "tamano": r["tamano"],
        }, ensure_ascii=False))
        sys.exit(0)

    if args.listar_sectores:
        print("\nSectores disponibles:")
        for i, s in enumerate(SECTORES.keys(), 1):
            base = SECTORES[s]["base"]
            print(f"  {i:2}. {s} (base: ${base:,} USD)")
        print()

    elif args.sector and (args.tamano or args.empleados):
        tamano = args.tamano
        if args.empleados:
            tamano = normalizar_tamano(args.empleados)
            print(f"  → {args.empleados} empleados → categoría '{tamano}'")

        if args.plan:
            r = calcular_precio(args.plan, args.sector, tamano)
            if "error" in r:
                print(f"\nError: {r['error']}")
            else:
                print(f"\n  Plan {r['plan']} — {r['sector']} — {r['tamano']} empleados")
                print(f"  Precio:         ${r['precio_final']:,} USD")
                print(f"  Mensual:        ${r['precio_mensual']:,} USD/mes")
                print(f"  Con ATICA −10%: ${r['precio_atica']:,} USD (${r['precio_mensual_atica']:,}/mes)")
                if args.desglose:
                    print(f"\n  Desglose:")
                    print(f"    Base sector:     ${r['desglose']['base']:,}")
                    print(f"    % empleados:     +{r['desglose']['pct_empleados']*100:.0f}%")
                    for nombre, pct in r['desglose']['componentes'].items():
                        print(f"    {nombre}: +{pct*100:.0f}%")
                    print(f"    Multiplicador:   ×{r['desglose']['multiplicador']}")
        else:
            calcular_todos_los_planes(args.sector, tamano)

    else:
        # Demo rápido: Industria manufacturera, 100 empleados
        print("\n─── DEMO ────────────────────────────────────────────────────")
        print("Uso: python calcular-precio.py --sector 'Industria manufacturera' --tamano 100")
        print("     python calcular-precio.py --sector 'Salud' --empleados 85 --plan pro --desglose")
        print("     python calcular-precio.py --listar-sectores")
        print("─────────────────────────────────────────────────────────────")
        calcular_todos_los_planes("Industria manufacturera", "100")
        calcular_todos_los_planes("Salud", "100")
        calcular_todos_los_planes("Emprendimientos", "10 o menos")
