import unittest
import seguimiento as s


class TestFirma(unittest.TestCase):
    def test_firma_y_valida(self):
        sig = s.firmar("opp-123", "clave")
        self.assertTrue(s.valida("opp-123", sig, "clave"))
        self.assertFalse(s.valida("opp-123", "malo", "clave"))
        self.assertFalse(s.valida("otro", sig, "clave"))
        self.assertFalse(s.valida("opp-123", None, "clave"))


class TestPlantilla(unittest.TestCase):
    def test_propuesta(self):
        asunto, cuerpo = s.plantilla("PROPUESTA_ENVIADA", nombre="Ana", empresa="ACME", negocio="HC ACME")
        self.assertIn("Ana", cuerpo)
        self.assertIn("ACME", cuerpo)
        self.assertIn("propuesta", cuerpo.lower())

    def test_negociacion(self):
        asunto, cuerpo = s.plantilla("EN_NEGOCIACION", nombre="Luis", empresa="X", negocio="HC X")
        self.assertIn("HC X", asunto)
        self.assertIn("Luis", cuerpo)

    def test_etapa_sin_plantilla(self):
        self.assertIsNone(s.plantilla("CERRADO_GANADO", nombre="x", empresa="y", negocio="z"))
        self.assertFalse(s.tiene_plantilla("CERRADO_GANADO"))
        self.assertTrue(s.tiene_plantilla("PROPUESTA_ENVIADA"))
        self.assertTrue(s.tiene_plantilla("LEAD_CAPTURADO"))    # agenda

    def test_plantilla_agenda_lead(self):
        asunto, cuerpo = s.plantilla("LEAD_CAPTURADO", nombre="Ana", empresa="ACME", negocio="ACME")
        self.assertIn("Ana", cuerpo)
        self.assertIn("calendar.app.google", cuerpo)
        self.assertFalse(s.aplica_limite_semana("LEAD_CAPTURADO"))
        self.assertTrue(s.aplica_limite_semana("PROPUESTA_ENVIADA"))

    def test_cuerpo_email_lleva_firma(self):
        html = s.cuerpo_email_html("Hola Ana")
        self.assertIn("Hola Ana", html)
        self.assertIn("Viviana Bohórquez", html)
        self.assertIn("wa.me/573208675567", html)


class TestRemitentesYCC(unittest.TestCase):
    def test_remitentes_son_los_cuatro(self):
        self.assertEqual(set(s.REMITENTES), {"viviana", "laura", "alejandra", "miguel"})
        self.assertIn("viviana.bohorquez@carbonbox.app", s.REMITENTES["viviana"])
        self.assertIn("Laura", s.REMITENTES["laura"])

    def test_parse_cc_separa_y_limpia(self):
        self.assertEqual(s.parse_cc("a@x.co, b@y.co;c@z.co"), ["a@x.co", "b@y.co", "c@z.co"])
        self.assertEqual(s.parse_cc("  a@x.co  "), ["a@x.co"])
        self.assertEqual(s.parse_cc(""), [])
        self.assertEqual(s.parse_cc(None), [])

    def test_parse_cc_descarta_lo_que_no_es_correo(self):
        self.assertEqual(s.parse_cc("a@x.co, basura, b@y.co"), ["a@x.co", "b@y.co"])

    def test_permalink(self):
        self.assertEqual(s.permalink_gmail("abc123"),
                         "https://mail.google.com/mail/u/0/#all/abc123")


if __name__ == "__main__":
    unittest.main()
