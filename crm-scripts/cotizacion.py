#!/usr/bin/env python3
"""Envío de la cotización al cliente desde una página de confirmación.

Reusa la mecánica de seguimiento.py (firma HMAC, envío por Gmail, estilos de página).
El borrador del correo lo redacta la skill /cotizar y lo deja en el campo
`borradorCorreo` de la oportunidad; esta página lo muestra, deja editarlo, elegir
remitente y agregar copias, y solo envía al presionar el botón."""
from seguimiento import _esc, _pagina, REMITENTES

ASUNTO_BASE = "Cotización CarbonBox"


def asunto_cotizacion(empresa):
    return f"{ASUNTO_BASE} — {empresa}"


def cargar_opp_cotizacion(opp_id):
    from crm_lib import gql
    q = ("query($id: UUID!){ opportunities(first:1, filter:{id:{eq:$id}}) { edges { node { "
         "id name stage borradorCorreo "
         "linkCotizacion { primaryLinkUrl } "
         "pointOfContact { name { firstName } emails { primaryEmail } } "
         "company { name } } } } }")
    edges = gql(q, {"id": opp_id})["opportunities"]["edges"]
    return edges[0]["node"] if edges else None


def datos_cotizacion(opp):
    """(nombre, para, empresa, link_deck, borrador) — cadenas vacías si falta algo."""
    poc = opp.get("pointOfContact") or {}
    nombre = ((poc.get("name") or {}).get("firstName") or "").strip()
    para = ((poc.get("emails") or {}).get("primaryEmail") or "").strip()
    empresa = ((opp.get("company") or {}).get("name") or "").strip()
    link = ((opp.get("linkCotizacion") or {}).get("primaryLinkUrl") or "").strip()
    borrador = (opp.get("borradorCorreo") or "").strip()
    return nombre, para, empresa, link, borrador


def pagina_cotizacion(opp_id, sig, nombre, para, empresa, asunto, cuerpo, link_deck):
    inp = ("width:100%;padding:9px;margin:4px 0 12px;border:1px solid #d3d6f0;"
           "border-radius:8px;font-size:14px;font-family:inherit")
    opciones = "".join(f'<option value="{k}">{_esc(v)}</option>' for k, v in REMITENTES.items())
    cont = ("<h1>Enviar cotización</h1>"
            f"<p class=muted>Para: <b>{_esc(nombre)}</b> &lt;{_esc(para)}&gt; · "
            f"Empresa: <b>{_esc(empresa)}</b></p>"
            f"<p class=muted>Deck: <a href=\"{_esc(link_deck)}\">{_esc(link_deck)}</a></p>"
            "<form method=post action=\"/cotizacion/enviar\">"
            f"<input type=hidden name=opp value=\"{_esc(opp_id)}\">"
            f"<input type=hidden name=sig value=\"{_esc(sig)}\">"
            "<label class=muted>Enviar como</label>"
            f"<select name=remitente style=\"{inp}\">{opciones}</select>"
            "<label class=muted>Copia (CC) — separa con comas; opcional</label>"
            f"<input name=cc value=\"\" placeholder=\"otro@empresa.com, jefe@empresa.com\" style=\"{inp}\">"
            "<label class=muted>Asunto</label>"
            f"<input name=asunto value=\"{_esc(asunto)}\" style=\"{inp}\">"
            "<label class=muted>Mensaje — puedes editarlo antes de enviar</label>"
            f"<textarea name=cuerpo rows=10 style=\"{inp}\">{_esc(cuerpo)}</textarea>"
            "<div class=muted style=\"margin:0 0 14px\">Se firma automáticamente con la firma de "
            "CarbonBox. El link del deck va dentro del mensaje.</div>"
            "<button type=submit>Confirmar y enviar</button>"
            "<div class=muted style=\"margin-top:10px\">El correo solo se envía al presionar "
            "este botón.</div>"
            "</form>")
    return _pagina("Enviar cotización", cont)


def registrar_envio_cotizacion(opp_id, permalink):
    """Guarda el link del correo enviado, limpia el borrador y deja nota en la oportunidad."""
    from crm_lib import gql
    gql("mutation($id: UUID!, $d: OpportunityUpdateInput!){ updateOpportunity(id:$id, data:$d){ id } }",
        {"id": opp_id, "d": {"linkCorreoEnviado": {"primaryLinkUrl": permalink,
                                                   "primaryLinkLabel": "Correo enviado"},
                             "borradorCorreo": ""}})
    d = gql("mutation($data: NoteCreateInput!){ createNote(data:$data){ id } }",
            {"data": {"title": "📤 Cotización enviada",
                      "bodyV2": {"markdown": "Se envió la cotización al cliente.\n\n"
                                             f"[Ver el correo]({permalink})"}}})
    gql("mutation($data: NoteTargetCreateInput!){ createNoteTarget(data:$data){ id } }",
        {"data": {"noteId": d["createNote"]["id"], "targetOpportunityId": opp_id}})
