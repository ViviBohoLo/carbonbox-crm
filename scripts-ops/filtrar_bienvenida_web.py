#!/usr/bin/env python3
"""OPS one-off (2026-07-07): agrega la condición `fuenteLead IS WEB` al FILTER step del
workflow de bienvenida, para que la bienvenida automática ("agenda tu asesoría") solo
dispare con leads del formulario web comercial (no webinar/evento/importados).

Editar workflows exige TOKEN DE USUARIO (UserAuthGuard, expira 30 min), NO la API key.
Obtenerlo en el navegador con sesión del CRM:
  JSON.parse(localStorage.getItem('tokenPairState')).accessOrWorkspaceAgnosticToken.token
Guardarlo en el VPS: `umask 077; printf '%s' '<TOKEN>' > /tmp/user_token`

Uso (en el VPS):
  python3 filtrar_bienvenida_web.py           # crea draft, agrega filtro, imprime DRAFT_ID
  python3 filtrar_bienvenida_web.py --activate <DRAFT_ID>   # activa (tras probar)

Probar SIN activar: runWorkflowVersion con payload {properties:{after:{...,fuenteLead}}}
a una dirección propia; verificar en workflowRuns.state.stepInfos que WEB->matchesFilter
True (SEND_EMAIL SUCCESS) y WEBINAR->False (STOPPED/SKIPPED). Ver twenty-workflow-api.
"""
import json, urllib.request, uuid, sys

TOKEN = open("/tmp/user_token").read().strip()
CORE = "http://localhost:3000/graphql"
WF = "5a4c0efa-d69a-41e9-8edc-3c2782f3510e"          # workflow bienvenida
VER_ACTIVA = "523b1309-5fd5-4962-b7fe-e7bec7b5e6a7"  # versión activa de origen
GROUP = "e795c924-7e71-4651-b6e9-977463bcbebc"       # grupo AND del FILTER step


def gql(q, v=None):
    body = json.dumps({"query": q, "variables": v or {}}).encode()
    r = urllib.request.Request(CORE, data=body, headers={
        "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=30) as x:
        out = json.load(x)
    if out.get("errors"):
        raise RuntimeError(json.dumps(out["errors"], ensure_ascii=False)[:600])
    return out["data"]


def activate(draft):
    d = gql('mutation{ activateWorkflowVersion(workflowVersionId:"%s") }' % draft)
    print("activado:", d)


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--activate":
        activate(sys.argv[2]); return

    # 1) draft desde la versión activa
    d = gql("""mutation($i: CreateDraftFromWorkflowVersionInput!) {
      createDraftFromWorkflowVersion(input: $i) { id } }""",
            {"i": {"workflowId": WF, "workflowVersionIdToCopy": VER_ACTIVA}})
    draft = d["createDraftFromWorkflowVersion"]["id"]

    # 2) leer el FILTER step del draft (query por filtro; workflowVersion(id:) NO existe)
    d = gql("""query($id: UUID!){ workflowVersions(first:1, filter:{id:{eq:$id}}){
        edges{ node{ steps } } } }""", {"id": draft})
    filt = next(s for s in d["workflowVersions"]["edges"][0]["node"]["steps"]
                if s["type"] == "FILTER")

    # 3) agregar fuenteLead IS WEB (match EXACTO; NO CONTAINS: WEBINAR contiene WEB)
    sfs = filt["settings"]["input"]["stepFilters"]
    if not any("fuenteLead" in (f.get("stepOutputKey") or "") for f in sfs):
        sfs.append({"id": str(uuid.uuid4()), "type": "text", "value": "WEB",
                    "operand": "IS",
                    "stepOutputKey": "{{trigger.properties.after.fuenteLead}}",
                    "stepFilterGroupId": GROUP})

    # 4) guardar el step completo
    gql("""mutation($i: UpdateWorkflowVersionStepInput!) {
      updateWorkflowVersionStep(input: $i) { id } }""",
        {"i": {"workflowVersionId": draft, "step": filt}})
    print("DRAFT_ID=" + draft + "  (probar con runWorkflowVersion; luego --activate)")


if __name__ == "__main__":
    main()
