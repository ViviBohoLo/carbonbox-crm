#!/usr/bin/env python3
"""Librería compartida de los scripts cron del CRM CarbonBox."""
import json, urllib.request, urllib.parse
from datetime import datetime, timezone

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


def get_open_opportunities():
    d = gql("""query { opportunities(first: 200,
        filter: { stage: { in: ["LEAD_CAPTURADO", "CALIFICACION_BANT", "DEMO",
                                 "PILOTO_45D", "PROPUESTA_ENVIADA", "EN_NEGOCIACION",
                                 "RENOVACION"] } }) {
      edges { node { id name stage fechaEntradaEtapa createdAt updatedAt
        vencimientoContrato amount { amountMicros } } } } }""")
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


def hito_a_disparar(dias, ya_vistos):
    """Decide si hoy toca avisar de un hito de renovación para un contrato
    que vence en `dias` días, dados los hitos ya avisados `ya_vistos`.

    Devuelve (hito_o_None, lista_actualizada_de_vistos).
    - Dispara SOLO el hito más urgente ya alcanzado (min de los alcanzados),
      una única vez por hito (idempotente entre corridas y a prueba de apagones).
    - Marca como vistos todos los hitos alcanzados (los saltados por apagón no
      se re-disparan tarde).
    - Fuera de ventana (dias > 90) resetea: contrato renovado/empujado a futuro
      → se re-arma para el próximo ciclo."""
    vistos = [int(x) for x in ya_vistos]
    alcanzados = [h for h in HITOS if dias <= h]
    if not alcanzados:
        return None, []
    nuevos = sorted(set(vistos) | set(alcanzados), reverse=True)
    target = min(alcanzados)
    if target in vistos:
        return None, nuevos
    return target, nuevos


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


def send_notification(subject, body):
    """Envía email vía el workflow Notificador (webhook->Gmail)."""
    try:
        with open(NOTIFIER_FILE) as f:
            wf_id = f.read().strip()
    except FileNotFoundError:
        print("[warn] notificador no configurado; sin email")
        return False
    url = f"http://localhost:3000/webhooks/workflows/{WORKSPACE_ID}/{wf_id}"
    payload = json.dumps({"subject": subject, "body": body}).encode()
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
