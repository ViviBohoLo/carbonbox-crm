import unittest
import gtasks_sync as g

T = {"title": "Llamar a Ana", "notes": "ficha", "due": "2026-07-10T00:00:00.000Z"}


class TestPlanSync(unittest.TestCase):
    def test_crea_tarea_nueva(self):
        acc, nuevo = g.plan_sync({"c1": T}, {}, {})
        self.assertEqual(acc, [{"op": "create", "crm": "c1", "data": T}])

    def test_google_completada_marca_crm_done(self):
        gb = {"g1": {"status": "completed", "title": T["title"], "notes": T["notes"], "due": T["due"]}}
        acc, nuevo = g.plan_sync({"c1": T}, gb, {"c1": "g1"})
        self.assertIn({"op": "complete_crm", "crm": "c1"}, acc)
        self.assertNotIn("c1", nuevo)

    def test_crm_cerrada_completa_google(self):
        gb = {"g1": {"status": "needsAction", "title": T["title"], "notes": T["notes"], "due": T["due"]}}
        acc, nuevo = g.plan_sync({}, gb, {"c1": "g1"})     # c1 ya no está abierta
        self.assertIn({"op": "complete_google", "g": "g1"}, acc)
        self.assertNotIn("c1", nuevo)

    def test_sin_cambios_no_hace_nada(self):
        gb = {"g1": {"status": "needsAction", "title": T["title"], "notes": T["notes"], "due": T["due"]}}
        acc, nuevo = g.plan_sync({"c1": T}, gb, {"c1": "g1"})
        self.assertEqual(acc, [])

    def test_cambio_de_titulo_actualiza(self):
        gb = {"g1": {"status": "needsAction", "title": "viejo", "notes": T["notes"], "due": T["due"]}}
        acc, nuevo = g.plan_sync({"c1": T}, gb, {"c1": "g1"})
        self.assertEqual(acc, [{"op": "update", "g": "g1", "data": T}])

    def test_google_borrada_se_recrea(self):
        acc, nuevo = g.plan_sync({"c1": T}, {}, {"c1": "g1"})   # mapeada pero ya no en google
        self.assertEqual(acc, [{"op": "create", "crm": "c1", "data": T}])


class TestTituloGtask(unittest.TestCase):
    """La Tasks API descarta la hora del due -> la hora va en el TÍTULO (hora Bogotá)."""

    def test_agrega_fecha_y_hora_bogota(self):
        # 19:30 UTC = 2:30pm en Bogotá (UTC-5)
        self.assertEqual(g.titulo_gtask("📞 Contactar a X", "2026-07-07T19:30:00.000Z"),
                         "📞 Contactar a X — 07/07 2:30pm")

    def test_manana_y_mediodia(self):
        self.assertEqual(g.titulo_gtask("T", "2026-07-08T13:05:00.000Z"), "T — 08/07 8:05am")
        self.assertEqual(g.titulo_gtask("T", "2026-07-08T17:00:00.000Z"), "T — 08/07 12:00pm")

    def test_medianoche_bogota(self):
        self.assertEqual(g.titulo_gtask("T", "2026-07-08T05:00:00.000Z"), "T — 08/07 12:00am")

    def test_cruce_de_dia(self):
        # 03:00 UTC del día 8 = 10:00pm del día 7 en Bogotá
        self.assertEqual(g.titulo_gtask("T", "2026-07-08T03:00:00.000Z"), "T — 07/07 10:00pm")

    def test_sin_due_queda_igual(self):
        self.assertEqual(g.titulo_gtask("T", None), "T")
        self.assertEqual(g.titulo_gtask("T", ""), "T")


if __name__ == "__main__":
    unittest.main()
