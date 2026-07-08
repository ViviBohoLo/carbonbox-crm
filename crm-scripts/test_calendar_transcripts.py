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

    def test_empresa_de_correo(self):
        def fake_gql(q, v=None):
            return {"people": {"edges": [{"node": {"company": {"name": "ITS"}}}]}}
        ct.c.gql = fake_gql
        self.assertEqual(ct.empresa_de_correo("ymartinez03@itsinfocom.com"), "ITS")

    def test_empresa_de_correo_sin_persona(self):
        ct.c.gql = lambda q, v=None: {"people": {"edges": []}}
        self.assertIsNone(ct.empresa_de_correo("nadie@x.com"))


if __name__ == "__main__":
    unittest.main()
