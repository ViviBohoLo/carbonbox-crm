#!/usr/bin/env python3
"""Reporte semanal del pipeline — lunes 8:00 am por cron.
Resumen por etapa + negocios en riesgo, enviado por email vía el Notificador."""
import sys
sys.path.insert(0, "/root/crm-scripts")
from datetime import timedelta
from crm_lib import (get_all_opportunities, get_open_opportunities,
                     send_notification, now_utc, parse_dt)

ORDEN = ["LEAD_CAPTURADO", "CALIFICACION_BANT", "DEMO", "PILOTO_45D",
         "PROPUESTA_ENVIADA", "EN_NEGOCIACION", "CERRADO_GANADO",
         "RENOVACION", "NURTURING", "PERDIDO"]
NOMBRES = {
    "LEAD_CAPTURADO": "① Lead Capturado", "CALIFICACION_BANT": "② Calificación BANT",
    "DEMO": "③ Demo", "PILOTO_45D": "③b Piloto 45d", "PROPUESTA_ENVIADA": "④ Propuesta Enviada",
    "EN_NEGOCIACION": "⑤ En Negociación", "CERRADO_GANADO": "⑥ Cerrado Ganado",
    "RENOVACION": "⑦ Renovación", "NURTURING": "Nurturing", "PERDIDO": "Perdido",
}
SLAS_H = {"LEAD_CAPTURADO": 1, "CALIFICACION_BANT": 72, "DEMO": 168,
          "PROPUESTA_ENVIADA": 168, "EN_NEGOCIACION": 504}

opps = get_all_opportunities()
ahora = now_utc()

conteo = {}
valor = {}
for o in opps:
    s = o["stage"]
    conteo[s] = conteo.get(s, 0) + 1
    micros = (o.get("amount") or {}).get("amountMicros") or 0
    valor[s] = valor.get(s, 0) + (int(micros) / 1_000_000 if micros else 0)

lineas = [f"REPORTE SEMANAL DEL PIPELINE — {ahora.strftime('%d/%m/%Y')}", ""]
lineas.append("Negocios por etapa:")
total = 0
for s in ORDEN:
    if conteo.get(s):
        v = f" (${valor[s]:,.0f})" if valor.get(s) else ""
        lineas.append(f"  {NOMBRES[s]}: {conteo[s]}{v}")
        total += conteo[s]
lineas.append(f"  TOTAL: {total} negocios")

# en riesgo (SLA vencido ahora mismo)
riesgo = []
for o in get_open_opportunities():
    s = o["stage"]
    if s in SLAS_H:
        entrada = parse_dt(o.get("fechaEntradaEtapa")) or parse_dt(o["createdAt"])
        if entrada:
            horas = (ahora - entrada).total_seconds() / 3600
            if horas > SLAS_H[s]:
                riesgo.append(f"  🔴 {o['name']} — {NOMBRES.get(s, s)}, {round(horas/24, 1)} días sin avanzar")

lineas.append("")
if riesgo:
    lineas.append(f"⚠️ En riesgo ({len(riesgo)}):")
    lineas.extend(riesgo)
else:
    lineas.append("✅ Sin negocios en riesgo de SLA.")

lineas += ["", "Metas del funnel: 25 MQL/mes · 10 demos/mes · 5-6 propuestas/mes · 3-4 cierres/mes",
           "CRM: http://localhost:3000"]

body = "\n".join(lineas)
ok = send_notification(f"📊 Pipeline CarbonBox — semana del {ahora.strftime('%d/%m')}", body)
print("reporte enviado" if ok else "reporte NO enviado (notificador no configurado)")
print(body)
