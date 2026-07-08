#!/usr/bin/env python3
"""Lógica reutilizable de alta de leads en el CRM CarbonBox.
La usan el puente de HubSpot (transición) y el servidor de intake del formulario."""
import sys
sys.path.insert(0, "/root/crm-scripts")
from crm_lib import gql, send_notification

DOMINIOS_GRATIS = {"gmail.com", "hotmail.com", "outlook.com", "yahoo.com",
                   "icloud.com", "live.com", "aol.com", "proton.me",
                   "protonmail.com", "yahoo.es", "hotmail.es", "outlook.es"}

PAIS_POR_INDICATIVO = {"+57": "COLOMBIA", "+52": "MEXICO", "+54": "ARGENTINA",
                       "+56": "CHILE", "+51": "PERU"}


def dominio_de_email(email):
    if not email or "@" not in email:
        return None
    dom = email.split("@")[1].lower()
    return None if dom in DOMINIOS_GRATIS else dom


def pais_de_telefono(tel):
    for ind, p in PAIS_POR_INDICATIVO.items():
        if tel.startswith(ind):
            return p
    return None


def origen_cors(origin):
    """Devuelve el Origin a reflejar en CORS si es un sitio nuestro
    (carbonbox.app, www, o un preview *.vercel.app); si no, cae al de producción."""
    o = (origin or "").strip()
    if o in ("https://carbonbox.app", "https://www.carbonbox.app") or o.endswith(".vercel.app"):
        return o
    return "https://carbonbox.app"


class RateLimiter:
    """Límite simple en memoria: N envíos por IP en una ventana deslizante corta.
    Ventana corta (no de una hora) para que un pico se libere rápido y no bloquee al
    usuario legítimo; umbral con holgura para absorber los reintentos del cliente."""
    def __init__(self, max_peticiones=10, ventana_seg=300):
        self.max = max_peticiones
        self.ventana = ventana_seg
        self._hist = {}  # ip -> [timestamps]

    def permite(self, ip, ahora):
        h = [t for t in self._hist.get(ip, []) if ahora - t < self.ventana]
        if len(h) >= self.max:
            self._hist[ip] = h
            return False
        h.append(ahora)
        self._hist[ip] = h
        return True

    def retry_after(self, ip, ahora):
        """Segundos hasta que se libere un slot (para la cabecera Retry-After).
        0 si todavía permite. No muta el historial."""
        h = [t for t in self._hist.get(ip, []) if ahora - t < self.ventana]
        if len(h) < self.max:
            return 0
        return max(1, int(self.ventana - (ahora - min(h))) + 1)


def es_bot(payload):
    """Honeypot: los bots rellenan el campo oculto 'website'."""
    return bool((payload.get("website") or "").strip())


def mapear_form(payload):
    """Payload plano del formulario web -> dict `datos` de crear_lead."""
    def g(k):
        return (payload.get(k) or "").strip()
    return {
        "nombre": g("firstname"),
        "apellido": g("lastname"),
        "email": g("email").lower(),
        "tel": g("mobilephone").replace(" ", ""),
        "empresa": g("company"),
        "cargo": g("jobtitle"),
        "ciudad": g("city"),
        "necesidad": g("necesidad"),
        "mensaje": g("describenos_cual_es_tu_necesidad"),
        "acepta_marketing": g("acepta_marketing").lower() in ("true", "on", "1", "yes"),
    }


def es_duplicado(ex):
    """Un error de duplicado = el registro ya existe (lo creó otra petición: p.ej. una
    carrera entre el envío y su reintento con el mismo email). NO es un fallo real →
    tratarlo como benigno, no como error. Lo usan el intake y el puente de HubSpot."""
    m = str(ex).lower()
    return "duplicate" in m or "already exists" in m


def resumen_lead(datos):
    """Una línea con lo clave del lead (para bullets del puente y logs)."""
    nombre = " ".join(x for x in [datos.get("nombre"), datos.get("apellido")] if x).strip()
    partes = [nombre or "(sin nombre)"]
    if datos.get("empresa"):
        partes.append(datos["empresa"])
    linea = " — ".join(partes)
    extra = []
    if datos.get("tel"):
        extra.append(f"📞 {datos['tel']}")
    if datos.get("email"):
        extra.append(f"📧 {datos['email']}")
    return linea + ("  ·  " + "  ·  ".join(extra) if extra else "")


def ficha_persona(datos):
    """Bloque multilínea con la info para poder llamar (nombre, empresa, teléfono,
    correo, cargo/ciudad, necesidad). Va en el correo de aviso y en la nota."""
    cargo_ciudad = " · ".join(x for x in [datos.get("cargo"), datos.get("ciudad")] if x)
    pares = [
        ("Nombre", " ".join(x for x in [datos.get("nombre"), datos.get("apellido")] if x).strip()),
        ("Empresa", datos.get("empresa")),
        ("Teléfono", datos.get("tel")),
        ("Correo", datos.get("email")),
        ("Cargo", cargo_ciudad),
        ("Necesidad", datos.get("necesidad")),
        ("Mensaje", datos.get("mensaje")),
    ]
    return "\n".join(f"{etq}: {val}" for etq, val in pares if val)


def _crear_company(data):
    d = gql("""mutation($data: CompanyCreateInput!) { createCompany(data:$data) { id } }""",
            {"data": data})
    return d["createCompany"]["id"]


def find_or_create_company(nombre, dominio=None, pais=None, ciudad=None):
    if not nombre:
        return None
    # dedup por nombre
    d = gql("""query($n: String!) { companies(filter:{name:{ilike:$n}}, first:1) {
        edges { node { id } } } }""", {"n": nombre})
    if d["companies"]["edges"]:
        return d["companies"]["edges"][0]["node"]["id"]
    # dedup por dominio (dos personas de la misma empresa con nombre escrito distinto)
    if dominio:
        d = gql("""query($u: String!) { companies(filter:{domainName:{primaryLinkUrl:{ilike:$u}}}, first:1) {
            edges { node { id } } } }""", {"u": f"%{dominio}%"})
        if d["companies"]["edges"]:
            return d["companies"]["edges"][0]["node"]["id"]
    data = {"name": nombre}
    if dominio:
        data["domainName"] = {"primaryLinkUrl": f"https://{dominio}"}
    if pais:
        data["pais"] = pais
    if ciudad:
        data["address"] = {"addressCity": ciudad}
    try:
        return _crear_company(data)
    except RuntimeError as ex:
        # el dominio puede chocar con la restricción única (p.ej. empresa soft-deleted):
        # no perder el lead -> crear la empresa sin el dominio.
        if dominio and "duplicate" in str(ex).lower():
            data.pop("domainName", None)
            return _crear_company(data)
        raise


def crear_lead(datos):
    """Crea Empresa(dedup)+Contacto(WEB)+Oportunidad(LEAD_CAPTURADO)+Nota.
    Devuelve resumen o None si se omite (dup por email o sin datos minimos)."""
    nombre = (datos.get("nombre") or "").strip()
    apellido = (datos.get("apellido") or "").strip()
    email = (datos.get("email") or "").strip().lower()
    tel = (datos.get("tel") or "").replace(" ", "")
    empresa = (datos.get("empresa") or "").strip()
    cargo = (datos.get("cargo") or "").strip()
    ciudad = (datos.get("ciudad") or "").strip()
    necesidad = (datos.get("necesidad") or "").strip()
    mensaje = (datos.get("mensaje") or "").strip()

    if not email and not (nombre or apellido):
        return None
    if email:
        d = gql("""query($e: String!) { people(filter:{emails:{primaryEmail:{eq:$e}}}, first:1) {
            edges { node { id } } } }""", {"e": email})
        if d["people"]["edges"]:
            return None

    company_id = find_or_create_company(
        empresa,
        dominio=dominio_de_email(email),
        pais=pais_de_telefono(tel) or ("COLOMBIA" if tel and not tel.startswith("+") else None),
        ciudad=ciudad or None)

    pdata = {"name": {"firstName": nombre or "(sin nombre)", "lastName": apellido},
             "fuenteLead": "WEB",
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
    if cargo:
        pdata["jobTitle"] = cargo[:120]
    if company_id:
        pdata["companyId"] = company_id
    def _crear_person():
        return gql("""mutation($data: PersonCreateInput!) { createPerson(data:$data) { id } }""",
                   {"data": pdata})
    try:
        d = _crear_person()
    except RuntimeError as ex:
        if not es_duplicado(ex) or not email:
            raise
        # Duplicado en el email. Dos casos:
        # 1) Carrera: otra petición (p.ej. el reintento del cliente) YA creó este email
        #    → hay una persona VIVA → benigno, no duplicar.
        live = gql("""query($e: String!) { people(filter:{emails:{primaryEmail:{eq:$e}}}, first:1) {
            edges { node { id } } } }""", {"e": email})
        if live["people"]["edges"]:
            return None
        # 2) El email lo bloquea un registro BORRADO (soft-deleted): el índice único
        #    incluye los borrados. Es un lead REAL que vuelve → liberar el email y reintentar
        #    (si no, se perdería en silencio).
        dead = gql("""query($e: String!) { people(
            filter:{emails:{primaryEmail:{eq:$e}}, deletedAt:{is:NOT_NULL}}, first:1) {
            edges { node { id } } } }""", {"e": email})
        for e in dead["people"]["edges"]:
            gql("""mutation($id: UUID!) { destroyPerson(id:$id) { id } }""", {"id": e["node"]["id"]})
        d = _crear_person()  # reintento tras liberar el email
    person_id = d["createPerson"]["id"]

    opp_name = f"{empresa or (nombre + ' ' + apellido).strip()} — web"
    odata = {"name": opp_name, "stage": "LEAD_CAPTURADO", "pointOfContactId": person_id}
    if company_id:
        odata["companyId"] = company_id
    d = gql("""mutation($data: OpportunityCreateInput!) { createOpportunity(data:$data) { id } }""",
            {"data": odata})
    opp_id = d["createOpportunity"]["id"]

    cuerpo = ficha_persona(datos) + "\n\n_Origen: formulario web carbonbox.app_"
    d = gql("""mutation($data: NoteCreateInput!) { createNote(data:$data) { id } }""",
            {"data": {"title": "Formulario web", "bodyV2": {"markdown": cuerpo}}})
    note_id = d["createNote"]["id"]
    gql("""mutation($data: NoteTargetCreateInput!) { createNoteTarget(data:$data) { id } }""",
        {"data": {"noteId": note_id, "targetOpportunityId": opp_id}})

    return resumen_lead(datos)
