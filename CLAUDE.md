# CarbonBox Ops

Repo único de la operación de CarbonBox. **No hay otras carpetas.** Si encuentras
`_VIEJO_CRM CarbonBox`, `_VIEJO_Cobros CMR CarbonBox` o
`_VIEJO_Automatización de cotizaciones CarbonBox`, son archivo histórico:
no leerlas, no copiar de ellas, no trabajar en ellas.

## Antes de empezar a trabajar: sincronizar

```bash
git fetch origin && git status
```

Si dice `behind`, hacer `git pull --rebase` **antes** de tocar nada.

Esto no es ceremonia. En julio de 2026 esta carpeta local se quedó 2 commits atrás
sin que nadie lo notara, y se diagnosticó el estado del proyecto leyendo la copia
vieja. La conclusión ("hay trabajo sin respaldo") era falsa y casi provoca una
migración innecesaria.

## Qué hay aquí

| Carpeta | Qué es |
|---|---|
| `crm-scripts/` | Scripts Python (stdlib) que corren en el VPS. `crm_lib.py` es el cliente de la API de Twenty. |
| `tools/cotizar/` | Motor de cotizaciones: genera decks `.pptx`. Node + pptxgenjs, Python + Pillow. |
| `deploy/` | Docker Compose, Caddy, systemd, cron del CRM. |
| `rebrand/` | Parche para reconstruir la imagen personalizada de Twenty. |
| `branding/` | Logos, tokens de color, guías HTML. |
| `docs/` | Planes y specs. **Historia, no instrucciones** — ver abajo. |
| `scripts-ops/` | Operaciones puntuales ya ejecutadas y verificadas (2026-07-07/08): crear el campo `suscritoMarketing`, backfill de contactos existentes, y filtro `fuenteLead IS WEB` en el workflow de bienvenida. Registro histórico, no herramientas reutilizables — no se corren de nuevo. No se despliegan al VPS junto con `crm-scripts/`: se copiaron ahí una sola vez para ejecutarse contra `crm_lib.py` y no forman parte del despliegue regular. |

## El CRM

Twenty self-hosted en `https://crm.carbonbox.app`, VPS Hostinger `72.60.125.170`,
en Docker. Llave SSH: `C:\Users\USUARIO\.ssh\hostinger_vps` (está en **Windows**,
no en WSL).

**El VPS no usa git.** No tiene ningún clon de este repo. Los scripts se despliegan
copiándolos a `/root/crm-scripts/`:

```bash
scp -i "C:/Users/USUARIO/.ssh/hostinger_vps" crm-scripts/<script>.py root@72.60.125.170:/root/crm-scripts/
```

Commitear a GitHub **no** despliega nada. Son dos pasos separados.

Para verificar que el repo coincide con producción:

```bash
ssh -i "C:/Users/USUARIO/.ssh/hostinger_vps" root@72.60.125.170 'cd /root/crm-scripts && md5sum *.py | sort -k2'
```

## Qué se versiona y qué no

Regla: **lo que el código consume entra; lo que produce, no.**

Entra: código, `Insumos/`, `Recursos/`, `Logos/`, sistema de diseño, docs, branding.
No entra: `tools/cotizar/Cotizaciones/` (decks entregados — se respaldan por correo),
`node_modules/`, secretos, datos de clientes, dumps de la base.

Nunca commitear: tokens, `.env`, llaves, contraseñas, CSV de HubSpot,
transcripciones de clientes. El `.gitignore` cubre lo previsible; el criterio
lo pones tú.

Prueba de que la línea está bien: un clon fresco + `npm install` debe poder
generar un deck sin conseguir nada por fuera.

## Los docs son historia, no instrucciones

`docs/superpowers/plans/` y `specs/` registran **lo que se decidió en su momento**.
Varios se contradicen entre sí — dos de ellos señalan carpetas de desarrollo
distintas y opuestas, y eso fue lo que partió el proyecto en dos.

Este `CLAUDE.md` es la única fuente de verdad vigente. Si un doc lo contradice,
gana este archivo. Si un plan tiene casillas sin marcar, **no está hecho** aunque
el spec suene definitivo.

## Tests

En Windows no hay python. Los tests corren en WSL:

```bash
wsl -d Ubuntu-24.04 -- bash -lc 'cd "/mnt/c/Users/USUARIO/Claude/Projects/carbonbox-crm/crm-scripts" && python3 -m unittest discover -p "test_*.py"'
```

Verificado: 122 tests OK.

**Trampa real (16-jul-2026, costó tiempo):** todos los scripts hacen
`sys.path.insert(0, "/root/crm-scripts")`. En el VPS eso es correcto — es la
carpeta de despliegue real. Pero si dentro de **WSL** también existe un
`/root/crm-scripts`, esa línea lo mete de primero en `sys.path` y secuestra el
import: los tests cargan un `crm_lib` viejo en vez del de este repo y fallan con
errores tipo `module 'crm_lib' has no attribute 'X'`. Eso fue exactamente lo que
pasó: había una copia de rebusque del 6-jul dentro de WSL, 25 tests fallaban, y el
repo estaba sano — el problema era la copia vieja, no el código. Se apartó a
`/root/_VIEJO_crm-scripts-wsl-scratch`. Si los tests vuelven a fallar así,
primero revisar que `/root/crm-scripts` no exista dentro de WSL antes de
sospechar del código.
