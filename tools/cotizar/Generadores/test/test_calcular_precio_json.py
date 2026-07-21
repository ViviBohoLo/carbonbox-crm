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


def test_codigo_crm_equivale_al_nombre_literal():
    """El código de `sectorCarbonbox` debe dar el mismo precio que el nombre literal."""
    a = json.loads(run(["--sector", "COMUNICACIONES", "--empleados", "1072",
                        "--plan", "pro", "--json"]).stdout)
    b = json.loads(run(["--sector", "Comunicaciones", "--empleados", "1072",
                        "--plan", "pro", "--json"]).stdout)
    assert a["precio_final"] == b["precio_final"]
    assert a["sector"] == b["sector"] == "Comunicaciones"


def test_codigos_crm_con_etiqueta_distinta():
    """Los 6 sectores cuya etiqueta en el CRM NO coincide literalmente (comas, tildes, &)."""
    casos = {
        "MINERIA": 1845, "ENERGIA": 1476, "AGROPECUARIO": 1230,
        "SILVICULTURA": 1230, "RETAIL_ECOMMERCE": 1230, "TRANSPORTE": 984,
    }
    for codigo, base in casos.items():
        r = run(["--sector", codigo, "--empleados", "10", "--plan", "esencial", "--json"])
        assert r.returncode == 0, f"{codigo}: {r.stdout}{r.stderr}"
        d = json.loads(r.stdout)
        assert d["precio_final"] > 0, codigo
        # con 10 empleados pct_empleados=0, así que el precio parte de la base del sector
        assert d["precio_final"] >= base, f"{codigo}: {d['precio_final']} < base {base}"


def test_los_20_codigos_resuelven():
    sys.path.insert(0, BASE)
    import importlib.util
    spec = importlib.util.spec_from_file_location("cp", os.path.join(BASE, "calcular-precio.py"))
    cp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cp)
    assert len(cp.SECTOR_CRM) == 20
    for codigo, nombre in cp.SECTOR_CRM.items():
        assert nombre in cp.SECTORES, f"{codigo} apunta a un sector inexistente: {nombre}"
        assert cp.resolver_sector(codigo) == nombre
    # un nombre literal pasa derecho
    assert cp.resolver_sector("Industria manufacturera") == "Industria manufacturera"


if __name__ == "__main__":
    test_json_ok(); test_json_error_exit1()
    test_codigo_crm_equivale_al_nombre_literal()
    test_codigos_crm_con_etiqueta_distinta()
    test_los_20_codigos_resuelven()
    print("OK")
