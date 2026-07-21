import unittest
from datetime import datetime, timezone, timedelta
import reporte_semanal as r

AHORA = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)


def _opp(stage, name, dias=0, micros=0):
    d = (AHORA - timedelta(days=dias)).isoformat()
    return {"id": name, "name": name, "stage": stage,
            "fechaEntradaEtapa": d, "createdAt": d, "amount": {"amountMicros": micros}}


class TestReporte(unittest.TestCase):
    def test_estructura_y_contenido(self):
        allo = [_opp("PROPUESTA_ENVIADA", "PC System", 159, 12_500_000_000_000),
                _opp("LEAD_CAPTURADO", "Waya", 4)]
        openo = allo
        body = r.construir_reporte(allo, openo, AHORA)
        self.assertIn("REPORTE SEMANAL DEL PIPELINE", body)
        self.assertIn("Propuesta enviada", body)          # etapa en palabras
        self.assertIn("LEADS SIN PRIMER CONTACTO (1)", body)
        self.assertIn("NEGOCIOS ESTANCADOS (1)", body)
        self.assertIn("hace 159 días (límite 7 días)", body)
        self.assertIn("https://crm.carbonbox.app", body)
        self.assertIn("**PC System**", body)                 # nombre en negrilla
        self.assertNotIn("localhost", body)
        self.assertNotIn("④", body)

    def test_sin_riesgo_muestra_ok(self):
        allo = [_opp("CERRADO_GANADO", "Ganado", 3, 1_000_000)]
        body = r.construir_reporte(allo, [], AHORA)
        self.assertIn("Sin negocios en riesgo", body)

    def test_licitacion_no_aparece_en_estancados(self):
        allo = [_opp("PROPUESTA_ENVIADA", "Licitación - Banco Agrario", 30)]
        body = r.construir_reporte(allo, allo, AHORA, link_fn=lambda it: "https://x.co/s")
        self.assertNotIn("NEGOCIOS ESTANCADOS", body)
        self.assertNotIn("Enviar recordatorio", body)
        self.assertIn("Sin etapa de licitación marcada", body)   # no desaparece

    def test_bloque_licitaciones(self):
        d = (AHORA.date() + timedelta(days=4)).isoformat()
        lic = {"id": "L1", "name": "Licitación - Banco", "stage": "EN_NEGOCIACION",
               "fechaEntradaEtapa": (AHORA - timedelta(days=60)).isoformat(),
               "createdAt": (AHORA - timedelta(days=60)).isoformat(),
               "amount": {"amountMicros": 0},
               "etapaLicitacion": "ABIERTA", "fechaCierreLicitacion": d}
        ev = dict(lic, id="L2", name="Licitación - Alcaldía",
                  etapaLicitacion="EVALUACION", fechaCierreLicitacion=None)
        body = r.construir_reporte([lic, ev], [lic, ev], AHORA)
        self.assertIn("LICITACIONES", body)
        self.assertIn("cierra en 4 días", body)
        self.assertIn("En evaluación", body)
        self.assertIn("Licitación - Alcaldía", body)

    def test_enlace_recordatorio(self):
        allo = [_opp("PROPUESTA_ENVIADA", "PC System", 159)]
        body = r.construir_reporte(allo, allo, AHORA, link_fn=lambda it: "https://x.co/s?opp=" + it["id"])
        self.assertIn("[Enviar recordatorio](https://x.co/s?opp=PC System)", body)


if __name__ == "__main__":
    unittest.main()
