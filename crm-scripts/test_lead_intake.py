import unittest
import lead_intake as li


class TestHelpers(unittest.TestCase):
    def test_dominio_corporativo(self):
        self.assertEqual(li.dominio_de_email("ana@acme.com"), "acme.com")

    def test_dominio_gratuito_es_none(self):
        self.assertIsNone(li.dominio_de_email("ana@gmail.com"))

    def test_dominio_sin_arroba(self):
        self.assertIsNone(li.dominio_de_email("noesunemail"))

    def test_pais_por_indicativo(self):
        self.assertEqual(li.pais_de_telefono("+573001234567"), "COLOMBIA")
        self.assertEqual(li.pais_de_telefono("+521234567890"), "MEXICO")

    def test_pais_desconocido(self):
        self.assertIsNone(li.pais_de_telefono("3001234567"))


class TestCrearLead(unittest.TestCase):
    def setUp(self):
        self.calls = []

        def fake_gql(query, variables=None):
            self.calls.append((query, variables or {}))
            if "people(filter" in query:
                return {"people": {"edges": []}}          # no existe -> no dup
            if "companies(filter" in query:
                return {"companies": {"edges": []}}        # no existe
            if "createCompany" in query:
                return {"createCompany": {"id": "co-1"}}
            if "createPerson" in query:
                return {"createPerson": {"id": "pe-1"}}
            if "createOpportunity" in query:
                return {"createOpportunity": {"id": "op-1"}}
            if "createNote" in query and "Target" not in query:
                return {"createNote": {"id": "no-1"}}
            if "createNoteTarget" in query:
                return {"createNoteTarget": {"id": "nt-1"}}
            return {}
        li.gql = fake_gql

    def _person_input(self):
        for q, v in self.calls:
            if "createPerson" in q:
                return v["data"]
        return None

    def test_persona_fuente_web_y_stage(self):
        datos = {"nombre": "Ana", "apellido": "Ruiz", "email": "ana@acme.com",
                 "tel": "+573001234567", "empresa": "Acme", "cargo": "CEO",
                 "ciudad": "Bogotá", "necesidad": "Huella", "mensaje": "Hola"}
        r = li.crear_lead(datos)
        self.assertIn("Ana Ruiz", r)
        self.assertEqual(self._person_input()["fuenteLead"], "WEB")
        self.assertTrue(any("createOpportunity" in q and v["data"]["stage"] == "LEAD_CAPTURADO"
                            for q, v in self.calls))

    def test_dedupe_email_existente(self):
        li.gql = lambda q, v=None: {"people": {"edges": [{"node": {"id": "x"}}]}} \
            if "people(filter" in q else {}
        r = li.crear_lead({"nombre": "Ya", "apellido": "Existe",
                           "email": "dup@acme.com", "tel": "", "empresa": "",
                           "cargo": "", "ciudad": "", "necesidad": "", "mensaje": ""})
        self.assertIsNone(r)

    def test_setea_suscrito_marketing_true(self):
        li.crear_lead({"nombre": "Ana", "email": "ana@acme.com", "empresa": "Acme",
                       "acepta_marketing": True})
        self.assertTrue(self._person_input()["suscritoMarketing"])

    def test_setea_suscrito_marketing_false(self):
        li.crear_lead({"nombre": "Ana", "email": "ana@acme.com", "empresa": "Acme",
                       "acepta_marketing": False})
        self.assertFalse(self._person_input()["suscritoMarketing"])

    def test_duplicado_por_carrera_devuelve_none(self):
        """Carrera con una persona VIVA (el reintento del cliente ya la creó): benigno."""
        st = {"live_calls": 0}
        def fq(q, v=None):
            if "createPerson" in q:
                raise RuntimeError('[{"message": "A duplicate entry was detected"}]')
            if "deletedAt" in q:
                return {"people": {"edges": []}}
            if "people(filter" in q:            # dedup (top) vacío; re-check devuelve viva
                st["live_calls"] += 1
                node = [] if st["live_calls"] == 1 else [{"node": {"id": "pe-live"}}]
                return {"people": {"edges": node}}
            if "companies(filter" in q:
                return {"companies": {"edges": []}}
            if "createCompany" in q:
                return {"createCompany": {"id": "co-1"}}
            return {}
        li.gql = fq
        r = li.crear_lead({"nombre": "Race", "email": "race@acme.com", "empresa": "Acme"})
        self.assertIsNone(r)

    def test_recupera_lead_si_email_bloqueado_por_borrado(self):
        """Colisión con un contacto SOFT-DELETED: se libera (destroyPerson) y se reintenta,
        para NO perder un lead real que vuelve a escribir."""
        st = {"person_creates": 0, "destroyed": []}
        def fq(q, v=None):
            if "destroyPerson" in q:
                st["destroyed"].append(v["id"]); return {"destroyPerson": {"id": v["id"]}}
            if "createPerson" in q:
                st["person_creates"] += 1
                if st["person_creates"] == 1:
                    raise RuntimeError('[{"message": "A duplicate entry was detected"}]')
                return {"createPerson": {"id": "pe-new"}}
            if "deletedAt" in q:                 # query de borrados: hay uno
                return {"people": {"edges": [{"node": {"id": "dead-1"}}]}}
            if "people(filter" in q:             # dedup/recheck de vivos: vacío
                return {"people": {"edges": []}}
            if "companies(filter" in q:
                return {"companies": {"edges": []}}
            if "createCompany" in q:
                return {"createCompany": {"id": "co-1"}}
            if "createOpportunity" in q:
                return {"createOpportunity": {"id": "op-1"}}
            if "createNote" in q and "Target" not in q:
                return {"createNote": {"id": "no-1"}}
            return {"createNoteTarget": {"id": "nt-1"}}
        li.gql = fq
        r = li.crear_lead({"nombre": "Vuelve", "email": "vuelve@acme.com", "empresa": "Acme"})
        self.assertIsNotNone(r)                       # el lead SÍ se crea
        self.assertEqual(st["destroyed"], ["dead-1"])  # liberó el email del borrado
        self.assertEqual(st["person_creates"], 2)      # reintentó el create


class TestFicha(unittest.TestCase):
    DATOS = {"nombre": "Ana", "apellido": "Ruiz", "email": "ana@acme.com",
             "tel": "+573001234567", "empresa": "Acme", "cargo": "CEO",
             "ciudad": "Bogotá", "necesidad": "Huella", "mensaje": "Hola"}

    def test_ficha_incluye_todo(self):
        f = li.ficha_persona(self.DATOS)
        for esperado in ["Ana Ruiz", "Acme", "+573001234567", "ana@acme.com", "CEO", "Bogotá", "Huella"]:
            self.assertIn(esperado, f)

    def test_ficha_omite_vacios(self):
        f = li.ficha_persona({"nombre": "Ana", "email": "a@x.com"})
        self.assertIn("Ana", f)
        self.assertNotIn("Teléfono", f)

    def test_resumen_incluye_empresa_y_telefono(self):
        r = li.resumen_lead(self.DATOS)
        self.assertIn("Acme", r)
        self.assertIn("+573001234567", r)
        self.assertIn("Ana Ruiz", r)


class TestEsDuplicado(unittest.TestCase):
    def test_detecta_duplicado(self):
        self.assertTrue(li.es_duplicado(RuntimeError("A duplicate entry was detected")))
        self.assertTrue(li.es_duplicado(Exception("This record already exists")))

    def test_no_es_duplicado(self):
        self.assertFalse(li.es_duplicado(RuntimeError("Connection timeout")))
        self.assertFalse(li.es_duplicado(RuntimeError("LIMIT_REACHED")))


class TestRateLimiter(unittest.TestCase):
    def test_bloquea_tras_el_limite(self):
        rl = li.RateLimiter(max_peticiones=3, ventana_seg=300)
        t = 1000.0
        self.assertTrue(rl.permite("1.1.1.1", t))
        self.assertTrue(rl.permite("1.1.1.1", t))
        self.assertTrue(rl.permite("1.1.1.1", t))
        self.assertFalse(rl.permite("1.1.1.1", t))

    def test_otra_ip_no_afecta(self):
        rl = li.RateLimiter(max_peticiones=1, ventana_seg=300)
        t = 1000.0
        self.assertTrue(rl.permite("1.1.1.1", t))
        self.assertTrue(rl.permite("2.2.2.2", t))

    def test_ventana_corta_se_libera(self):
        rl = li.RateLimiter(max_peticiones=1, ventana_seg=300)
        self.assertTrue(rl.permite("1.1.1.1", 1000.0))
        self.assertFalse(rl.permite("1.1.1.1", 1000.0))
        self.assertTrue(rl.permite("1.1.1.1", 1000.0 + 301))  # pasó la ventana

    def test_retry_after(self):
        rl = li.RateLimiter(max_peticiones=1, ventana_seg=300)
        self.assertEqual(rl.retry_after("1.1.1.1", 1000.0), 0)  # aún permite
        rl.permite("1.1.1.1", 1000.0)
        ra = rl.retry_after("1.1.1.1", 1000.0)                  # ahora bloqueado
        self.assertTrue(1 <= ra <= 301, ra)
        self.assertEqual(rl.retry_after("1.1.1.1", 1000.0 + 301), 0)  # tras la ventana


class TestOrigenCors(unittest.TestCase):
    def test_produccion(self):
        self.assertEqual(li.origen_cors("https://carbonbox.app"), "https://carbonbox.app")
    def test_www(self):
        self.assertEqual(li.origen_cors("https://www.carbonbox.app"), "https://www.carbonbox.app")
    def test_preview_vercel(self):
        o = "https://carbonbox-web-abc123.vercel.app"
        self.assertEqual(li.origen_cors(o), o)
    def test_desconocido_cae_a_produccion(self):
        self.assertEqual(li.origen_cors("https://evil.com"), "https://carbonbox.app")
    def test_vacio(self):
        self.assertEqual(li.origen_cors(""), "https://carbonbox.app")


class TestFindOrCreateCompany(unittest.TestCase):
    def test_dedup_por_dominio(self):
        """Nombre no coincide pero el dominio ya existe -> reusa esa empresa (no crea)."""
        def fq(q, v=None):
            if "name:{ilike" in q:
                return {"companies": {"edges": []}}
            if "domainName" in q:
                return {"companies": {"edges": [{"node": {"id": "co-exist"}}]}}
            raise AssertionError("no deberia intentar crear")
        li.gql = fq
        self.assertEqual(li.find_or_create_company("Nombre Distinto SA", dominio="acme.com"),
                         "co-exist")

    def test_fallback_dominio_duplicado(self):
        """Si createCompany choca por dominio duplicado (soft-deleted), reintenta sin dominio."""
        state = {"creates": 0}
        def fq(q, v=None):
            if "companies(filter" in q:
                return {"companies": {"edges": []}}
            if "createCompany" in q:
                state["creates"] += 1
                if state["creates"] == 1 and "domainName" in str(v):
                    raise RuntimeError('[{"message": "A duplicate entry was detected"}]')
                return {"createCompany": {"id": "co-new"}}
            return {}
        li.gql = fq
        self.assertEqual(li.find_or_create_company("X SA", dominio="dup.com"), "co-new")
        self.assertEqual(state["creates"], 2)  # reintentó sin dominio


class TestMapeoForm(unittest.TestCase):
    def test_mapea_campos(self):
        payload = {"firstname": "Ana", "lastname": "Ruiz", "email": "ANA@Acme.com",
                   "mobilephone": "+57 300 123 4567", "company": "Acme",
                   "jobtitle": "CEO", "city": "Bogotá", "necesidad": "Huella",
                   "describenos_cual_es_tu_necesidad": "Hola"}
        d = li.mapear_form(payload)
        self.assertEqual(d["nombre"], "Ana")
        self.assertEqual(d["email"], "ana@acme.com")
        self.assertEqual(d["tel"], "+573001234567")
        self.assertEqual(d["mensaje"], "Hola")

    def test_honeypot(self):
        self.assertTrue(li.es_bot({"website": "http://spam"}))
        self.assertFalse(li.es_bot({"website": ""}))
        self.assertFalse(li.es_bot({}))

    def test_marketing_marcado(self):
        d = li.mapear_form({"firstname": "Ana", "email": "a@x.com",
                            "acepta_marketing": "true"})
        self.assertTrue(d["acepta_marketing"])

    def test_marketing_no_marcado(self):
        d = li.mapear_form({"firstname": "Ana", "email": "a@x.com"})
        self.assertFalse(d["acepta_marketing"])

    def test_marketing_valores_checkbox(self):
        for v in ("true", "on", "1", "yes", "TRUE", "On"):
            self.assertTrue(li.mapear_form({"acepta_marketing": v})["acepta_marketing"], v)
        for v in ("", "false", "0", "off"):
            self.assertFalse(li.mapear_form({"acepta_marketing": v})["acepta_marketing"], v)


if __name__ == "__main__":
    unittest.main()
