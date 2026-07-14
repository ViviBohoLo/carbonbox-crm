#!/usr/bin/env python3
"""Revisor de seguimientos del funnel CarbonBox.
Uso: vigia_sla.py [sla|renovacion|todo]  (default: todo)
- sla: crea tareas urgentes por negocios que pasaron el límite de su etapa (cron cada 3 h).
- renovacion: avisa hitos -90/-60/-30 de contratos ganados (cron 1 vez al día)."""
import sys
sys.path.insert(0, "/root/crm-scripts")
from crm_lib import (ETAPAS, nombre_etapa, antiguedad_texto, gql,
                     get_open_opportunities, get_renewal_candidates, get_leads,
                     find_open_task_by_title, create_urgent_task, send_notification,
                     now_utc, parse_dt, hito_a_disparar, load_renov_seen, save_renov_seen,
                     hito_agenda, load_agenda_seen, save_agenda_seen, google_access_token)
from seguimiento import firmar, secreto
from calendar_transcripts import correos_agendados

CRM_URL = "https://crm.carbonbox.app"
ACCION_HITO = {
    90: "Enviar **propuesta anticipada** de renovación (10% dto si renueva antes de -60 días).",
    60: "Enviar el **contrato** de renovación.",
    30: "**Llamada** + plan de fidelización.",
}


def revisar_sla(ahora):
    nuevos = []
    for opp in get_open_opportunities():
        if opp["stage"] == "LEAD_CAPTURADO":
            continue                       # los leads los maneja revisar_agenda
        etapa = ETAPAS.get(opp["stage"])
        if not etapa or not etapa["sla"]:
            continue
        entrada = parse_dt(opp.get("fechaEntradaEtapa")) or parse_dt(opp["createdAt"])
        if not entrada or (ahora - entrada) <= etapa["sla"]:
            continue
        nombre = opp["name"]
        antig = antiguedad_texto(entrada, ahora)
        limite = etapa["sla_txt"]
        title = f"🔴 Sin avanzar: {nombre} — {etapa['nombre']}"
        if find_open_task_by_title(title):
            continue
        create_urgent_task(
            title,
            f"**Lleva {antig} en {etapa['nombre']}** — el límite de esta etapa es "
            f"{limite}.\n\n**Acción:** {etapa['accion']}",
            opp["id"])
        nuevos.append(f"  • **{nombre}** — {etapa['nombre']} hace {antig} (límite {limite}).")
    return nuevos


def revisar_renovacion(ahora):
    nuevos = []
    seen = load_renov_seen()
    vivos = set()
    for opp in get_renewal_candidates():
        vence = parse_dt(opp.get("vencimientoContrato"))
        if not vence:
            continue
        oid = opp["id"]
        vivos.add(oid)
        dias = (vence.date() - ahora.date()).days
        hito, nuevos_vistos = hito_a_disparar(dias, seen.get(oid, []))
        seen[oid] = nuevos_vistos
        if hito is None:
            continue
        nombre = opp["name"]
        title = f"🔄 Renovación en {hito} días: {nombre}"
        if find_open_task_by_title(title):
            continue
        create_urgent_task(
            title,
            f"El contrato **vence en {dias} días** (hito -{hito}).\n\n"
            f"**Acción de este hito:** {ACCION_HITO[hito]}\n\n"
            "**Ruta completa:** -90 propuesta anticipada (10% dto si renueva antes de -60) · "
            "-60 enviar contrato · -30 llamada + plan de fidelización.",
            oid)
        nuevos.append(f"  • **{nombre}** — renovación hito -{hito} (vence en {dias} días).")
    seen = {k: v for k, v in seen.items() if k in vivos}
    save_renov_seen(seen)
    return nuevos


def _crear_nota(opp_id, titulo, cuerpo_md):
    d = gql("mutation($data: NoteCreateInput!){ createNote(data:$data){ id } }",
            {"data": {"title": titulo, "bodyV2": {"markdown": cuerpo_md}}})
    gql("mutation($data: NoteTargetCreateInput!){ createNoteTarget(data:$data){ id } }",
        {"data": {"noteId": d["createNote"]["id"], "targetOpportunityId": opp_id}})


def revisar_agenda(ahora):
    """Leads (LEAD_CAPTURADO) que no agendaron la llamada: día 3 y 6 crean tarea con
    enlace de recordatorio; al día 9 sin agendar se mueven solos a Nurturing.
    'Agendó' se detecta si el correo del lead aparece como invitado en el calendario."""
    nuevos = []
    try:
        agendados = correos_agendados(google_access_token())
    except Exception as ex:
        print(f"[agenda] no se pudo leer el calendario: {ex}", flush=True)
        return nuevos
    sec = secreto()
    seen = load_agenda_seen()
    vivos = set()
    for opp in get_leads():
        oid, nombre = opp["id"], opp["name"]
        poc = opp.get("pointOfContact") or {}
        email = ((poc.get("emails") or {}).get("primaryEmail") or "").lower().strip()
        if email and email in agendados:
            seen.pop(oid, None)          # ya agendó -> no molestar
            continue
        entrada = parse_dt(opp.get("fechaEntradaEtapa")) or parse_dt(opp["createdAt"])
        if not entrada:
            continue
        dias = (ahora - entrada).days
        if dias >= 9:
            gql("mutation($id: UUID!){ updateOpportunity(id:$id, data:{stage:\"NURTURING\"}){ id } }", {"id": oid})
            _crear_nota(oid, "🌱 Movido a Nurturing (no agendó)",
                        f"El lead **{nombre}** no agendó la llamada en 9 días. "
                        "Se movió a Nurturing automáticamente.")
            seen.pop(oid, None)
            nuevos.append(f"  • **{nombre}** — movido a Nurturing (no agendó en 9 días).")
            continue
        vivos.add(oid)
        ronda, nuevos_vistos = hito_agenda(dias, seen.get(oid, []))
        seen[oid] = nuevos_vistos
        if ronda is None:
            continue
        etiqueta = "1er aviso" if ronda == 3 else "2º aviso"
        title = f"🗓️ Lead sin agendar ({etiqueta}): {nombre}"
        if find_open_task_by_title(title):
            continue
        if email:
            link = f"{CRM_URL}/seguimiento?opp={oid}&sig={firmar(oid, sec)}"
            accion = ("**Acción:** contáctalo directamente (llamada/WhatsApp), o envíale el "
                      f"recordatorio de agenda con un clic:\n[Enviar recordatorio de agenda]({link})")
        else:
            accion = ("**Acción:** contáctalo directamente (llamada/WhatsApp). "
                      "Este lead no tiene correo en el CRM, así que no se le puede enviar recordatorio por email.")
        create_urgent_task(
            title,
            f"El lead **{nombre}** lleva {dias} días sin agendar la llamada de presentación.\n\n"
            f"{accion}\n\nSi al día 9 no agenda, pasa solo a Nurturing.",
            oid)
        nuevos.append(f"  • **{nombre}** — lead sin agendar, {etiqueta} ({dias} días).")
    seen = {k: v for k, v in seen.items() if k in vivos}
    save_agenda_seen(seen)
    return nuevos


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "todo"
    ahora = now_utc()
    nuevos = []
    if modo in ("todo", "sla"):
        nuevos += revisar_sla(ahora)
        nuevos += revisar_agenda(ahora)
    if modo in ("todo", "renovacion"):
        nuevos += revisar_renovacion(ahora)

    if nuevos:
        send_notification(
            f"🔴 CarbonBox: {len(nuevos)} negocio(s) necesitan acción",
            f"El Revisor de seguimientos revisó el pipeline y creó **{len(nuevos)} "
            "tarea(s) urgentes** para Viviana:\n\n" + "\n".join(nuevos)
            + f"\n\nLas tareas ya están en el CRM, cada una con su acción:\n{CRM_URL}")
        print(f"{len(nuevos)} alertas nuevas")
    else:
        print("sin novedades")
