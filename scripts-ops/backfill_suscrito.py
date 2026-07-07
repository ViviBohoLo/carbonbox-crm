#!/usr/bin/env python3
"""OPS one-off (2026-07-07): marca suscritoMarketing=true en todos los contactos
existentes (agregar un campo con default NO rellena registros viejos). Paginado por
cursor, con pausa por el rate limit (100 req/min) y reintento. Idempotente."""
import sys, time
sys.path.insert(0, "/root/crm-scripts")
import crm_lib as c


def update_person(pid):
    for intento in range(4):
        try:
            c.gql("""mutation($id: UUID!, $data: PersonUpdateInput!) {
                updatePerson(id: $id, data: $data) { id } }""",
                  {"id": pid, "data": {"suscritoMarketing": True}})
            return True
        except RuntimeError as ex:
            if "LIMIT_REACHED" in str(ex) or "rate" in str(ex).lower():
                time.sleep(2 * (intento + 1)); continue
            raise
    return False


cursor = None
total = 0
saltados = 0
while True:
    after = f', after: "{cursor}"' if cursor else ""
    d = c.gql("""query { people(first: 60%s) {
        pageInfo { hasNextPage endCursor }
        edges { node { id suscritoMarketing } } } }""" % after)
    for e in d["people"]["edges"]:
        n = e["node"]
        if n.get("suscritoMarketing") is True:
            saltados += 1
            continue
        if update_person(n["id"]):
            total += 1
        time.sleep(0.72)
    pi = d["people"]["pageInfo"]
    if not pi["hasNextPage"]:
        break
    cursor = pi["endCursor"]
print(f"Actualizados: {total}  (ya estaban: {saltados})")
