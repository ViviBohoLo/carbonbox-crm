#!/usr/bin/env python3
"""Pruebas de las funciones puras de webinar_lib (sin red ni CRM)."""
import unittest
from datetime import datetime, timedelta, timezone

import sys
sys.path.insert(0, "/root/crm-scripts")
import webinar_lib as wl

COLS = {
    "email": "Correo electrónico",
    "nombre": "Nombre",
    "empresa": "Empresa",
    "acepta_marketing": "Acepto recibir información de CarbonBox",
}


class TestMapeoSheet(unittest.TestCase):
    def test_indices_tolerante_a_espacios_y_mayusculas(self):
        cab = ["Marca temporal", "  CORREO electrónico ", "Nombre", "Empresa",
               "Acepto recibir información de CarbonBox"]
        idx = wl.indices_columnas(cab, COLS)
        self.assertEqual(idx["email"], 1)
        self.assertEqual(idx["nombre"], 2)
        self.assertEqual(idx["acepta_marketing"], 4)

    def test_fila_a_datos_marketing_si(self):
        cab = ["Marca temporal", "Correo electrónico", "Nombre", "Empresa",
               "Acepto recibir información de CarbonBox"]
        idx = wl.indices_columnas(cab, COLS)
        fila = ["2026/07/14 10:00", "ANA@EMPRESA.com", "Ana", "Empresa X", "Sí"]
        d = wl.fila_a_datos(fila, idx)
        self.assertEqual(d["email"], "ana@empresa.com")
        self.assertEqual(d["nombre"], "Ana")
        self.assertEqual(d["empresa"], "Empresa X")
        self.assertTrue(d["acepta_marketing"])

    def test_fila_a_datos_marketing_no(self):
        cab = ["Correo electrónico", "Acepto recibir información de CarbonBox"]
        idx = wl.indices_columnas(cab, {"email": "Correo electrónico",
                                        "acepta_marketing": "Acepto recibir información de CarbonBox"})
        d = wl.fila_a_datos(["x@y.com", ""], idx)
        self.assertFalse(d["acepta_marketing"])

    def test_filas_inscritos_omite_sin_email(self):
        valores = [
            ["Correo electrónico", "Nombre"],
            ["a@b.com", "Ana"],
            ["", "SinCorreo"],
        ]
        res = wl.filas_inscritos(valores, {"email": "Correo electrónico", "nombre": "Nombre"})
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["email"], "a@b.com")

    def test_filas_inscritos_vacio(self):
        self.assertEqual(wl.filas_inscritos([], COLS), [])


class TestRecordatorios(unittest.TestCase):
    def setUp(self):
        self.inicio = datetime(2026, 8, 5, 15, 0, tzinfo=timezone.utc)

    def test_lejos_no_hay_recordatorios(self):
        ahora = self.inicio - timedelta(days=10)
        self.assertEqual(wl.recordatorios_debidos(self.inicio, ahora), [])

    def test_dentro_de_7d(self):
        ahora = self.inicio - timedelta(days=5)
        self.assertEqual(wl.recordatorios_debidos(self.inicio, ahora), ["E3"])

    def test_dentro_de_1d(self):
        ahora = self.inicio - timedelta(hours=20)
        self.assertEqual(wl.recordatorios_debidos(self.inicio, ahora), ["E3", "E4"])

    def test_dentro_de_1h(self):
        ahora = self.inicio - timedelta(minutes=30)
        self.assertEqual(wl.recordatorios_debidos(self.inicio, ahora), ["E3", "E4", "E5"])

    def test_ya_paso(self):
        ahora = self.inicio + timedelta(minutes=1)
        self.assertEqual(wl.recordatorios_debidos(self.inicio, ahora), [])


class TestEstado(unittest.TestCase):
    def test_marcar_y_consultar(self):
        est = {}
        self.assertFalse(wl.ya_enviado(est, "a@b.com", "intake"))
        wl.marcar_enviado(est, "a@b.com", "intake")
        self.assertTrue(wl.ya_enviado(est, "a@b.com", "intake"))
        # idempotente
        wl.marcar_enviado(est, "a@b.com", "intake")
        self.assertEqual(est["a@b.com"], ["intake"])


class TestCorreos(unittest.TestCase):
    CFG = {
        "titulo": "Título de prueba",
        "fecha_hora": "2026-08-05T10:00:00-05:00",
        "zona_texto": "hora Colombia",
        "meet_link": "https://meet.google.com/abc",
        "add_to_calendar_link": "https://calendar.google.com/x",
        "adelanto": "Un adelanto.",
        "youtube_url": "https://youtu.be/xyz",
        "cta_texto": "Mide primero.",
        "cta_url": "https://calendar.app.google/x",
    }

    def test_confirmacion_incluye_meet_y_titulo(self):
        asunto, html, texto = wl.email_confirmacion(self.CFG, "Ana")
        self.assertIn("Título de prueba", asunto)
        self.assertIn("https://meet.google.com/abc", html)
        self.assertIn("Ana", html)

    def test_recordatorio_e5(self):
        asunto, html, texto = wl.email_recordatorio(self.CFG, "", "E5")
        self.assertIn("En una hora", asunto)
        self.assertIn("meet.google.com", html)

    def test_post_incluye_youtube(self):
        asunto, html, texto = wl.email_post(self.CFG, "")
        self.assertIn("youtu.be/xyz", html)

    def test_fecha_legible(self):
        # 2026-08-05 es miércoles; 10:00 -05:00
        self.assertIn("miércoles 5 de agosto", wl._fecha_legible(self.CFG))
        self.assertIn("10:00 a. m.", wl._fecha_legible(self.CFG))


if __name__ == "__main__":
    unittest.main()
