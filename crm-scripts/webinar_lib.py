#!/usr/bin/env python3
"""Lógica reutilizable del flujo de webinars de CarbonBox (Fase B).

Fuente de verdad de inscritos = el Google Sheet de respuestas del Google Form,
que vive en la carpeta del invitado en Drive. Este módulo:
  · lee ese Sheet (Sheets API con el OAuth de Google ya montado en el VPS),
  · da de alta a cada inscrito en el CRM como fuenteLead=WEBINAR SIN oportunidad
    (no entra al pipeline; solo contacto + consentimiento de marketing),
  · construye los correos del ciclo (confirmación, recordatorios, post-webinar),
  · lleva un estado por webinar (qué correo se envió a qué email) para no repetir.

Las funciones puras (mapeo de filas, ventanas de recordatorio, render de correos,
estado) se prueban en test_webinar_lib.py sin tocar red ni CRM.

Stack: solo stdlib. Reutiliza crm_lib, lead_intake y seguimiento."""
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

import sys
sys.path.insert(0, "/root/crm-scripts")
from crm_lib import gql, google_access_token, now_utc
from lead_intake import find_or_create_company, dominio_de_email, pais_de_telefono
import seguimiento as seg

# --- Rutas ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEBINARS_DIR = os.path.join(BASE_DIR, "webinars")
STATE_DIR = os.path.join(WEBINARS_DIR, "state")

# Segundos de cada umbral de recordatorio (relativo al inicio del webinar).
UMBRAL_7D = 7 * 24 * 3600
UMBRAL_1D = 24 * 3600
UMBRAL_1H = 3600


# ------------------------------------------------------------------ #
# Configuración de webinars (una "ficha" JSON por webinar)            #
# ------------------------------------------------------------------ #
def cargar_config(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def listar_webinars(activos_solo=True):
    """Devuelve [(slug, config), ...] leyendo webinars/*.json.
    Ignora el subdirectorio state/ y los archivos *.example.json."""
    salida = []
    if not os.path.isdir(WEBINARS_DIR):
        return salida
    for nombre in sorted(os.listdir(WEBINARS_DIR)):
        if not nombre.endswith(".json") or nombre.endswith(".example.json"):
            continue
        cfg = cargar_config(os.path.join(WEBINARS_DIR, nombre))
        if activos_solo and not cfg.get("activo", True):
            continue
        salida.append((cfg.get("slug") or nombre[:-5], cfg))
    return salida


def fecha_inicio(cfg):
    """datetime aware del inicio del webinar, desde cfg['fecha_hora'] (ISO con offset)."""
    return datetime.fromisoformat(cfg["fecha_hora"])


# ------------------------------------------------------------------ #
# Lectura del Google Sheet de respuestas                             #
# ------------------------------------------------------------------ #
def leer_sheet(spreadsheet_id, rango, access_token):
    """Filas del Sheet (incluida la cabecera) vía Sheets API values.get.
    `rango` p.ej. 'Respuestas de formulario 1!A:Z'."""
    url = ("https://sheets.googleapis.com/v4/spreadsheets/"
           f"{spreadsheet_id}/values/{urllib.parse.quote(rango)}")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r).get("values", [])


def indices_columnas(cabecera, columnas):
    """Mapa campo->índice de columna, casando por el texto de la cabecera.
    `columnas` es {campo: 'Texto exacto de la pregunta en el Form'}.
    El match es tolerante: ignora mayúsculas y espacios de sobra."""
    def norm(s):
        return " ".join((s or "").strip().lower().split())
    norm_cab = [norm(c) for c in cabecera]
    idx = {}
    for campo, titulo in columnas.items():
        n = norm(titulo)
        if n in norm_cab:
            idx[campo] = norm_cab.index(n)
    return idx


def fila_a_datos(fila, idx):
    """Una fila del Sheet -> dict `datos` (mismo shape que usa el CRM)."""
    def val(campo):
        i = idx.get(campo)
        if i is None or i >= len(fila):
            return ""
        return (fila[i] or "").strip()

    marketing_raw = val("acepta_marketing").lower()
    return {
        "nombre": val("nombre"),
        "apellido": val("apellido"),
        "email": val("email").lower(),
        "tel": val("tel").replace(" ", ""),
        "empresa": val("empresa"),
        "cargo": val("cargo"),
        "ciudad": val("ciudad"),
        "acepta_marketing": marketing_raw in (
            "true", "on", "1", "yes", "sí", "si", "acepto", "x"),
    }


def filas_inscritos(valores, columnas):
    """Convierte la matriz cruda del Sheet en [datos, ...] (omite filas sin email)."""
    if not valores:
        return []
    cabecera, filas = valores[0], valores[1:]
    idx = indices_columnas(cabecera, columnas)
    salida = []
    for fila in filas:
        datos = fila_a_datos(fila, idx)
        if datos["email"]:
            salida.append(datos)
    return salida


# ------------------------------------------------------------------ #
# Alta en el CRM (SIN oportunidad; fuenteLead=WEBINAR)               #
# ------------------------------------------------------------------ #
def _persona_por_email(email):
    d = gql("""query($e: String!) { people(filter:{emails:{primaryEmail:{eq:$e}}}, first:1) {
        edges { node { id suscritoMarketing } } } }""", {"e": email})
    edges = d["people"]["edges"]
    return edges[0]["node"] if edges else None


def alta_inscrito(datos):
    """Da de alta (o reconcilia) un inscrito al webinar en el CRM.

    · Si el email ya existe: NO duplica. Si el inscrito aceptó marketing y la
      persona no estaba suscrita, la actualiza a suscritoMarketing=true. -> 'actualizado' | 'existe'
    · Si no existe: crea Empresa (dedup) + Persona con fuenteLead=WEBINAR y el
      consentimiento de marketing. NO crea oportunidad (no entra al pipeline). -> 'creado'
    · Devuelve None si faltan datos mínimos.
    """
    email = (datos.get("email") or "").strip().lower()
    nombre = (datos.get("nombre") or "").strip()
    apellido = (datos.get("apellido") or "").strip()
    if not email and not (nombre or apellido):
        return None

    if email:
        ex = _persona_por_email(email)
        if ex:
            if datos.get("acepta_marketing") and not ex.get("suscritoMarketing"):
                gql("""mutation($id: UUID!) { updatePerson(id:$id,
                    data:{suscritoMarketing:true}) { id } }""", {"id": ex["id"]})
                return "actualizado"
            return "existe"

    tel = (datos.get("tel") or "").replace(" ", "")
    company_id = find_or_create_company(
        (datos.get("empresa") or "").strip(),
        dominio=dominio_de_email(email),
        pais=pais_de_telefono(tel) or ("COLOMBIA" if tel and not tel.startswith("+") else None),
        ciudad=(datos.get("ciudad") or "").strip() or None)

    pdata = {"name": {"firstName": nombre or "(sin nombre)", "lastName": apellido},
             "fuenteLead": "WEBINAR",
             "suscritoMarketing": bool(datos.get("acepta_marketing"))}
    if email:
        pdata["emails"] = {"primaryEmail": email}
    if tel:
        pdata["phones"] = ({"primaryPhoneNumber": tel.lstrip("+"),
                            "primaryPhoneCallingCode": "+" + tel.lstrip("+")[:2],
                            "primaryPhoneCountryCode": "CO"} if tel.startswith("+")
                           else {"primaryPhoneNumber": tel,
                                 "primaryPhoneCallingCode": "+57",
                                 "primaryPhoneCountryCode": "CO"})
    cargo = (datos.get("cargo") or "").strip()
    if cargo:
        pdata["jobTitle"] = cargo[:120]
    if company_id:
        pdata["companyId"] = company_id

    d = gql("""mutation($data: PersonCreateInput!) { createPerson(data:$data) { id } }""",
            {"data": pdata})
    return "creado"


# ------------------------------------------------------------------ #
# Estado por webinar (qué correo se envió a qué email)               #
# ------------------------------------------------------------------ #
def _state_path(slug):
    return os.path.join(STATE_DIR, f"{slug}.json")


def cargar_estado(slug):
    """dict email -> lista de etapas ya enviadas ('intake','E3','E4','E5','E6')."""
    try:
        with open(_state_path(slug), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def guardar_estado(slug, estado):
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = _state_path(slug) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _state_path(slug))


def ya_enviado(estado, email, etapa):
    return etapa in estado.get(email, [])


def marcar_enviado(estado, email, etapa):
    estado.setdefault(email, [])
    if etapa not in estado[email]:
        estado[email].append(etapa)


# ------------------------------------------------------------------ #
# Ventanas de recordatorio                                           #
# ------------------------------------------------------------------ #
def recordatorios_debidos(inicio, ahora):
    """Etapas de recordatorio cuyo umbral ya se cruzó (y el webinar no ha pasado).
    Enfoque por umbral + estado: cada correo se envía una sola vez aunque el cron
    corra muchas veces y sin importar cuándo se inscribió la persona."""
    restante = (inicio - ahora).total_seconds()
    if restante <= 0:
        return []
    debidos = []
    if restante <= UMBRAL_7D:
        debidos.append("E3")
    if restante <= UMBRAL_1D:
        debidos.append("E4")
    if restante <= UMBRAL_1H:
        debidos.append("E5")
    return debidos


# ------------------------------------------------------------------ #
# Correos del ciclo (HTML branded + texto plano)                     #
# ------------------------------------------------------------------ #
_E = seg._esc


def _fecha_legible(cfg):
    """'martes 5 de agosto, 10:00 a. m. (hora Colombia)' — legible para el correo."""
    try:
        dt = fecha_inicio(cfg)
    except Exception:
        return cfg.get("fecha_texto", "")
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
             "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    h = dt.hour % 12 or 12
    ampm = "a. m." if dt.hour < 12 else "p. m."
    reloj = f"{h}:{dt.minute:02d} {ampm}"
    base = f"{dias[dt.weekday()]} {dt.day} de {meses[dt.month - 1]}, {reloj}"
    return base + (f" ({cfg['zona_texto']})" if cfg.get("zona_texto") else "")


def _boton(url, texto):
    if not url:
        return ""
    return (f'<p style="margin:22px 0"><a href="{_E(url)}" '
            'style="background:#1620a4;color:#fff;text-decoration:none;'
            'padding:13px 26px;border-radius:10px;font-weight:600;'
            'display:inline-block">' + _E(texto) + "</a></p>")


def _envolver(titulo_hd, cuerpo_html):
    """Correo con cabecera de marca CarbonBox + firma de Viviana."""
    hd = ('<div style="background:linear-gradient(135deg,#1620a4,#2a35c9 60%,#2f6b4a 155%);'
          'color:#fff;padding:20px 26px;border-radius:14px 14px 0 0">'
          '<div style="font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;'
          'opacity:.85">Webinar CarbonBox</div>'
          f'<div style="font-size:20px;font-weight:600;margin-top:4px">{_E(titulo_hd)}</div></div>')
    bd = ('<div style="padding:22px 26px;font-family:Poppins,Arial,sans-serif;'
          f'font-size:15px;line-height:1.6;color:#0f1535">{cuerpo_html}'
          + seg.FIRMA_VIVIANA + "</div>")
    return ('<div style="max-width:600px;margin:0 auto;border:1px solid #e6e8f2;'
            f'border-radius:14px;overflow:hidden">{hd}{bd}</div>')


def email_confirmacion(cfg, nombre):
    """E2 — confirmación inmediata de inscripción."""
    saludo = f"Hola {nombre}," if nombre else "¡Hola!"
    asunto = f"Confirmada tu inscripción: {cfg['titulo']}"
    cuerpo = (
        f"<p>{_E(saludo)}</p>"
        f"<p>Tu inscripción al webinar <b>{_E(cfg['titulo'])}</b> quedó confirmada. "
        "Nos alegra que nos acompañes.</p>"
        f"<p><b>Fecha:</b> {_E(_fecha_legible(cfg))}<br>"
        f"<b>Dónde:</b> En línea (Google Meet)</p>"
        + _boton(cfg.get("meet_link"), "Entrar al webinar")
        + _boton(cfg.get("add_to_calendar_link"), "Añadir a mi calendario")
        + "<p>Te enviaremos un recordatorio antes del evento. Si tienes dudas, "
        "responde a este correo.</p>")
    texto = (f"{saludo}\n\nTu inscripción al webinar \"{cfg['titulo']}\" quedó confirmada.\n"
             f"Fecha: {_fecha_legible(cfg)}\nDónde: En línea (Google Meet)\n"
             f"Enlace: {cfg.get('meet_link', '(se enviará antes del evento)')}\n")
    return asunto, _envolver("Inscripción confirmada", cuerpo), texto


def email_recordatorio(cfg, nombre, etapa):
    """E3/E4/E5 — recordatorios según cuánto falta."""
    saludo = f"Hola {nombre}," if nombre else "¡Hola!"
    cuando = {"E3": "la próxima semana", "E4": "mañana", "E5": "en una hora"}[etapa]
    titulo_hd = {"E3": "Falta poco", "E4": "Es mañana", "E5": "Empezamos pronto"}[etapa]
    asunto = {
        "E3": f"La próxima semana: {cfg['titulo']}",
        "E4": f"Mañana es el webinar: {cfg['titulo']}",
        "E5": f"En una hora: {cfg['titulo']}",
    }[etapa]
    cuerpo = (
        f"<p>{_E(saludo)}</p>"
        f"<p>Te recordamos que el webinar <b>{_E(cfg['titulo'])}</b> es {cuando}.</p>"
        f"<p><b>Fecha:</b> {_E(_fecha_legible(cfg))}<br>"
        f"<b>Dónde:</b> En línea (Google Meet)</p>"
        + _boton(cfg.get("meet_link"), "Entrar al webinar"))
    if etapa == "E3" and cfg.get("adelanto"):
        cuerpo += f"<p>{_E(cfg['adelanto'])}</p>"
    texto = (f"{saludo}\n\nEl webinar \"{cfg['titulo']}\" es {cuando}.\n"
             f"Fecha: {_fecha_legible(cfg)}\nEnlace: {cfg.get('meet_link', '')}\n")
    return asunto, _envolver(titulo_hd, cuerpo), texto


def email_post(cfg, nombre):
    """E6 — agradecimiento + grabación en YouTube."""
    saludo = f"Hola {nombre}," if nombre else "¡Hola!"
    asunto = f"Gracias por acompañarnos: {cfg['titulo']}"
    yt = cfg.get("youtube_url") or (
        f"https://youtu.be/{cfg['youtube_id']}" if cfg.get("youtube_id") else "")
    cuerpo = (
        f"<p>{_E(saludo)}</p>"
        f"<p>Gracias por tu interés en el webinar <b>{_E(cfg['titulo'])}</b>. "
        "Ya sea que nos acompañaste en vivo o no pudiste conectarte, aquí tienes "
        "la grabación completa para verla cuando quieras.</p>"
        + _boton(yt, "Ver la grabación en YouTube")
        + (f"<p>{_E(cfg['cta_texto'])}</p>" if cfg.get("cta_texto") else "")
        + _boton(cfg.get("cta_url"), cfg.get("cta_boton", "Agendar un diagnóstico gratuito")))
    texto = (f"{saludo}\n\nGracias por tu interés en \"{cfg['titulo']}\".\n"
             f"Grabación: {yt}\n")
    return asunto, _envolver("Gracias por participar", cuerpo), texto


# ------------------------------------------------------------------ #
# Envío (envoltura fina sobre Gmail API de seguimiento.py)           #
# ------------------------------------------------------------------ #
def enviar(para, asunto, html, texto, token=None):
    return seg.enviar_gmail(token or google_access_token(), para, asunto, html, texto=texto)
