import unittest
from datetime import datetime, timezone, timedelta
import crm_lib as c

AHORA = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)


class TestFormato(unittest.TestCase):
    def test_pesos_formato_colombiano(self):
        self.assertEqual(c.pesos(43806832), "$43.806.832")
        self.assertEqual(c.pesos(0), "$0")

    def test_antiguedad_dias(self):
        self.assertEqual(c.antiguedad_texto(AHORA - timedelta(days=159, hours=7), AHORA), "159 días")

    def test_antiguedad_horas(self):
        self.assertEqual(c.antiguedad_texto(AHORA - timedelta(hours=5), AHORA), "5 horas")

    def test_antiguedad_singular(self):
        self.assertEqual(c.antiguedad_texto(AHORA - timedelta(days=1, hours=1), AHORA), "1 día")

    def test_antiguedad_minutos(self):
        self.assertEqual(c.antiguedad_texto(AHORA - timedelta(minutes=40), AHORA), "40 minutos")

    def test_etapas_nombre_y_limite_texto(self):
        self.assertEqual(c.ETAPAS["PROPUESTA_ENVIADA"]["nombre"], "Propuesta enviada")
        self.assertEqual(c.ETAPAS["PROPUESTA_ENVIADA"]["sla_txt"], "7 días")
        self.assertEqual(c.ETAPAS["LEAD_CAPTURADO"]["sla_txt"], "60 minutos")
        self.assertIsNone(c.ETAPAS["DEMO"]["sla"])          # Demo a futuro: no genera alertas
        self.assertEqual(c.ETAPAS["EN_NEGOCIACION"]["sla"], timedelta(days=21))

    def test_nombre_etapa_desconocida(self):
        self.assertEqual(c.nombre_etapa("RARO"), "RARO")


def _opp(stage, name, dias, micros=0):
    d = (AHORA - timedelta(days=dias)).isoformat()
    return {"id": name, "name": name, "stage": stage,
            "fechaEntradaEtapa": d, "createdAt": d, "amount": {"amountMicros": micros}}


class TestRiesgo(unittest.TestCase):
    def test_separa_leads_de_estancados_y_ordena(self):
        opps = [
            _opp("LEAD_CAPTURADO", "Waya", 4),
            _opp("PROPUESTA_ENVIADA", "PC System", 159, 12_500_000_000_000),
            _opp("PROPUESTA_ENVIADA", "Los Cobos", 136),
            _opp("EN_NEGOCIACION", "Banco", 5),          # 5 días < límite 21 -> NO en riesgo
        ]
        leads, estancados = c.clasificar_riesgo(opps, AHORA)
        self.assertEqual([l["nombre"] for l in leads], ["Waya"])
        self.assertEqual([e["nombre"] for e in estancados], ["PC System", "Los Cobos"])
        self.assertEqual(estancados[0]["antiguedad"], "159 días")
        self.assertEqual(estancados[0]["limite"], "7 días")
        self.assertEqual(estancados[0]["valor"], "$12.500.000")

    def test_demo_no_entra_en_riesgo(self):
        leads, estancados = c.clasificar_riesgo([_opp("DEMO", "X", 99)], AHORA)
        self.assertEqual((leads, estancados), ([], []))


class TestEmailHtml(unittest.TestCase):
    def test_wrap_pre_conserva_saltos(self):
        h = c.cuerpo_html("línea 1\nlínea 2")
        self.assertTrue(h.startswith("<pre"))
        self.assertIn("white-space:pre-wrap", h)
        self.assertIn("línea 1\nlínea 2", h)

    def test_escapa_html(self):
        h = c.cuerpo_html("a & b <x>")
        self.assertIn("&amp;", h)
        self.assertIn("&lt;x&gt;", h)
        self.assertNotIn("<x>", h)

    def test_negrita(self):
        h = c.cuerpo_html("hola **mundo** fin")
        self.assertIn("<strong>mundo</strong>", h)
        self.assertNotIn("**", h)

    def test_enlace_markdown(self):
        h = c.cuerpo_html("ver [Enviar recordatorio](https://x.co/s?a=1&b=2)")
        self.assertIn('<a href="https://x.co/s?a=1&amp;b=2">Enviar recordatorio</a>', h)


class TestLicitacion(unittest.TestCase):
    def test_detecta(self):
        self.assertTrue(c.es_licitacion("Licitación - Banco Agrario de Colombia"))
        self.assertTrue(c.es_licitacion("Licitación :HC + Huella Hídrica - Superservicios"))
        self.assertTrue(c.es_licitacion("Estudio de mercado - Alcaldía"))
        self.assertFalse(c.es_licitacion("HC Organizacional - Colsubsidio UMed"))

    def test_riesgo_marca_y_cambia_accion(self):
        opps = [_opp("PROPUESTA_ENVIADA", "Licitación - Banco", 30),
                _opp("PROPUESTA_ENVIADA", "HC - ACME", 30)]
        _, est = c.clasificar_riesgo(opps, AHORA)
        lic = [e for e in est if e["nombre"].startswith("Licitación")][0]
        com = [e for e in est if e["nombre"].startswith("HC")][0]
        self.assertTrue(lic["licitacion"])
        self.assertIn("TDR", lic["accion"])
        self.assertFalse(com["licitacion"])
        self.assertIn("propuesta", com["accion"].lower())


class TestHitoAgenda(unittest.TestCase):
    def test_antes_de_3_no_dispara(self):
        self.assertEqual(c.hito_agenda(2, []), (None, []))

    def test_dispara_ronda_1_al_dia_3(self):
        self.assertEqual(c.hito_agenda(3, []), (3, [3]))

    def test_no_repite_la_ronda(self):
        self.assertEqual(c.hito_agenda(4, [3]), (None, [3]))

    def test_dispara_ronda_2_al_dia_6(self):
        self.assertEqual(c.hito_agenda(6, [3]), (6, [3, 6]))

    def test_ambas_rondas_ya_vistas(self):
        self.assertEqual(c.hito_agenda(8, [3, 6]), (None, [3, 6]))


if __name__ == "__main__":
    unittest.main()
