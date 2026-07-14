#!/usr/bin/env python3
"""Correo de seguimiento con un clic (Fase 3).
Firma HMAC de los enlaces, plantillas por etapa y envío por Gmail API (como Viviana).
Las funciones puras (firmar/valida/plantilla) se prueban en test_seguimiento.py."""
import base64, hmac, hashlib, json, urllib.request
from email.message import EmailMessage

SECRETO_FILE = "/root/.seguimiento_secret"
REMITENTE = "Viviana Bohórquez <viviana.bohorquez@carbonbox.app>"

FIRMA_VIVIANA = (
    '<br><br>—<br><b>Viviana Bohórquez</b><br>CarbonBox · '
    '<a href="mailto:info@carbonbox.app">info@carbonbox.app</a><br>'
    '<a href="https://www.carbonbox.app">www.carbonbox.app</a> · '
    '<a href="https://wa.me/573208675567">WhatsApp</a>')

# Solo las etapas "estancables" tienen recordatorio.
PLANTILLAS = {
    "PROPUESTA_ENVIADA": (
        "Sobre la propuesta de CarbonBox",
        "Hola {nombre}, ¿alcanzaste a revisar la propuesta que te compartimos para "
        "{empresa}? Quedo atenta a cualquier duda o ajuste para ayudarte a avanzar."),
    "EN_NEGOCIACION": (
        "¿Cómo vamos con {negocio}?",
        "Hola {nombre}, ¿cómo vas con la decisión sobre {negocio}? Con gusto reviso "
        "contigo cualquier detalle o ajuste que necesites."),
    "LEAD_CAPTURADO": (
        "¿Agendamos una llamada?",
        "Hola {nombre}, gracias por tu interés en CarbonBox. Nos encantaría conocer los "
        "retos de {empresa} en huella de carbono y contarte cómo podemos ayudarte. "
        "¿Agendamos una llamada corta? Elige el horario que mejor te quede aquí: "
        "https://calendar.app.google/Ede9nmxveoahb5by8"),
}


def aplica_limite_semana(stage):
    """El límite de 1/semana aplica a los recordatorios de negocios estancados,
    NO al recordatorio de agenda (leads), cuya cadencia la controla el Revisor."""
    return stage in ("PROPUESTA_ENVIADA", "EN_NEGOCIACION")


def secreto(path=SECRETO_FILE):
    with open(path) as f:
        return f.read().strip()


def firmar(opp_id, secreto):
    return hmac.new(secreto.encode(), opp_id.encode(), hashlib.sha256).hexdigest()


def valida(opp_id, sig, secreto):
    return hmac.compare_digest(firmar(opp_id, secreto), sig or "")


def tiene_plantilla(stage):
    return stage in PLANTILLAS


def plantilla(stage, nombre, empresa, negocio):
    """Devuelve (asunto, cuerpo_texto) o None si la etapa no tiene recordatorio."""
    t = PLANTILLAS.get(stage)
    if not t:
        return None
    asunto, cuerpo = t
    ctx = {"nombre": nombre or "", "empresa": empresa or "", "negocio": negocio or ""}
    return asunto.format(**ctx), cuerpo.format(**ctx)


def cuerpo_email_html(cuerpo_texto):
    esc = _esc(cuerpo_texto).replace("\n", "<br>")
    return "<p>" + esc + "</p><p>Un abrazo,</p>" + FIRMA_VIVIANA


def enviar_gmail(access_token, para, asunto, html, texto="", remitente=REMITENTE):
    """Envía un correo (HTML + texto plano) por la Gmail API. Devuelve el id del mensaje.
    Usa EmailMessage para codificar bien las cabeceras con acentos (si no, Gmail
    ignora el alias del remitente y cae al correo por defecto)."""
    msg = EmailMessage()
    msg["To"] = para
    msg["From"] = remitente
    msg["Subject"] = asunto
    msg.set_content(texto or "Abre este correo en un cliente que muestre HTML.")
    msg.add_alternative(html, subtype="html")
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    body = json.dumps({"raw": raw}).encode()
    req = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=body, headers={"Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r).get("id")


# --- Datos de la oportunidad + estado (usan gql; import diferido para no acoplar) ---
def cargar_opp(opp_id):
    from crm_lib import gql
    q = ("query($id: UUID!){ opportunities(first:1, filter:{id:{eq:$id}}) { edges { node { "
         "id name stage ultimoSeguimiento "
         "pointOfContact { name { firstName lastName } emails { primaryEmail } } "
         "company { name } } } } }")
    edges = gql(q, {"id": opp_id})["opportunities"]["edges"]
    return edges[0]["node"] if edges else None


def datos_contacto(opp):
    """(nombre_pila, email, empresa) a partir del nodo de oportunidad."""
    poc = opp.get("pointOfContact") or {}
    nombre = ((poc.get("name") or {}).get("firstName") or "").strip()
    email = ((poc.get("emails") or {}).get("primaryEmail") or "").strip()
    empresa = ((opp.get("company") or {}).get("name") or "").strip()
    return nombre, email, empresa


def dias_desde(fecha_iso, hoy):
    """Días enteros entre una fecha ISO (o None) y hoy (date). None si no hay fecha."""
    if not fecha_iso:
        return None
    from datetime import date
    f = fecha_iso[:10]
    return (hoy - date(int(f[:4]), int(f[5:7]), int(f[8:10]))).days


def registrar_envio(opp_id, cuando_iso, para):
    from crm_lib import gql
    fecha = cuando_iso[:10]  # el campo ultimoSeguimiento es DATE -> 'YYYY-MM-DD'
    gql("mutation($id: UUID!, $d: DateTime!){ updateOpportunity(id:$id, data:{ultimoSeguimiento:$d}){ id } }",
        {"id": opp_id, "d": fecha})
    d = gql("mutation($data: NoteCreateInput!){ createNote(data:$data){ id } }",
            {"data": {"title": "✉️ Recordatorio de seguimiento enviado",
                      "bodyV2": {"markdown": f"Se envió el correo de recordatorio a **{para}**."}}})
    gql("mutation($data: NoteTargetCreateInput!){ createNoteTarget(data:$data){ id } }",
        {"data": {"noteId": d["createNote"]["id"], "targetOpportunityId": opp_id}})


# --- Páginas HTML (sobrias; se pulen después) ---
def _esc(s):
    return (str(s if s is not None else "").replace("&", "&amp;")
            .replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


_FONTS = "https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap"


def _pagina(titulo, contenido):
    return (
        "<!doctype html><html lang=es><head><meta charset=utf-8>"
        "<meta name=viewport content=\"width=device-width, initial-scale=1\">"
        f"<title>{_esc(titulo)} · CarbonBox</title>"
        "<link rel=preconnect href=\"https://fonts.googleapis.com\">"
        f"<link href=\"{_FONTS}\" rel=stylesheet>"
        "<style>"
        ":root{--primary:#1620a4;--primary-deep:#0d1578;--accent:#2f6b4a;--ink:#0f1535;"
        "--ink2:#4a526e;--ink3:#7a82a0;--bg:#f7f8fc;--line:#e6e8f2;--soft:#ecedfb}"
        "*{box-sizing:border-box}"
        "body{margin:0;background:var(--bg);color:var(--ink);padding:34px 16px;"
        "font-family:'Poppins',-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;"
        "font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased}"
        ".card{max-width:600px;margin:0 auto;background:#fff;border:1px solid var(--line);"
        "border-radius:16px;overflow:hidden;box-shadow:0 14px 34px rgba(22,32,164,.10)}"
        ".hd{background:linear-gradient(135deg,var(--primary) 0%,#2a35c9 60%,var(--accent) 155%);"
        "color:#fff;padding:22px 28px}"
        ".hd .brand{font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;opacity:.85;font-weight:500}"
        ".hd h1{margin:5px 0 0;font-size:21px;font-weight:600;letter-spacing:-.01em}"
        ".bd{padding:24px 28px}"
        ".bd p{margin:0 0 12px}"
        ".meta{color:var(--ink3);font-size:13.5px;margin:0 0 18px!important}.meta b{color:var(--ink2)}"
        "label{display:block;font-size:12px;font-weight:600;color:var(--primary);"
        "text-transform:uppercase;letter-spacing:.05em;margin:16px 0 5px}"
        "input,textarea{width:100%;padding:11px 13px;border:1px solid var(--line);border-radius:10px;"
        "font-size:14.5px;font-family:inherit;color:var(--ink);background:#fcfcfe}"
        "input:focus,textarea:focus{outline:none;border-color:var(--primary);box-shadow:0 0 0 3px var(--soft)}"
        "textarea{resize:vertical;line-height:1.55}"
        ".hint{color:var(--ink3);font-size:12.5px;margin:8px 0 0}"
        "button{margin-top:18px;background:var(--primary);color:#fff;border:0;border-radius:10px;"
        "padding:13px 26px;font-size:15px;font-weight:600;font-family:inherit;cursor:pointer;transition:background .15s}"
        "button:hover{background:var(--primary-deep)}"
        ".ico{width:54px;height:54px;border-radius:50%;display:flex;align-items:center;justify-content:center;"
        "font-size:26px;font-weight:700;margin:0 0 10px}"
        ".ico.ok{background:#e8f1ec;color:var(--accent)}.ico.info{background:var(--soft);color:var(--primary)}"
        ".ico.error{background:#f7e4e3;color:#c0453f}"
        ".foot{text-align:center;color:var(--ink3);font-size:12px;margin:16px auto 0;max-width:600px}"
        "</style></head><body>"
        f"<div class=card>{contenido}</div>"
        "<p class=foot>CarbonBox · CRM comercial</p>"
        "</body></html>")


def pagina_confirmacion(opp_id, sig, nombre, para, empresa, negocio, asunto, cuerpo):
    c = ("<div class=hd><div class=brand>Recordatorio de seguimiento</div>"
         "<h1>Revisa y envía</h1></div>"
         "<div class=bd>"
         f"<p class=meta>Para <b>{_esc(nombre)}</b> &lt;{_esc(para)}&gt;<br>"
         f"Negocio: <b>{_esc(negocio)}</b></p>"
         "<form method=post action=\"/seguimiento/enviar\">"
         f"<input type=hidden name=opp value=\"{_esc(opp_id)}\">"
         f"<input type=hidden name=sig value=\"{_esc(sig)}\">"
         "<label>Asunto</label>"
         f"<input name=asunto value=\"{_esc(asunto)}\">"
         "<label>Mensaje</label>"
         f"<textarea name=cuerpo rows=6>{_esc(cuerpo)}</textarea>"
         "<p class=hint>Puedes editar el texto antes de enviar. Se firma automáticamente "
         "como Viviana Bohórquez · CarbonBox.</p>"
         "<button type=submit>Confirmar y enviar</button>"
         "<p class=hint>El correo solo se envía al presionar este botón.</p>"
         "</form></div>")
    return _pagina("Enviar recordatorio", c)


def pagina_mensaje(titulo, texto, tono="info"):
    ico = {"ok": "✓", "info": "i", "error": "!"}.get(tono, "i")
    c = ("<div class=hd><div class=brand>Recordatorio de seguimiento</div>"
         f"<h1>{_esc(titulo)}</h1></div>"
         f"<div class=bd><div class=\"ico {tono}\">{ico}</div><p>{_esc(texto)}</p></div>")
    return _pagina(titulo, c)
