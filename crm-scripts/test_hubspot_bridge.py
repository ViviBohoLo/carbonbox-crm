import unittest
import hubspot_bridge as hb


class TestEsDuplicado(unittest.TestCase):
    def test_detecta_duplicado_twenty(self):
        ex = RuntimeError('[{"message": "A duplicate entry was detected", '
                          '"extensions": {"code": "BAD_USER_INPUT"}}]')
        self.assertTrue(hb.es_duplicado(ex))

    def test_detecta_already_exists(self):
        self.assertTrue(hb.es_duplicado(Exception("This record already exists")))

    def test_error_transitorio_no_es_duplicado(self):
        self.assertFalse(hb.es_duplicado(RuntimeError("Connection timeout")))
        self.assertFalse(hb.es_duplicado(RuntimeError("LIMIT_REACHED")))
        self.assertFalse(hb.es_duplicado(Exception("500 Internal Server Error")))


if __name__ == "__main__":
    unittest.main()
