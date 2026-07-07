#!/usr/bin/env python3
"""OPS one-off (2026-07-07): crea el campo booleano `suscritoMarketing` en Persona.
Metadata va con la API key (/root/.twenty_api_token) vía createOneField en /metadata."""
import json, urllib.request, sys
sys.path.insert(0, "/root/crm-scripts")
import crm_lib as c

META = "http://localhost:3000/metadata"
PERSON_OBJ = "16790c1d-680e-488c-8cef-a69feb631305"


def meta(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(META, data=body, headers={
        "Authorization": f"Bearer {c.token()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if out.get("errors"):
        raise RuntimeError(json.dumps(out["errors"], ensure_ascii=False)[:500])
    return out["data"]


d = meta("""
mutation($input: CreateOneFieldMetadataInput!) {
  createOneField(input: $input) { id name type }
}""", {"input": {"field": {
    "name": "suscritoMarketing",
    "label": "Suscrito a marketing",
    "description": "Recibe correos de marketing (guias, eventos). Consentimiento del contacto.",
    "type": "BOOLEAN",
    "icon": "IconMailStar",
    "objectMetadataId": PERSON_OBJ,
    "defaultValue": True,
}}})
print("Campo creado:", json.dumps(d["createOneField"], ensure_ascii=False))
