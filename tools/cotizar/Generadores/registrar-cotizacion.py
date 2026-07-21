#!/usr/bin/env python3
"""
Registra en el CRM (Twenty, crm.carbonbox.app) que se envió una cotización.

Busca o crea la Empresa + Oportunidad del cliente y la mueve a la etapa
"Propuesta enviada" (PROPUESTA_ENVIADA), con una nota con plan, precio y NIT.
Replica los patrones de crm-scripts/crm_lib.py y lead_intake.py del repo
carbonbox-crm (solo como referencia — este script vive en tools/cotizar,
NO modifica los scripts de infraestructura del CRM).

⚠️ REQUIERE UN TOKEN LOCAL — nunca lo pegues en el chat con Claude.
1. Genera un token de API en Twenty: crm.carbonbox.app → Configuración →
   API & Webhooks → API keys.
2. Guárdalo en un archivo `.env` en esta misma carpeta (Generadores/), así:
     TWENTY_API_TOKEN=el_token_aqui
3. Este archivo `.env` es local — no lo subas al repo (agrégalo a .gitignore
   si no está ya).

Uso:
    python3 registrar-cotizacion.py --cliente "Hotel Waya Guajira" \\
        --nit "900.123.456-7" --plan Pro --precio 4101 \\
        --servicio "Estimación de huella de carbono organizacional" \\
        --nota "Cotización enviada por correo el 16 de julio de 2026"

Nota: el mapeo de campos/mutaciones GraphQL sigue el patrón observado en
crm_lib.py y lead_intake.py del repo, pero no se ha probado contra la
instancia real de Twenty (requiere el token). Primera corrida: verifica
que la oportunidad y la nota queden bien en crm.carbonbox.app antes de
usarlo como parte del flujo habitual.
"""

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

CORE = "https://crm.carbonbox.app/graphql"
HERE = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(HERE, ".env")
TOKEN_FILE_ALT = os.path.join(HERE, "token crm.txt")  # formato simple: solo el token, sin prefijo


def cargar_token():
    tok = os.environ.get("TWENTY_API_TOKEN")
    if tok:
        return tok.strip()
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                if line.strip().startswith("TWENTY_API_TOKEN="):
                    return line.strip().split("=", 1)[1].strip()
    if os.path.exists(TOKEN_FILE_ALT):
        with open(TOKEN_FILE_ALT) as f:
            tok = f.read().strip()
        if tok:
            return tok
    sys.exit(
        "❌ No encontré el token de Twenty.\n"
        f"   Crea el archivo {ENV_FILE} con la línea:\n"
        "   TWENTY_API_TOKEN=tu_token_aqui\n"
        f"   (o un archivo {TOKEN_FILE_ALT} con solo el token)\n"
        "   Genera el token en crm.carbonbox.app → Configuración → API & Webhooks"
    )


def gql(query, variables=None):
    token = cargar_token()
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(CORE, data=body, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if out.get("errors"):
        raise RuntimeError(json.dumps(out["errors"], ensure_ascii=False)[:800])
    return out["data"]


def find_or_create_company(nombre):
    d = gql("""query($n: String!) { companies(filter:{name:{ilike:$n}}, first:1) {
        edges { node { id name } } } }""", {"n": nombre})
    if d["companies"]["edges"]:
        return d["companies"]["edges"][0]["node"]["id"]
    d = gql("""mutation($data: CompanyCreateInput!) { createCompany(data:$data) { id } }""",
            {"data": {"name": nombre}})
    return d["createCompany"]["id"]


def find_open_opportunity(company_id):
    """Busca una oportunidad abierta (no ganada/perdida) de esta empresa."""
    d = gql("""query($cid: UUID!) { opportunities(
        filter: { companyId: { eq: $cid },
                  stage: { in: ["LEAD_CAPTURADO","CALIFICACION_BANT","DEMO",
                                 "PILOTO_45D","PROPUESTA_ENVIADA","EN_NEGOCIACION",
                                 "RENOVACION","NURTURING"] } }, first: 1) {
        edges { node { id name stage } } } }""", {"cid": company_id})
    edges = d["opportunities"]["edges"]
    return edges[0]["node"] if edges else None


def crear_oportunidad(company_id, nombre_cliente, servicio, precio):
    odata = {"name": f"{nombre_cliente} — {servicio}", "stage": "PROPUESTA_ENVIADA",
              "companyId": company_id}
    if precio:
        odata["amount"] = {"amountMicros": int(round(precio * 1_000_000)), "currencyCode": "USD"}
    d = gql("""mutation($data: OpportunityCreateInput!) { createOpportunity(data:$data) { id } }""",
            {"data": odata})
    return d["createOpportunity"]["id"]


def mover_a_propuesta_enviada(opp_id, precio):
    data = {"stage": "PROPUESTA_ENVIADA"}
    if precio:
        data["amount"] = {"amountMicros": int(round(precio * 1_000_000)), "currencyCode": "USD"}
    gql("""mutation($id: UUID!, $data: OpportunityUpdateInput!) {
        updateOpportunity(id:$id, data:$data) { id } }""", {"id": opp_id, "data": data})


def agregar_nota(opp_id, texto):
    d = gql("""mutation($data: NoteCreateInput!) { createNote(data:$data) { id } }""",
            {"data": {"title": "Cotización enviada", "bodyV2": {"markdown": texto}}})
    note_id = d["createNote"]["id"]
    gql("""mutation($data: NoteTargetCreateInput!) { createNoteTarget(data:$data) { id } }""",
        {"data": {"noteId": note_id, "targetOpportunityId": opp_id}})


def registrar_cotizacion(cliente, nit, plan, precio, servicio, nota_extra=None):
    company_id = find_or_create_company(cliente)
    existente = find_open_opportunity(company_id)

    if existente:
        opp_id = existente["id"]
        mover_a_propuesta_enviada(opp_id, precio)
        accion = f"Oportunidad existente actualizada → Propuesta enviada ({existente['name']})"
    else:
        opp_id = crear_oportunidad(company_id, cliente, servicio, precio)
        accion = "Oportunidad nueva creada en Propuesta enviada"

    fecha = datetime.now(timezone.utc).astimezone().strftime("%d de %B de %Y")
    texto = (f"**Servicio:** {servicio}\n"
             f"**Plan:** {plan}\n"
             f"**NIT:** {nit}\n"
             + (f"**Precio:** ${precio:,.0f} USD\n" if precio else "")
             + f"**Fecha de envío:** {fecha}\n"
             + (f"\n{nota_extra}" if nota_extra else ""))
    agregar_nota(opp_id, texto)

    print(f"✅ {accion}")
    print(f"   Oportunidad: {opp_id}")
    print(f"   CRM: https://crm.carbonbox.app/object/opportunity/{opp_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Registra una cotización enviada en el CRM CarbonBox")
    parser.add_argument("--cliente", required=True, help="Nombre de la empresa cliente")
    parser.add_argument("--nit", required=True, help="NIT del cliente")
    parser.add_argument("--plan", required=True, help="Esencial / Pro / Experto")
    parser.add_argument("--precio", type=float, help="Precio final en USD")
    parser.add_argument("--servicio", default="Estimación de huella de carbono",
                        help="Descripción del servicio cotizado")
    parser.add_argument("--nota", help="Texto adicional para la nota del CRM")

    args = parser.parse_args()
    registrar_cotizacion(args.cliente, args.nit, args.plan, args.precio, args.servicio, args.nota)
