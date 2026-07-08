#!/usr/bin/env python3
"""Sincroniza en dos vías las tareas del CRM (asignadas a Viviana) con Google Tasks
(lista "Llamada Lead-CMR"). Cron cada 10 min. Ver spec/plan 2026-07-07-google-tasks-sync.

- CRM -> Google: tareas abiertas de Viviana aparecen como Google Tasks con la ficha de
  la persona (para poder llamar) y su fecha de vencimiento (solo fecha; la API descarta
  la hora).
- Google -> CRM: marcar hecha en el celular -> la tarea del CRM queda DONE.
- Completar/borrar en el CRM -> se completa la Google Task.
- Conflicto: "completada gana".
Estado del mapeo: /root/crm-scripts/gtasks_map.json (crmTaskId -> googleTaskId)."""
import json, os, sys, urllib.request, urllib.error
sys.path.insert(0, "/root/crm-scripts")
import crm_lib as c

LISTA = "YUpOX0VGanZ2SE90YnpyVA"                   # lista "Llamada Lead-CMR"
BASE = "https://tasks.googleapis.com/tasks/v1"
MEMBER = "f38776b9-a83b-47c6-8d84-0b32a662ac84"    # Viviana (assignee)
MAP_FILE = "/root/crm-scripts/gtasks_map.json"


# ---------- Google Tasks API ----------
def gt_access_token():
    return c.google_access_token()


def _api(at, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Authorization": "Bearer " + at,
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        txt = r.read()
    return json.loads(txt) if txt else {}


def gt_list_tasks(at):
    out = _api(at, "GET", f"/lists/{LISTA}/tasks?showCompleted=true&showHidden=true&maxResults=100")
    return out.get("items", [])


def gt_create(at, title, notes, due):
    body = {"title": title, "notes": notes}
    if due:
        body["due"] = due
    return _api(at, "POST", f"/lists/{LISTA}/tasks", body)["id"]


def gt_patch(at, gid, campos):
    _api(at, "PATCH", f"/lists/{LISTA}/tasks/{gid}", campos)


def gt_complete(at, gid):
    _api(at, "PATCH", f"/lists/{LISTA}/tasks/{gid}", {"status": "completed"})


# ---------- Lectura del CRM ----------
def _due(dueAt):
    """dueAt ISO -> due de Google (solo fecha; la API descarta la hora)."""
    return dueAt[:10] + "T00:00:00.000Z" if dueAt else ""


def _notas_de_opp(opp):
    """Ficha de la persona de la oportunidad (para poder llamar)."""
    if not opp:
        return ""
    p = opp.get("pointOfContact") or {}
    nm = p.get("name") or {}
    nombre = " ".join(x for x in [nm.get("firstName"), nm.get("lastName")] if x)
    ph = p.get("phones") or {}
    tel = ((ph.get("primaryPhoneCallingCode") or "") + ph["primaryPhoneNumber"]
           if ph.get("primaryPhoneNumber") else "")
    correo = (p.get("emails") or {}).get("primaryEmail")
    pares = [("Nombre", nombre), ("Empresa", (opp.get("company") or {}).get("name")),
             ("Teléfono", tel), ("Correo", correo), ("Cargo", p.get("jobTitle"))]
    return "\n".join(f"{etq}: {val}" for etq, val in pares if val)


def _fetch_opps(opp_ids):
    """{oppId: nodo} con la persona de contacto. Query aparte porque a través del morph
    `targetOpportunity` de un taskTarget, Twenty NO resuelve el pointOfContact anidado."""
    if not opp_ids:
        return {}
    d = c.gql("""query($ids: [UUID!]){ opportunities(first:200, filter:{id:{in:$ids}}) {
        edges { node { id name company { name }
          pointOfContact { name{firstName lastName} jobTitle
            emails{primaryEmail} phones{primaryPhoneNumber primaryPhoneCallingCode} } } } } }""",
        {"ids": list(opp_ids)})
    return {e["node"]["id"]: e["node"] for e in d["opportunities"]["edges"]}


def _opp_id_de_tarea(node):
    for tt in (node.get("taskTargets") or {}).get("edges") or []:
        oid = tt["node"].get("targetOpportunityId")
        if oid:
            return oid
    return None


def crm_tareas_abiertas():
    """{crmId: {'title','notes','due'}} de las tareas ABIERTAS de Viviana."""
    d = c.gql("""query($m: UUID!){ tasks(first:100, filter:{assigneeId:{eq:$m},
        status:{in:["TODO","IN_PROGRESS"]}}) { edges { node { id title dueAt
        taskTargets { edges { node { targetOpportunityId } } } } } } }""", {"m": MEMBER})
    tasks = d["tasks"]["edges"]
    opps = _fetch_opps({_opp_id_de_tarea(e["node"]) for e in tasks} - {None})
    out = {}
    for e in tasks:
        n = e["node"]
        opp = opps.get(_opp_id_de_tarea(n))
        out[n["id"]] = {"title": n["title"], "notes": _notas_de_opp(opp), "due": _due(n.get("dueAt"))}
    return out


# ---------- Reconciliación pura ----------
def plan_sync(crm_tasks, google_by_id, mapping):
    """Decide las acciones sin tocar nada. Ver docstring del módulo.
    Devuelve (acciones, nuevo_mapping)."""
    acciones = []
    nuevo = dict(mapping)
    crm_ids = set(crm_tasks)
    for cid, t in crm_tasks.items():
        gid = mapping.get(cid)
        gt = google_by_id.get(gid) if gid else None
        if gt is None:                                    # nueva, o su Google Task ya no existe
            acciones.append({"op": "create", "crm": cid, "data": t})
        elif gt.get("status") == "completed":             # la marcaste hecha en el celular
            acciones.append({"op": "complete_crm", "crm": cid})
            nuevo.pop(cid, None)
        elif (gt.get("title"), gt.get("notes"), gt.get("due")) != (t["title"], t["notes"], t["due"]):
            acciones.append({"op": "update", "g": gid, "data": t})   # cambió en el CRM
    for cid, gid in mapping.items():                      # mapeadas que ya no están abiertas
        if cid not in crm_ids:
            gt = google_by_id.get(gid)
            if gt is not None and gt.get("status") != "completed":
                acciones.append({"op": "complete_google", "g": gid})
            nuevo.pop(cid, None)
    return acciones, nuevo


# ---------- Estado + main ----------
def load_map():
    try:
        return json.load(open(MAP_FILE))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_map(m):
    json.dump(m, open(MAP_FILE, "w"))


def main():
    at = gt_access_token()
    crm_tasks = crm_tareas_abiertas()
    google_by_id = {t["id"]: t for t in gt_list_tasks(at)}
    mapping = load_map()
    acciones, nuevo = plan_sync(crm_tasks, google_by_id, mapping)
    for a in acciones:
        if a["op"] == "create":
            t = a["data"]
            nuevo[a["crm"]] = gt_create(at, t["title"], t["notes"], t["due"])
        elif a["op"] == "update":
            t = a["data"]
            campos = {"title": t["title"], "notes": t["notes"]}
            if t["due"]:
                campos["due"] = t["due"]
            gt_patch(at, a["g"], campos)
        elif a["op"] == "complete_google":
            gt_complete(at, a["g"])
        elif a["op"] == "complete_crm":
            c.gql("""mutation($id: UUID!){ updateTask(id:$id, data:{status:"DONE"}){ id } }""",
                  {"id": a["crm"]})
    save_map(nuevo)
    print(f"sync: {len(acciones)} acciones, {len(nuevo)} tareas mapeadas")


if __name__ == "__main__":
    main()
