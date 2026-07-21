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


class TestHitosConfigurables(unittest.TestCase):
    LIC = [15, 7, 3, 1]

    def test_renovacion_sigue_igual_sin_parametro(self):
        self.assertEqual(c.hito_a_disparar(90, []), (90, [90]))
        self.assertEqual(c.hito_a_disparar(59, [90]), (60, [90, 60]))

    def test_licitacion_dispara_15(self):
        self.assertEqual(c.hito_a_disparar(12, [], hitos=self.LIC), (15, [15]))

    def test_licitacion_no_repite(self):
        self.assertEqual(c.hito_a_disparar(10, [15], hitos=self.LIC), (None, [15]))

    def test_licitacion_dispara_7_luego_3(self):
        self.assertEqual(c.hito_a_disparar(5, [15], hitos=self.LIC), (7, [15, 7]))
        self.assertEqual(c.hito_a_disparar(2, [15, 7], hitos=self.LIC), (3, [15, 7, 3]))

    def test_licitacion_lejos_resetea(self):
        self.assertEqual(c.hito_a_disparar(40, [15, 7], hitos=self.LIC), (None, []))


class TestLicitacion(unittest.TestCase):
    def test_detecta(self):
        self.assertTrue(c.es_licitacion("Licitación - Banco Agrario de Colombia"))
        self.assertTrue(c.es_licitacion("Licitación :HC + Huella Hídrica - Superservicios"))
        self.assertTrue(c.es_licitacion("Estudio de mercado - Alcaldía"))
        self.assertFalse(c.es_licitacion("HC Organizacional - Colsubsidio UMed"))

    def test_riesgo_ya_no_marca_sino_que_excluye(self):
        opps = [_opp("PROPUESTA_ENVIADA", "Licitación - Banco", 30),
                _opp("PROPUESTA_ENVIADA", "HC - ACME", 30)]
        _, est = c.clasificar_riesgo(opps, AHORA)
        self.assertEqual([e["nombre"] for e in est], ["HC - ACME"])


def _lic(nombre, etapa, dias_al_cierre=None):
    o = {"id": nombre, "name": nombre, "stage": "EN_NEGOCIACION",
         "fechaEntradaEtapa": (AHORA - timedelta(days=60)).isoformat(),
         "createdAt": (AHORA - timedelta(days=60)).isoformat(),
         "amount": {"amountMicros": 0}, "etapaLicitacion": etapa,
         "fechaCierreLicitacion": None}
    if dias_al_cierre is not None:
        o["fechaCierreLicitacion"] = (AHORA.date() + timedelta(days=dias_al_cierre)).isoformat()
    return o


class TestLicitacionCampo(unittest.TestCase):
    def test_detecta_por_campo(self):
        self.assertTrue(c.es_licitacion({"name": "Convenio X", "etapaLicitacion": "ABIERTA"}))
        self.assertFalse(c.es_licitacion({"name": "HC - ACME", "etapaLicitacion": None}))

    def test_respaldo_por_nombre(self):
        self.assertTrue(c.es_licitacion({"name": "Licitación - Banco", "etapaLicitacion": None}))
        self.assertTrue(c.es_licitacion("Licitación - Banco"))

    def test_riesgo_excluye_licitaciones(self):
        opps = [_lic("Licitación - Banco", "ABIERTA", 10),
                _opp("PROPUESTA_ENVIADA", "HC - ACME", 30)]
        _, est = c.clasificar_riesgo(opps, AHORA)
        self.assertEqual([e["nombre"] for e in est], ["HC - ACME"])

    def test_clasificar_licitaciones(self):
        opps = [_lic("Lic A", "ABIERTA", 12), _lic("Lic B", "ABIERTA", 3),
                _lic("Lic C", "ABIERTA"), _lic("Lic D", "EVALUACION"),
                _lic("Lic E", "ADJUDICADA", 5)]
        ab, ev, sc = c.clasificar_licitaciones(opps, AHORA.date())
        self.assertEqual([x["nombre"] for x in ab], ["Lic B", "Lic A", "Lic C"])
        self.assertEqual(ab[0]["dias"], 3)
        self.assertTrue(ab[2]["sin_fecha"])
        self.assertEqual([x["nombre"] for x in ev], ["Lic D"])
        self.assertEqual(sc, [])

    def test_licitacion_sin_etapa_no_desaparece(self):
        """Detectada por nombre pero sin etapa marcada: sale en 'sin clasificar',
        no se pierde entre estancados y el bloque de licitaciones."""
        opps = [_opp("PROPUESTA_ENVIADA", "Licitación - Banco", 30)]
        _, est = c.clasificar_riesgo(opps, AHORA)
        ab, ev, sc = c.clasificar_licitaciones(opps, AHORA.date())
        self.assertEqual(est, [])
        self.assertEqual([x["nombre"] for x in sc], ["Licitación - Banco"])


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
