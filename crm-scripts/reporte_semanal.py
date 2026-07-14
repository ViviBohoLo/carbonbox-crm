#!/usr/bin/env python3
"""Reporte semanal del pipeline — lunes 8:00 am por cron.
Conteo/valor por etapa + leads sin contactar + negocios estancados, por email."""
import sys
sys.path.insert(0, "/root/crm-scripts")
from crm_lib import (ETAPAS, nombre_etapa, pesos, clasificar_riesgo,
                     get_all_opportunities, get_open_opportunities,
                     send_notification, now_utc)

ORDEN = ["LEAD_CAPTURADO", "CALIFICACION_BANT", "DEMO", "PILOTO_45D",
         "PROPUESTA_ENVIADA", "EN_NEGOCIACION", "CERRADO_GANADO",
         "RENOVACION", "NURTURING", "PERDIDO"]
CRM_URL = "https://crm.carbonbox.app"


def construir_reporte(opps_all, opps_open, ahora, link_fn=None):
    conteo, valor = {}, {}
    for o in opps_all:
        s = o["stage"]
        conteo[s] = conteo.get(s, 0) + 1
        micros = (o.get("amount") or {}).get("amountMicros") or 0
        valor[s] = valor.get(s, 0) + (int(micros) / 1_000_000 if micros else 0)

    leads, estancados = clasificar_riesgo(opps_open, ahora)
    total = sum(conteo.values())
    en_riesgo = len(leads) + len(estancados)

    L = ["**REPORTE SEMANAL DEL PIPELINE**", ahora.strftime("%d/%m/%Y"), ""]
    aten = f" · **{en_riesgo} necesitan atención esta semana**" if en_riesgo else ""
    L.append(f"{total} negocios en el funnel{aten}.")
    L += ["", "**── NEGOCIOS POR ETAPA ──**"]
    for s in ORDEN:
        if conteo.get(s):
            v = f" · {pesos(valor[s])}" if valor.get(s) else ""
            L.append(f"  {nombre_etapa(s)}: {conteo[s]}{v}")
    L.append(f"  Total: {total} negocios")

    if leads:
        L += ["", f"**── LEADS SIN PRIMER CONTACTO ({len(leads)}) ──**",
              "Un lead nuevo debe contactarse en la 1.ª hora; se enfría rápido."]
        for it in leads:
            L.append(f"  • **{it['nombre']}** — capturado hace {it['antiguedad']}")
        L.append("  → Contactar hoy por correo o llamada.")

    if estancados:
        L += ["", f"**── NEGOCIOS ESTANCADOS ({len(estancados)}) ──**",
              "Del más atrasado al menos. «Límite» = tiempo máximo en esa etapa sin avanzar."]
        for i, it in enumerate(estancados, 1):
            val = f"   {it['valor']}" if it['valor'] else ""
            L.append("")
            L.append(f" {i}. **{it['nombre']}**{val}")
            L.append(f"    {it['etapa']} hace {it['antiguedad']} (límite {it['limite']}).")
            if it['accion']:
                L.append(f"    → {it['accion']}")
            url = link_fn(it) if link_fn else None
            if url:
                L.append(f"    ✉️ [Enviar recordatorio]({url})")

    if not en_riesgo:
        L += ["", "✅ Sin negocios en riesgo esta semana."]

    L += ["", "**── METAS DEL MES ──**",
          "  25 MQL · 10 demos · 5-6 propuestas · 3-4 cierres",
          "", f"Abrir el CRM → {CRM_URL}"]
    return "\n".join(L)


if __name__ == "__main__":
    from seguimiento import firmar, secreto, tiene_plantilla
    ahora = now_utc()
    _sec = secreto()

    def _link(it):
        if not tiene_plantilla(it["stage"]):
            return None
        return f"{CRM_URL}/seguimiento?opp={it['id']}&sig={firmar(it['id'], _sec)}"

    body = construir_reporte(get_all_opportunities(), get_open_opportunities(), ahora, link_fn=_link)
    ok = send_notification(f"📊 Pipeline CarbonBox — semana del {ahora.strftime('%d/%m')}", body)
    print("reporte enviado" if ok else "reporte NO enviado")
    print(body)
