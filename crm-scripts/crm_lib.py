#!/usr/bin/env python3
"""Librería compartida de los scripts cron del CRM CarbonBox."""
import json, re, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta, date

CORE = "http://localhost:3000/graphql"
TOKEN_FILE = "/root/.twenty_api_token"
WORKSPACE_ID = "8f353725-f145-46c2-9e38-95fb89474339"
MEMBER_VIVIANA = "f38776b9-a83b-47c6-8d84-0b32a662ac84"
NOTIFIER_FILE = "/root/crm-scripts/notifier_workflow_id.txt"


def token():
    with open(TOKEN_FILE) as f:
        return f.read().strip()


def gql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(CORE, data=body, headers={
        "Authorization": f"Bearer {token()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if out.get("errors"):
        raise RuntimeError(json.dumps(out["errors"], ensure_ascii=False)[:400])
    return out["data"]


def now_utc():
    return datetime.now(timezone.utc)


def parse_dt(s):
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


# --- Origen único de etapas: nombre, límite (para el cálculo y para mostrar) y acción ---
# 'sla' es el timedelta para comparar; 'sla_txt' es el texto que se muestra (evita
# ambigüedades tipo 60 min == 1 h, 72 h == 3 días). Deben coincidir con la guía HTML.
ETAPAS = {
    "LEAD_CAPTURADO":    {"nombre": "Lead capturado",    "sla": timedelta(minutes=60), "sla_txt": "60 minutos",
                          "accion": "Contactar hoy por correo o llamada; un lead nuevo se enfría rápido."},
    "CALIFICACION_BANT": {"nombre": "Calificación BANT",  "sla": timedelta(hours=72),   "sla_txt": "72 horas",
                          "accion": "Intentar un último contacto; si no responde, pasar a Nurturing."},
    "DEMO":              {"nombre": "Demo",               "sla": None, "sla_txt": None, "accion": ""},   # a futuro
    "PILOTO_45D":        {"nombre": "Piloto 45d",         "sla": None, "sla_txt": None, "accion": ""},   # a futuro
    "PROPUESTA_ENVIADA": {"nombre": "Propuesta enviada",  "sla": timedelta(days=7),  "sla_txt": "7 días",
                          "accion": "Llamar: «¿Alcanzó a revisar la propuesta?». Si no responde, pasar a Nurturing."},
    "EN_NEGOCIACION":    {"nombre": "En negociación",     "sla": timedelta(days=21), "sla_txt": "21 días",
                          "accion": "Si no responde, pasar a Nurturing mensual y documentar."},
    "CERRADO_GANADO":    {"nombre": "Cerrado ganado",     "sla": None, "sla_txt": None, "accion": ""},
    "RENOVACION":        {"nombre": "Renovación",         "sla": None, "sla_txt": None, "accion": ""},
    "NURTURING":         {"nombre": "Nurturing",          "sla": None, "sla_txt": None, "accion": ""},
    "PERDIDO":           {"nombre": "Perdido",            "sla": None, "sla_txt": None, "accion": ""},
}


def nombre_etapa(stage):
    e = ETAPAS.get(stage)
    return e["nombre"] if e else stage


def pesos(v):
    return "$" + f"{int(round(v)):,}".replace(",", ".")


def antiguedad_texto(entrada, ahora):
    """Tiempo transcurrido, en la unidad más grande y con plural correcto:
    '159 días' / '1 día' / '5 horas' / '40 minutos'. Sin la palabra 'hace'."""
    seg = (ahora - entrada).total_seconds()
    if seg >= 86400:
        n = int(round(seg / 86400)); return f"{n} día" if n == 1 else f"{n} días"
    if seg >= 3600:
        n = int(round(seg / 3600)); return f"{n} hora" if n == 1 else f"{n} horas"
    n = int(round(seg / 60)); return f"{n} minuto" if n == 1 else f"{n} minutos"


def es_licitacion(opp):
    """True si la oportunidad es una licitación o estudio de mercado: procesos formales
    (TDR con fecha de cierre), NO seguimiento comercial.

    Acepta el nodo completo de la oportunidad (preferido: mira el campo etapaLicitacion)
    o solo el nombre (respaldo, para las que aún no se hayan marcado en el CRM)."""
    if isinstance(opp, dict):
        if opp.get("etapaLicitacion"):
            return True
        nombre = opp.get("name")
    else:
        nombre = opp
    n = (nombre or "").lower()
    return n.startswith("licitación") or n.startswith("licitacion") or "estudio de mercado" in n


def clasificar_riesgo(opps, ahora):
    """Separa las oportunidades vencidas en (leads_sin_contacto, negocios_estancados).
    Un item entra si su etapa tiene límite y ya lo superó. LEAD_CAPTURADO va a 'leads';
    el resto a 'estancados', ordenados del más atrasado al menos."""
    leads, estancados = [], []
    for o in opps:
        if es_licitacion(o):
            continue                      # tienen su propio bloque y sus propias fechas
        etapa = ETAPAS.get(o["stage"])
        if not etapa or not etapa["sla"]:
            continue
        entrada = parse_dt(o.get("fechaEntradaEtapa")) or parse_dt(o.get("createdAt"))
        if not entrada:
            continue
        atraso = (ahora - entrada).total_seconds() - etapa["sla"].total_seconds()
        if atraso <= 0:
            continue
        micros = (o.get("amount") or {}).get("amountMicros") or 0
        valor = int(micros) / 1_000_000 if micros else 0
        item = {
            "id": o["id"],
            "stage": o["stage"],
            "nombre": o["name"],
            "etapa": etapa["nombre"],
            "antiguedad": antiguedad_texto(entrada, ahora),
            "limite": etapa["sla_txt"],
            "valor": pesos(valor) if valor else "",
            "accion": etapa["accion"],
            "_orden": atraso,
        }
        (leads if o["stage"] == "LEAD_CAPTURADO" else estancados).append(item)
    estancados.sort(key=lambda x: x["_orden"], reverse=True)
    leads.sort(key=lambda x: x["_orden"], reverse=True)
    return leads, estancados


def get_open_opportunities():
    d = gql("""query { opportunities(first: 200,
        filter: { stage: { in: ["LEAD_CAPTURADO", "CALIFICACION_BANT", "DEMO",
                                 "PILOTO_45D", "PROPUESTA_ENVIADA", "EN_NEGOCIACION",
                                 "RENOVACION"] } }) {
      edges { node { id name stage fechaEntradaEtapa createdAt updatedAt
        vencimientoContrato etapaLicitacion fechaCierreLicitacion
        amount { amountMicros } } } } }""")
    return [e["node"] for e in d["opportunities"]["edges"]]


def get_all_opportunities():
    d = gql("""query { opportunities(first: 500) {
      edges { node { id name stage amount { amountMicros } createdAt } } } }""")
    return [e["node"] for e in d["opportunities"]["edges"]]


def get_renewal_candidates():
    """Oportunidades cuyo contrato puede necesitar renovación: contratos
    ganados (CERRADO_GANADO). RENOVACION queda excluido: si ya está en esa
    etapa, alguien lo está gestionando activamente."""
    d = gql("""query { opportunities(first: 300,
        filter: { stage: { in: ["CERRADO_GANADO"] } }) {
      edges { node { id name stage vencimientoContrato } } } }""")
    return [e["node"] for e in d["opportunities"]["edges"]]


def get_leads():
    """Leads abiertos (LEAD_CAPTURADO) con su contacto, para el recordatorio de agenda."""
    d = gql("""query { opportunities(first: 200,
        filter: { stage: { in: ["LEAD_CAPTURADO"] } }) {
      edges { node { id name fechaEntradaEtapa createdAt
        company { name }
        pointOfContact { name { firstName } emails { primaryEmail } } } } } }""")
    return [e["node"] for e in d["opportunities"]["edges"]]


# --- Hitos de renovación (ruta del funnel: -90 / -60 / -30 días) ---
HITOS = [90, 60, 30]
RENOV_SEEN_FILE = "/root/crm-scripts/renovacion_seen.json"


def load_renov_seen():
    try:
        with open(RENOV_SEEN_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_renov_seen(d):
    with open(RENOV_SEEN_FILE, "w") as f:
        json.dump(d, f)


def hito_a_disparar(dias, ya_vistos, hitos=None):
    """Decide si hoy toca avisar de un hito para algo que ocurre en `dias` días,
    dados los hitos ya avisados `ya_vistos`.

    `hitos` por defecto son los de renovación (HITOS = [90, 60, 30]); las
    licitaciones pasan LICITACION_HITOS = [15, 7, 3, 1].

    Devuelve (hito_o_None, lista_actualizada_de_vistos).
    - Dispara SOLO el hito más urgente ya alcanzado (min de los alcanzados),
      una única vez por hito (idempotente entre corridas y a prueba de apagones).
    - Marca como vistos todos los hitos alcanzados (los saltados por apagón no
      se re-disparan tarde).
    - Fuera de ventana (dias > el hito mayor) resetea: se re-arma para el
      próximo ciclo (contrato renovado, licitación prorrogada…)."""
    hitos = HITOS if hitos is None else hitos
    vistos = [int(x) for x in ya_vistos]
    alcanzados = [h for h in hitos if dias <= h]
    if not alcanzados:
        return None, []
    nuevos = sorted(set(vistos) | set(alcanzados), reverse=True)
    target = min(alcanzados)
    if target in vistos:
        return None, nuevos
    return target, nuevos


# --- Licitaciones: hitos de aviso antes del cierre y estado ---
LICITACION_HITOS = [15, 7, 3, 1]
LICITACION_SEEN_FILE = "/root/crm-scripts/licitacion_seen.json"
ETAPAS_LICITACION = {"ESTUDIO_MERCADO": "Estudio de mercado", "ABIERTA": "Abierta",
                     "EVALUACION": "En evaluación", "ADJUDICADA": "Adjudicada",
                     "NO_ADJUDICADA": "No adjudicada"}


def load_licitacion_seen():
    try:
        with open(LICITACION_SEEN_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_licitacion_seen(d):
    with open(LICITACION_SEEN_FILE, "w") as f:
        json.dump(d, f)


def fecha_cierre(opp):
    """date de fechaCierreLicitacion, o None si no está cargada."""
    f = opp.get("fechaCierreLicitacion")
    if not f:
        return None
    return date(int(f[:4]), int(f[5:7]), int(f[8:10]))


def clasificar_licitaciones(opps, hoy):
    """(abiertas, en_evaluacion, sin_clasificar) para el reporte.

    Las abiertas van de la más urgente a la menos; las que no tienen fecha de cierre
    cargada quedan al final. `sin_clasificar` son las que se detectan como licitación
    (por el nombre) pero aún no tienen etapa marcada: si no se listaran, quedarían
    invisibles — fuera de 'estancados' y fuera de este bloque."""
    abiertas, evaluacion, sin_clasificar = [], [], []
    for o in opps:
        et = o.get("etapaLicitacion")
        if not et:
            if es_licitacion(o):
                sin_clasificar.append({"nombre": o["name"]})
            continue
        if et == "ABIERTA":
            f = fecha_cierre(o)
            abiertas.append({
                "id": o["id"], "nombre": o["name"],
                "dias": (f - hoy).days if f else None,
                "fecha": f.strftime("%d/%m") if f else None,
                "sin_fecha": f is None,
            })
        elif et == "EVALUACION":
            evaluacion.append({"nombre": o["name"]})
    abiertas.sort(key=lambda x: (x["dias"] is None, x["dias"] if x["dias"] is not None else 0))
    return abiertas, evaluacion, sin_clasificar


# --- Recordatorio de agenda: leads que no agendaron la llamada (día 3 y 6) ---
AGENDA_HITOS = [3, 6]
AGENDA_SEEN_FILE = "/root/crm-scripts/agenda_seen.json"
AGENDA_NURTURING_DIAS = 9


def load_agenda_seen():
    try:
        with open(AGENDA_SEEN_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_agenda_seen(d):
    with open(AGENDA_SEEN_FILE, "w") as f:
        json.dump(d, f)


def hito_agenda(dias, ya_vistos):
    """Recordatorio de agenda para un lead con `dias` días sin agendar.
    Dispara el hito alcanzado más bajo que aún no se ha avisado (3, luego 6),
    una vez cada uno. Devuelve (hito_o_None, lista_actualizada_de_vistos)."""
    vistos = [int(x) for x in ya_vistos]
    for h in AGENDA_HITOS:
        if dias >= h and h not in vistos:
            return h, sorted(set(vistos) | {h})
    return None, vistos


def find_open_task_by_title(title):
    d = gql("""query($t: String!) { tasks(first: 5,
        filter: { title: { eq: $t }, status: { in: ["TODO", "IN_PROGRESS"] } }) {
      edges { node { id } } } }""", {"t": title})
    return len(d["tasks"]["edges"]) > 0


def create_urgent_task(title, body_md, opp_id):
    d = gql("""mutation($data: TaskCreateInput!) { createTask(data: $data) { id } }""",
            {"data": {"title": title, "status": "TODO",
                      "dueAt": now_utc().isoformat(),
                      "assigneeId": MEMBER_VIVIANA,
                      "bodyV2": {"markdown": body_md}}})
    task_id = d["createTask"]["id"]
    gql("""mutation($data: TaskTargetCreateInput!) { createTaskTarget(data: $data) { id } }""",
        {"data": {"taskId": task_id, "targetOpportunityId": opp_id}})
    return task_id


def cuerpo_html(body):
    """El Notificador de Twenty trata el body como HTML → los saltos de línea (\\n)
    se colapsan y todo queda en una sola línea. Se envuelve el texto plano en <pre>
    (conserva saltos y espacios) y se escapan los caracteres especiales de HTML."""
    esc = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    esc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc)   # **negrita** -> <strong>
    esc = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', esc)  # [texto](url) -> enlace
    return ('<pre style="font-family:ui-monospace,Consolas,monospace;'
            'white-space:pre-wrap;font-size:13px;line-height:1.5;margin:0">'
            + esc + "</pre>")


def send_notification(subject, body, html=False):
    """Envía email vía el workflow Notificador (webhook->Gmail).
    Por defecto el body es texto plano y se formatea con cuerpo_html() (conserva
    saltos de línea y aplica **negritas**). Pasa html=True si el body YA es HTML."""
    try:
        with open(NOTIFIER_FILE) as f:
            wf_id = f.read().strip()
    except FileNotFoundError:
        print("[warn] notificador no configurado; sin email")
        return False
    url = f"http://localhost:3000/webhooks/workflows/{WORKSPACE_ID}/{wf_id}"
    cuerpo = body if html else cuerpo_html(body)
    payload = json.dumps({"subject": subject, "body": cuerpo}).encode()
    req = urllib.request.Request(url, data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status < 300


def google_access_token(refresh_file="/root/.gtasks_token", env_file="/root/twenty/.env"):
    """Access token Bearer para las APIs de Google (Tasks/Calendar/Drive), a partir del
    refresh token compartido y el client 'CarbonBox CRM Web' de /root/twenty/.env."""
    cid = secret = None
    for line in open(env_file):
        if line.startswith("AUTH_GOOGLE_CLIENT_ID="):
            cid = line.split("=", 1)[1].strip()
        if line.startswith("AUTH_GOOGLE_CLIENT_SECRET="):
            secret = line.split("=", 1)[1].strip()
    rt = open(refresh_file).read().strip()
    data = urllib.parse.urlencode({
        "client_id": cid, "client_secret": secret,
        "refresh_token": rt, "grant_type": "refresh_token"}).encode()
    out = json.load(urllib.request.urlopen(
        urllib.request.Request("https://oauth2.googleapis.com/token", data=data), timeout=30))
    return out["access_token"]
