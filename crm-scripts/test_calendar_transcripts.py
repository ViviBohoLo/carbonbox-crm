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


if __name__ == "__main__":
    unittest.main()
