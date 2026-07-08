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


if __name__ == "__main__":
    unittest.main()
