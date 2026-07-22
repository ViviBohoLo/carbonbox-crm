import unittest
import cotizacion as c


OPP = {
    "id": "o1", "name": "HC Organizacional - ACME", "stage": "PROPUESTA_ENVIADA",
    "borradorCorreo": "Hola Ana, te comparto la cotización.",
    "linkCotizacion": {"primaryLinkUrl": "https://drive.google.com/file/d/XYZ/view"},
    "company": {"name": "ACME"},
    "pointOfContact": {"name": {"firstName": "Ana"}, "emails": {"primaryEmail": "ana@acme.co"}},
}


class TestAsunto(unittest.TestCase):
    def test_asunto_estandar(self):
        self.assertEqual(c.asunto_cotizacion("ACME"), "Cotización CarbonBox — ACME")


class TestDatos(unittest.TestCase):
    def test_extrae_todo(self):
        nombre, para, empresa, link, borrador = c.datos_cotizacion(OPP)
        self.assertEqual((nombre, para, empresa), ("Ana", "ana@acme.co", "ACME"))
        self.assertIn("XYZ", link)
        self.assertIn("cotización", borrador)

    def test_sin_contacto_ni_link(self):
        nombre, para, empresa, link, borrador = c.datos_cotizacion(
            {"name": "X", "company": None, "pointOfContact": None,
             "linkCotizacion": None, "borradorCorreo": None})
        self.assertEqual((nombre, para, empresa, link, borrador), ("", "", "", "", ""))


class TestPagina(unittest.TestCase):
    def test_trae_los_campos(self):
        h = c.pagina_cotizacion("o1", "sig123", "Ana", "ana@acme.co", "ACME",
                                "Cotización CarbonBox — ACME", "Hola Ana", "https://drive/x")
        self.assertIn("ana@acme.co", h)
        self.assertIn("name=cc", h)
        self.assertIn("name=remitente", h)
        self.assertIn("name=asunto", h)
        self.assertIn("<textarea", h)
        self.assertIn("Confirmar y enviar", h)
        for k in ("viviana", "laura", "alejandra", "miguel"):
            self.assertIn(k, h)

    def test_escapa_html(self):
        h = c.pagina_cotizacion("o1", "s", "A", "a@x.co", "<b>ACME</b>", "asunto", "cuerpo", "u")
        self.assertNotIn("<b>ACME</b>", h)
        self.assertIn("&lt;b&gt;ACME&lt;/b&gt;", h)


if __name__ == "__main__":
    unittest.main()
