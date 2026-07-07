#!/usr/bin/env python3
"""Vigía SLA del funnel CarbonBox — corre cada 30 min por cron.
Compara el tiempo en etapa contra el SLA del funnel y crea tareas urgentes
(sin duplicar). Si hay vencimientos nuevos, envía email de alerta."""
import sys
sys.path.insert(0, "/root/crm-scripts")
from datetime import timedelta
from crm_lib import (get_open_opportunities, get_renewal_candidates,
                     find_open_task_by_title, create_urgent_task, send_notification,
                     now_utc, parse_dt, hito_a_disparar, load_renov_seen, save_renov_seen)

# SLA por etapa (del documento Funnel de Conversión KIMSA/CarbonBox)
SLAS = {
    "LEAD_CAPTURADO":    (timedelta(minutes=60), "60 minutos", "Contactar YA por email o llamada. Un lead nuevo se enfría rápido."),
    "CALIFICACION_BANT": (timedelta(hours=72),   "72 horas",   "Intentar un último contacto. Si no responde: mover a Nurturing."),
    "DEMO":              (timedelta(days=7),     "7 días",     "Reagendar demo en 24h o mover a Nurturing si cancela 2 veces."),
    "PROPUESTA_ENVIADA": (timedelta(days=7),     "7 días",     "Llamar directamente: '¿Tuvo oportunidad de revisar la propuesta?'"),
    "EN_NEGOCIACION":    (timedelta(days=21),    "21 días",    "Si no responde: mover a Nurturing mensual y documentar."),
}

# Acción por hito de renovación (ruta del funnel)
ACCION_HITO = {
    90: "Enviar **propuesta anticipada** de renovación (10% dto si renueva antes de -60 días).",
    60: "Enviar el **contrato** de renovación.",
    30: "**Llamada** + plan de fidelización.",
}

nuevos = []
ahora = now_utc()

# 1) SLA de permanencia en etapa (oportunidades abiertas)
for opp in get_open_opportunities():
    stage = opp["stage"]
    nombre = opp["name"]

    if stage in SLAS:
        sla, sla_txt, accion = SLAS[stage]
        entrada = parse_dt(opp.get("fechaEntradaEtapa")) or parse_dt(opp["createdAt"])
        if entrada and (ahora - entrada) > sla:
            title = f"🔴 SLA VENCIDO [{stage}]: {nombre}"
            if not find_open_task_by_title(title):
                horas = round((ahora - entrada).total_seconds() / 3600, 1)
                create_urgent_task(
                    title,
                    f"**SLA de la etapa:** {sla_txt} — lleva **{horas}h** sin avanzar.\n\n"
                    f"**Acción:** {accion}",
                    opp["id"])
                nuevos.append(f"• {nombre} — {stage} vencido ({horas}h, SLA {sla_txt})")

# 2) Renovación: contratos ganados, avisa en los hitos -90/-60/-30 (una vez c/u)
seen = load_renov_seen()
vivos = set()
for opp in get_renewal_candidates():
    vence = parse_dt(opp.get("vencimientoContrato"))
    if not vence:
        continue
    oid = opp["id"]
    vivos.add(oid)
    # vencimientoContrato es un campo date (naive) → comparar por fecha
    dias = (vence.date() - ahora.date()).days
    hito, nuevos_vistos = hito_a_disparar(dias, seen.get(oid, []))
    seen[oid] = nuevos_vistos
    if hito is not None:
        nombre = opp["name"]
        title = f"🔄 RENOVACIÓN -{hito}d: {nombre}"
        if not find_open_task_by_title(title):
            create_urgent_task(
                title,
                f"El contrato **vence en {dias} días** (hito -{hito}).\n\n"
                f"**Acción de este hito:** {ACCION_HITO[hito]}\n\n"
                "**Ruta completa:** -90 propuesta anticipada (10% dto si renueva antes de -60) · "
                "-60 enviar contrato · -30 llamada + plan de fidelización.",
                oid)
            nuevos.append(f"• {nombre} — renovación hito -{hito} (vence en {dias} días)")

# Poda: olvida contratos que ya no son candidatos (cerrados-perdidos, borrados)
seen = {k: v for k, v in seen.items() if k in vivos}
save_renov_seen(seen)

if nuevos:
    send_notification(
        f"🔴 CRM CarbonBox: {len(nuevos)} alerta(s) del funnel",
        "El vigía del funnel encontró estos vencimientos y ya creó las tareas en el CRM:\n\n"
        + "\n".join(nuevos)
        + "\n\nEntra a http://localhost:3000 para gestionarlos.")
    print(f"{len(nuevos)} alertas nuevas")
else:
    print("sin vencimientos nuevos")
