#!/usr/bin/env python3
"""Solo mira los envíos del formulario en HubSpot, sin crear nada."""
import json, urllib.request
from datetime import datetime, timezone

FORM_GUID = "64b92eab-d7b8-4d6e-b381-881adf692a4d"
URL = f"https://api.hubapi.com/form-integrations/v1/submissions/forms/{FORM_GUID}?limit=50"
TK = open("/root/.hubspot_token").read().strip()

req = urllib.request.Request(URL, headers={"Authorization": f"Bearer {TK}"})
with urllib.request.urlopen(req, timeout=30) as r:
    data = json.load(r)

subs = data.get("results", [])
print(f"envíos visibles: {len(subs)}")
for s in subs[:20]:
    ts = datetime.fromtimestamp(s.get("submittedAt", 0) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    email = next((v.get("value") for v in s.get("values", [])
                  if v.get("name", "").lower() in ("email", "correo")), "?")
    empresa = next((v.get("value") for v in s.get("values", [])
                    if v.get("name", "").lower() in ("company", "empresa")), "")
    print(f"  {ts}  {email}  {empresa}")
if data.get("paging"):
    print("(hay más páginas)")
