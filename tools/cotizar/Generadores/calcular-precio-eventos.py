#!/usr/bin/env python3
"""
Calculadora de precios CarbonBox — Huella de Carbono de Eventos
Replica exactamente la lógica de la calculadora de eventos del sitio web carbonbox.app
(pestaña "Eventos" de /precios).

Uso:
    python calcular-precio-eventos.py
    → Demo rápido

    python calcular-precio-eventos.py --tipo-evento "Congresos y Reuniones empresariales" --asistentes 100 --plan pro
    → Calcula precio específico

    python calcular-precio-eventos.py --tipo-evento "Congresos y Reuniones empresariales" --num-asistentes 80
    → Normaliza 80 asistentes reales a la categoría más cercana y muestra los 3 planes

    python calcular-precio-eventos.py --listar-tipos
    → Lista los tipos de evento disponibles
"""

import argparse

# ─────────────────────────────────────────────────────────────────────────────
# BASE DE DATOS DE PRECIOS (replicada del script Wix de carbonbox.app — pestaña Eventos)
# ─────────────────────────────────────────────────────────────────────────────

TIPOS_EVENTO = {
    "Congresos y Reuniones empresariales": {
        "50 o menos": 246, "100": 308, "500": 369, "1.000": 431,
        "10.000": 566, "25.000": 726, "50.000": 898, "75.000": 1058,
        "100.000": 1485, "150.000": 1919, "200.000": 2337, "> 200.000": None
    },
    "Festivales, Conciertos y Eventos Masivos": {
        "50 o menos": 492, "100": 554, "500": 615, "1.000": 640,
        "10.000": 677, "25.000": 738, "50.000": 923, "75.000": 1082,
        "100.000": 1169, "150.000": 1230, "200.000": 1353, "> 200.000": None
    }
}

EXPERTO_DEDICADO = {
    "Experto Full": {
        "50 o menos": 0.35, "100": 0.35, "500": 0.4, "1.000": 0.4,
        "10.000": 0.5, "25.000": 0.5, "50.000": 0.6, "75.000": 0.6,
        "100.000": 0.6, "150.000": 0.6, "200.000": 0.65
    },
    "Experto 96hr (8hr/mes)": {
        "50 o menos": 0.3, "100": 0.3, "500": 0.3, "1.000": 0.4,
        "10.000": 0.4, "25.000": 0.4, "50.000": 0.5, "75.000": 0.5,
        "100.000": 0.5, "150.000": 0.5, "200.000": 0.55
    },
    "Experto 48hr (4hr/mes)": {
        "50 o menos": 0.2, "100": 0.2, "500": 0.2, "1.000": 0.3,
        "10.000": 0.3, "25.000": 0.3, "50.000": 0.4, "75.000": 0.4,
        "100.000": 0.4, "150.000": 0.4, "200.000": 0.45
    },
    "Experto 24hr (2hr/mes)": {
        "50 o menos": 0.1, "100": 0.1, "500": 0.1, "1.000": 0.2,
        "10.000": 0.2, "25.000": 0.2, "50.000": 0.3, "75.000": 0.3,
        "100.000": 0.3, "150.000": 0.3, "200.000": 0.35
    }
}

TIPO_REPORTE = {
    "Auditable ISO-GHG": {
        "50 o menos": 0.35, "100": 0.35, "500": 0.4, "1.000": 0.4,
        "10.000": 0.45, "25.000": 0.45, "50.000": 0.5, "75.000": 0.5,
        "100.000": 0.55, "150.000": 0.55, "200.000": 0.55
    },
    "Auditable GHG": {
        "50 o menos": 0.25, "100": 0.3, "500": 0.3, "1.000": 0.35,
        "10.000": 0.35, "25.000": 0.4, "50.000": 0.4, "75.000": 0.45,
        "100.000": 0.45, "150.000": 0.5, "200.000": 0.5
    },
    "Informe técnico": {
        "50 o menos": 0.2, "100": 0.2, "500": 0.25, "1.000": 0.25,
        "10.000": 0.25, "25.000": 0.3, "50.000": 0.3, "75.000": 0.35,
        "100.000": 0.35, "150.000": 0.35, "200.000": 0.35
    },
    "Informe ejecutivo": {
        "50 o menos": 0.1, "100": 0.1, "500": 0.1, "1.000": 0.15,
        "10.000": 0.15, "25.000": 0.15, "50.000": 0.2, "75.000": 0.2,
        "100.000": 0.25, "150.000": 0.3, "200.000": 0.3
    }
}

CAPACITACION = {
    "Autogestionada": {
        "50 o menos": 0.2, "100": 0.2, "500": 0.25, "1.000": 0.25,
        "10.000": 0.25, "25.000": 0.3, "50.000": 0.3, "75.000": 0.3,
        "100.000": 0.3, "150.000": 0.3, "200.000": 0.3
    },
    "Capacitación": {
        "50 o menos": 0.25, "100": 0.25, "500": 0.3, "1.000": 0.3,
        "10.000": 0.3, "25.000": 0.35, "50.000": 0.35, "75.000": 0.4,
        "100.000": 0.45, "150.000": 0.45, "200.000": 0.45
    },
    "Capacitación & taller de aprendizaje": {
        "50 o menos": 0.3, "100": 0.3, "500": 0.35, "1.000": 0.35,
        "10.000": 0.35, "25.000": 0.4, "50.000": 0.4, "75.000": 0.4,
        "100.000": 0.5, "150.000": 0.55, "200.000": 0.55
    }
}

VALIDACION_DATOS = {
    "Validación de datos": {
        "50 o menos": 0.1, "100": 0.13, "500": 0.2, "1.000": 0.2,
        "10.000": 0.2, "25.000": 0.2, "50.000": 0.25, "75.000": 0.25,
        "100.000": 0.25, "150.000": 0.3, "200.000": 0.35
    },
    "Validación de datos & soportes": {
        "50 o menos": 0.15, "100": 0.2, "500": 0.23, "1.000": 0.23,
        "10.000": 0.25, "25.000": 0.3, "50.000": 0.35, "75.000": 0.4,
        "100.000": 0.45, "150.000": 0.5, "200.000": 0.55
    }
}

GESTION_REDUCCIONES = {
    "Recomendaciones de reducción para el evento": {
        "50 o menos": 0.1, "100": 0.2, "500": 0.2, "1.000": 0.2,
        "10.000": 0.2, "25.000": 0.25, "50.000": 0.25, "75.000": 0.25,
        "100.000": 0.25, "150.000": 0.25, "200.000": 0.25
    },
    "Recomendaciones de reducción personalizadas": {
        "50 o menos": 0.23, "100": 0.23, "500": 0.28, "1.000": 0.28,
        "10.000": 0.3, "25.000": 0.3, "50.000": 0.3, "75.000": 0.3,
        "100.000": 0.35, "150.000": 0.35, "200.000": 0.4
    },
    "Proyecciones, análisis y plan de reducción": {
        "50 o menos": 0.3, "100": 0.3, "500": 0.35, "1.000": 0.35,
        "10.000": 0.35, "25.000": 0.35, "50.000": 0.4, "75.000": 0.4,
        "100.000": 0.45, "150.000": 0.45, "200.000": 0.45
    }
}

COMUNICACION_CARBONO_NEUTRO = {
    "50 o menos": 0.2, "100": 0.2, "500": 0.3, "1.000": 0.3,
    "10.000": 0.4, "25.000": 0.4, "50.000": 0.45, "75.000": 0.45,
    "100.000": 0.45, "150.000": 0.5, "200.000": 0.5
}

CERTIFICACION_EVENTO = {
    "50 o menos": 0.3, "100": 0.3, "500": 0.4, "1.000": 0.4,
    "10.000": 0.5, "25.000": 0.5, "50.000": 0.55, "75.000": 0.55,
    "100.000": 0.55, "150.000": 0.6, "200.000": 0.6
}

ACOMPANAMIENTO_AUDITORIA = {
    "50 o menos": 0.2, "100": 0.2, "500": 0.3, "1.000": 0.3,
    "10.000": 0.4, "25.000": 0.4, "50.000": 0.45, "75.000": 0.45,
    "100.000": 0.45, "150.000": 0.5, "200.000": 0.55
}

# Categorías válidas de número de asistentes, en el mismo orden que la web
ASISTENTES_VALIDOS = [
    "50 o menos", "100", "500", "1.000", "10.000", "25.000",
    "50.000", "75.000", "100.000", "150.000", "200.000", "> 200.000"
]


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL DE CÁLCULO
# ─────────────────────────────────────────────────────────────────────────────

def calcular_precio_evento(plan: str, tipo_evento: str, num_asistentes: str) -> dict:
    """
    Calcula el precio de huella de carbono de EVENTO según plan, tipo de evento
    y categoría de número de asistentes.
    Replica exactamente calcularPrecioEvento() del script Wix de carbonbox.app.

    Args:
        plan: "esencial", "pro" o "experto"
        tipo_evento: "Congresos y Reuniones empresariales" o
                     "Festivales, Conciertos y Eventos Masivos"
        num_asistentes: categoría (ver ASISTENTES_VALIDOS)

    Returns:
        dict con precio_final, precio_mensual, precio_atica, desglose
        (o {"error": ...} / {"contactar": True} si aplica)
    """
    tipo_data = TIPOS_EVENTO.get(tipo_evento)
    if not tipo_data:
        tipos_disponibles = "\n  ".join(TIPOS_EVENTO.keys())
        return {"error": f"Tipo de evento no encontrado: '{tipo_evento}'\nTipos disponibles:\n  {tipos_disponibles}"}

    if num_asistentes == "> 200.000" or tipo_data.get(num_asistentes) is None:
        return {"contactar": True, "mensaje": "Contáctanos para una cotización personalizada."}

    precio_base = tipo_data[num_asistentes]
    plan = plan.lower()

    if plan == "esencial":
        componentes = {
            "Informe ejecutivo": TIPO_REPORTE["Informe ejecutivo"].get(num_asistentes, 0),
            "Capacitación autogestionada": CAPACITACION["Autogestionada"].get(num_asistentes, 0),
            "Recomendaciones de reducción para el evento": GESTION_REDUCCIONES["Recomendaciones de reducción para el evento"].get(num_asistentes, 0),
        }

    elif plan == "pro":
        componentes = {
            "Capacitación del equipo organizador": CAPACITACION["Capacitación"].get(num_asistentes, 0),
            "Informe técnico": TIPO_REPORTE["Informe técnico"].get(num_asistentes, 0),
            "Experto 48hr (4hr/mes)": EXPERTO_DEDICADO["Experto 48hr (4hr/mes)"].get(num_asistentes, 0),
            "Validación de datos": VALIDACION_DATOS["Validación de datos"].get(num_asistentes, 0),
            "Recomendaciones personalizadas": GESTION_REDUCCIONES["Recomendaciones de reducción personalizadas"].get(num_asistentes, 0),
            "Comunicación carbono neutro": COMUNICACION_CARBONO_NEUTRO.get(num_asistentes, 0),
        }

    elif plan == "experto":
        componentes = {
            "Capacitación & taller de aprendizaje": CAPACITACION["Capacitación & taller de aprendizaje"].get(num_asistentes, 0),
            "Reporte auditable ISO-GHG": TIPO_REPORTE["Auditable ISO-GHG"].get(num_asistentes, 0),
            "Experto Full": EXPERTO_DEDICADO["Experto Full"].get(num_asistentes, 0),
            "Validación de datos & soportes": VALIDACION_DATOS["Validación de datos & soportes"].get(num_asistentes, 0),
            "Proyecciones & plan de reducción": GESTION_REDUCCIONES["Proyecciones, análisis y plan de reducción"].get(num_asistentes, 0),
            "Acompañamiento auditoría": ACOMPANAMIENTO_AUDITORIA.get(num_asistentes, 0),
            "Certificación del evento": CERTIFICACION_EVENTO.get(num_asistentes, 0),
        }

    else:
        return {"error": f"Plan no reconocido: '{plan}'. Usar: esencial, pro, experto"}

    adicional_pct = sum(componentes.values())
    precio_final = round(precio_base * (1 + adicional_pct))
    precio_mensual = round(precio_final / 12)
    precio_atica = round(precio_final * 0.90)
    precio_mensual_atica = round(precio_atica / 12)

    return {
        "plan": plan.capitalize(),
        "tipo_evento": tipo_evento,
        "num_asistentes": num_asistentes,
        "precio_final": precio_final,
        "precio_mensual": precio_mensual,
        "precio_atica": precio_atica,
        "precio_mensual_atica": precio_mensual_atica,
        "desglose": {
            "base": precio_base,
            "componentes": componentes,
            "adicional_total": adicional_pct,
            "multiplicador": round(1 + adicional_pct, 4)
        }
    }


def normalizar_asistentes(num_asistentes_real: int) -> str:
    """
    Convierte un número real de asistentes a la categoría más cercana
    (redondeando hacia arriba, igual que el dropdown de la web).
    """
    if num_asistentes_real <= 50:
        return "50 o menos"
    elif num_asistentes_real <= 100:
        return "100"
    elif num_asistentes_real <= 500:
        return "500"
    elif num_asistentes_real <= 1000:
        return "1.000"
    elif num_asistentes_real <= 10000:
        return "10.000"
    elif num_asistentes_real <= 25000:
        return "25.000"
    elif num_asistentes_real <= 50000:
        return "50.000"
    elif num_asistentes_real <= 75000:
        return "75.000"
    elif num_asistentes_real <= 100000:
        return "100.000"
    elif num_asistentes_real <= 150000:
        return "150.000"
    elif num_asistentes_real <= 200000:
        return "200.000"
    else:
        return "> 200.000"


def calcular_todos_los_planes(tipo_evento: str, num_asistentes: str) -> None:
    """Imprime tabla con los 3 planes para un tipo de evento y categoría de asistentes dados."""
    print(f"\n{'═'*70}")
    print(f"  CarbonBox — Calculadora de Precios HC de EVENTO")
    print(f"{'═'*70}")
    print(f"  Tipo de evento : {tipo_evento}")
    print(f"  Asistentes     : {num_asistentes}")
    print(f"{'─'*70}")
    print(f"  {'Plan':<12} {'Precio USD':>12} {'Mensual':>10} {'Con ATICA (−10%)':>18}")
    print(f"{'─'*70}")

    for plan in ["esencial", "pro", "experto"]:
        r = calcular_precio_evento(plan, tipo_evento, num_asistentes)
        if r.get("contactar"):
            print(f"  {plan:<12} {r['mensaje']}")
        elif "error" in r:
            print(f"  {plan:<12} {r['error']}")
        else:
            print(f"  {r['plan']:<12} ${r['precio_final']:>10,} USD   ${r['precio_mensual']:>6,}/mes   ${r['precio_atica']:>8,} USD")

    print(f"{'═'*70}\n")


# ─────────────────────────────────────────────────────────────────────────────
# INTERFAZ DE LÍNEA DE COMANDOS
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calculadora de precios CarbonBox — HC de Eventos"
    )
    parser.add_argument("--tipo-evento", help="Congresos y Reuniones empresariales | Festivales, Conciertos y Eventos Masivos")
    parser.add_argument("--asistentes", help="Categoría de asistentes (ej: '100', '500', '10.000')")
    parser.add_argument("--num-asistentes", type=int, help="Número real de asistentes (se normaliza automáticamente)")
    parser.add_argument("--plan", choices=["esencial", "pro", "experto"], help="Plan específico")
    parser.add_argument("--listar-tipos", action="store_true", help="Lista los tipos de evento disponibles")
    parser.add_argument("--desglose", action="store_true", help="Mostrar desglose de componentes")

    args = parser.parse_args()

    if args.listar_tipos:
        print("\nTipos de evento disponibles:")
        for i, t in enumerate(TIPOS_EVENTO.keys(), 1):
            print(f"  {i}. {t}")
        print()

    elif args.tipo_evento and (args.asistentes or args.num_asistentes):
        asistentes = args.asistentes
        if args.num_asistentes:
            asistentes = normalizar_asistentes(args.num_asistentes)
            print(f"  → {args.num_asistentes} asistentes → categoría '{asistentes}'")

        if args.plan:
            r = calcular_precio_evento(args.plan, args.tipo_evento, asistentes)
            if r.get("contactar"):
                print(f"\n  {r['mensaje']}")
            elif "error" in r:
                print(f"\nError: {r['error']}")
            else:
                print(f"\n  Plan {r['plan']} — {r['tipo_evento']} — {r['num_asistentes']} asistentes")
                print(f"  Precio:         ${r['precio_final']:,} USD")
                print(f"  Mensual:        ${r['precio_mensual']:,} USD/mes")
                print(f"  Con ATICA −10%: ${r['precio_atica']:,} USD (${r['precio_mensual_atica']:,}/mes)")
                if args.desglose:
                    print(f"\n  Desglose:")
                    print(f"    Precio base:     ${r['desglose']['base']:,}")
                    for nombre, pct in r['desglose']['componentes'].items():
                        print(f"    {nombre}: +{pct*100:.0f}%")
                    print(f"    Multiplicador:   ×{r['desglose']['multiplicador']}")
        else:
            calcular_todos_los_planes(args.tipo_evento, asistentes)

    else:
        print("\n─── DEMO ────────────────────────────────────────────────────────────")
        print("Uso: python calcular-precio-eventos.py --tipo-evento 'Congresos y Reuniones empresariales' --asistentes 100")
        print("     python calcular-precio-eventos.py --tipo-evento 'Congresos y Reuniones empresariales' --num-asistentes 80 --plan pro --desglose")
        print("     python calcular-precio-eventos.py --listar-tipos")
        print("────────────────────────────────────────────────────────────────────")
        calcular_todos_los_planes("Congresos y Reuniones empresariales", "100")
        calcular_todos_los_planes("Festivales, Conciertos y Eventos Masivos", "1.000")
