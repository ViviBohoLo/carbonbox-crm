import json, subprocess, sys, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(args):
    r = subprocess.run([sys.executable, os.path.join(BASE, "calcular-precio.py")] + args,
                       capture_output=True, text=True)
    return r


def test_json_ok():
    r = run(["--sector", "Industria manufacturera", "--empleados", "100", "--plan", "pro", "--json"])
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    assert set(["precio_final", "precio_mensual", "precio_atica", "precio_mensual_atica",
                "plan", "sector", "tamano"]) <= set(d)
    assert isinstance(d["precio_final"], int) and d["precio_final"] > 0
    assert d["precio_atica"] == round(d["precio_final"] * 0.90)


def test_json_error_exit1():
    r = run(["--sector", "Sector Inexistente", "--empleados", "100", "--plan", "pro", "--json"])
    assert r.returncode == 1
    assert "error" in json.loads(r.stdout)


if __name__ == "__main__":
    test_json_ok(); test_json_error_exit1(); print("OK")
