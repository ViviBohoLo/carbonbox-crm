import json
import unittest

import subir_deck as s


class TestTipoMime(unittest.TestCase):
    def test_office_no_depende_del_sistema(self):
        # mimetypes no siempre conoce los formatos de Office; por eso hay tabla fija.
        self.assertEqual(
            s.tipo_mime("Cotizacion.pptx"),
            "application/vnd.openxmlformats-officedocument.presentationml.presentation")
        self.assertEqual(s.tipo_mime("x.pdf"), "application/pdf")

    def test_no_le_importan_las_mayusculas(self):
        self.assertEqual(s.tipo_mime("DECK.PDF"), "application/pdf")

    def test_desconocido_cae_en_binario(self):
        self.assertEqual(s.tipo_mime("cosa.zzz"), "application/octet-stream")


class TestCuerpoMultipart(unittest.TestCase):
    def setUp(self):
        self.cuerpo = s.cuerpo_multipart(
            {"name": "d.pdf", "parents": ["CARPETA"]}, b"%PDF-1.7 bytes",
            "application/pdf", "FRONTERA")

    def test_lleva_metadatos_y_contenido(self):
        self.assertIn(b'"name": "d.pdf"', self.cuerpo)
        self.assertIn(b"CARPETA", self.cuerpo)
        self.assertIn(b"%PDF-1.7 bytes", self.cuerpo)

    def test_estructura_multipart(self):
        # Dos partes abiertas con la frontera y el cierre con "--" al final.
        self.assertEqual(self.cuerpo.count(b"--FRONTERA\r\n"), 2)
        self.assertTrue(self.cuerpo.endswith(b"--FRONTERA--\r\n"))
        self.assertIn(b"Content-Type: application/json; charset=UTF-8", self.cuerpo)
        self.assertIn(b"Content-Type: application/pdf", self.cuerpo)

    def test_contenido_binario_no_se_corrompe(self):
        crudo = bytes(range(256))
        cuerpo = s.cuerpo_multipart({"name": "b"}, crudo, "application/octet-stream", "F")
        self.assertIn(crudo, cuerpo)

    def test_nombres_con_acentos(self):
        cuerpo = s.cuerpo_multipart({"name": "Cotización Ñ.pdf"}, b"x", "application/pdf", "F")
        meta = cuerpo.split(b"\r\n\r\n")[1].split(b"\r\n--F")[0]
        self.assertEqual(json.loads(meta)["name"], "Cotización Ñ.pdf")


if __name__ == "__main__":
    unittest.main()
