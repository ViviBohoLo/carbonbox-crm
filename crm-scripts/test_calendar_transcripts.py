import unittest
import calendar_transcripts as ct


class TestNombres(unittest.TestCase):
    def test_titulo_con_empresa(self):
        self.assertEqual(ct.nombre_reunion("ITS"), "ITS — Llamada CarbonBox")

    def test_titulo_cae_a_dominio_si_no_hay_empresa(self):
        self.assertEqual(ct.nombre_reunion("", nombre="Yurany", dominio="itsinfocom.com"),
                         "itsinfocom.com — Llamada CarbonBox")

    def test_titulo_cae_a_nombre_si_correo_gratuito(self):
        self.assertEqual(ct.nombre_reunion("", nombre="Yurany", dominio=None),
                         "Yurany — Llamada CarbonBox")

    def test_parsea_empresa_de_transcript(self):
        fn = "ITS — Llamada CarbonBox (2026-07-10 at 14:00) - Transcript"
        self.assertEqual(ct.empresa_de_nombre_archivo(fn), "ITS")

    def test_archivo_ajeno_devuelve_none(self):
        self.assertIsNone(ct.empresa_de_nombre_archivo("Reunión equipo - Notas"))


class TestDeteccion(unittest.TestCase):
    EV = {"summary": "Hablemos de huellas de carbono",
          "attendees": [{"email": "info@carbonbox.app", "self": True},
                        {"email": "ymartinez03@itsinfocom.com", "displayName": "Yurany"}]}

    def test_invitado_externo(self):
        self.assertEqual(ct.invitado_externo(self.EV)["email"], "ymartinez03@itsinfocom.com")

    def test_es_reserva(self):
        self.assertTrue(ct.es_reserva_sin_renombrar(self.EV))

    def test_ya_renombrado_no_es_reserva(self):
        ev = dict(self.EV, summary="ITS — Llamada CarbonBox")
        self.assertFalse(ct.es_reserva_sin_renombrar(ev))

    def test_sin_invitado_externo_no_es_reserva(self):
        ev = {"summary": "Hablemos de huellas de carbono",
              "attendees": [{"email": "info@carbonbox.app", "self": True}]}
        self.assertFalse(ct.es_reserva_sin_renombrar(ev))

    def setUp(self):
        self._orig_gql = ct.c.gql

    def tearDown(self):
        ct.c.gql = self._orig_gql

    def test_empresa_de_correo(self):
        def fake_gql(q, v=None):
            return {"people": {"edges": [{"node": {"company": {"name": "ITS"}}}]}}
        ct.c.gql = fake_gql
        self.assertEqual(ct.empresa_de_correo("ymartinez03@itsinfocom.com"), "ITS")

    def test_empresa_de_correo_sin_persona(self):
        ct.c.gql = lambda q, v=None: {"people": {"edges": []}}
        self.assertIsNone(ct.empresa_de_correo("nadie@x.com"))


class TestRenombrar(unittest.TestCase):
    def setUp(self):
        self._orig = {n: getattr(ct, n) for n in
                      ("cal_list_upcoming", "cal_patch_summary", "empresa_de_correo")}
        self.patched = []
        ct.cal_list_upcoming = lambda at: [
            {"id": "ev1", "summary": "Hablemos de huellas de carbono",
             "attendees": [{"email": "info@carbonbox.app", "self": True},
                           {"email": "ymartinez03@itsinfocom.com", "displayName": "Yurany"}]},
            {"id": "ev2", "summary": "ITS — Llamada CarbonBox",   # ya renombrado
             "attendees": [{"email": "x@itsinfocom.com"}]},
            {"id": "ev3", "summary": "Reunión interna",
             "attendees": [{"email": "info@carbonbox.app", "self": True}]},
        ]
        ct.cal_patch_summary = lambda at, eid, nuevo: self.patched.append((eid, nuevo))
        ct.empresa_de_correo = lambda e: "ITS"

    def tearDown(self):
        for n, v in self._orig.items():
            setattr(ct, n, v)

    def test_solo_renombra_la_reserva_pendiente(self):
        hechos = ct.renombrar_reservas(at="tok")
        self.assertEqual(self.patched, [("ev1", "ITS — Llamada CarbonBox")])
        self.assertEqual(hechos, [("ev1", "ITS — Llamada CarbonBox")])

    def test_sin_empresa_cae_a_dominio(self):
        ct.empresa_de_correo = lambda e: None
        ct.renombrar_reservas(at="tok")
        self.assertEqual(self.patched, [("ev1", "itsinfocom.com — Llamada CarbonBox")])

    def test_un_evento_que_falla_no_bloquea_los_demas(self):
        ct.cal_list_upcoming = lambda at: [
            {"id": "bad", "summary": "Hablemos de huellas de carbono",
             "attendees": [{"email": "a@acme.com", "displayName": "A"}]},
            {"id": "good", "summary": "Hablemos de huellas de carbono",
             "attendees": [{"email": "b@beta.com", "displayName": "B"}]},
        ]
        def patch(at, eid, nuevo):
            if eid == "bad":
                raise RuntimeError("403")
            self.patched.append((eid, nuevo))
        ct.cal_patch_summary = patch
        ct.empresa_de_correo = lambda e: None
        hechos = ct.renombrar_reservas(at="tok")
        self.assertEqual([e for e, _ in self.patched], ["good"])   # el bueno sí se renombró
        self.assertEqual([e for e, _ in hechos], ["good"])


class TestArchivar(unittest.TestCase):
    def setUp(self):
        self._orig = {n: getattr(ct, n) for n in
                      ("drive_meet_recordings_files", "drive_ensure_folder", "drive_move")}
        self.moved = []
        ct.drive_meet_recordings_files = lambda at: [
            {"id": "f1", "name": "ITS — Llamada CarbonBox (2026-07-10) - Transcript",
             "parents": ["MEET"]},
            {"id": "f2", "name": "Reunión equipo - Notas", "parents": ["MEET"]},  # ajeno
        ]
        ct.drive_ensure_folder = lambda at, nombre, parent=None: "FID-" + nombre
        ct.drive_move = lambda at, fid, nuevo, viejo: self.moved.append((fid, nuevo, viejo))

    def tearDown(self):
        for n, v in self._orig.items():
            setattr(ct, n, v)

    def test_mueve_solo_transcripts_nuestros_no_movidos(self):
        estado = ct.archivar_transcripts(at="tok", estado=set())
        self.assertEqual(self.moved, [("f1", "FID-ITS", "MEET")])
        self.assertIn("f1", estado)

    def test_no_remueve_lo_ya_movido(self):
        ct.archivar_transcripts(at="tok", estado={"f1"})
        self.assertEqual(self.moved, [])

    def test_un_archivo_que_falla_no_bloquea_ni_marca(self):
        ct.drive_meet_recordings_files = lambda at: [
            {"id": "bad", "name": "ACME — Llamada CarbonBox - Transcript", "parents": ["MEET"]},
            {"id": "good", "name": "BETA — Llamada CarbonBox - Transcript", "parents": ["MEET"]},
        ]
        def mv(at, fid, nuevo, viejo):
            if fid == "bad":
                raise RuntimeError("500")
            self.moved.append((fid, nuevo, viejo))
        ct.drive_move = mv
        estado = ct.archivar_transcripts(at="tok", estado=set())
        self.assertEqual([m[0] for m in self.moved], ["good"])   # el bueno sí se movió
        self.assertIn("good", estado)
        self.assertNotIn("bad", estado)                          # el que falló NO se marca


class TestDriveBordes(unittest.TestCase):
    def setUp(self):
        self._orig_api = ct._api

    def tearDown(self):
        ct._api = self._orig_api

    def _capturar_url(self):
        urls = []
        ct._api = lambda at, method, url, body=None: (urls.append(url) or {"id": "x"})
        return urls

    def test_move_sin_parent_no_manda_removeparents(self):
        urls = self._capturar_url()
        ct.drive_move("tok", "F", "DEST", None)     # archivo sin parent previo
        self.assertIn("addParents=DEST", urls[0])
        self.assertNotIn("removeParents", urls[0])

    def test_move_con_parent_manda_removeparents(self):
        urls = self._capturar_url()
        ct.drive_move("tok", "F", "DEST", "MEET")
        self.assertIn("removeParents=MEET", urls[0])

    def test_find_folder_escapa_backslash_y_comilla(self):
        import urllib.parse
        urls = self._capturar_url()
        ct.drive_find_folder("tok", "A\\B's")
        q = urllib.parse.unquote(urls[0])
        self.assertIn("A\\\\B\\'s", q)   # backslash duplicado y comilla escapada en la query

    def test_patch_summary_no_notifica(self):
        urls = self._capturar_url()
        ct.cal_patch_summary("tok", "EV", "ITS — Llamada CarbonBox")
        self.assertIn("sendUpdates=none", urls[0])


class TestEstado(unittest.TestCase):
    def setUp(self):
        self._orig_estado = ct.ESTADO

    def tearDown(self):
        ct.ESTADO = self._orig_estado

    def test_estado_round_trip(self):
        import tempfile, os
        ruta = os.path.join(tempfile.mkdtemp(), "s.json")
        ct.ESTADO = ruta
        ct.guardar_estado({"a", "b"})
        self.assertEqual(ct.cargar_estado(), {"a", "b"})

    def test_estado_vacio_si_no_existe(self):
        ct.ESTADO = "/tmp/no-existe-xyz-carbonbox.json"
        self.assertEqual(ct.cargar_estado(), set())


if __name__ == "__main__":
    unittest.main()
