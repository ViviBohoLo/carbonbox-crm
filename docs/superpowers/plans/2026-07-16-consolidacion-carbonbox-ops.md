# Consolidación en `carbonbox-ops` — Plan de implementación

> **Para agentes:** SUB-SKILL REQUERIDA: usar `superpowers:subagent-driven-development` (recomendado) o `superpowers:executing-plans` para implementar tarea por tarea. Los pasos usan checkbox (`- [ ]`).

**Spec:** `docs/superpowers/specs/2026-07-16-consolidacion-carbonbox-ops-design.md`

**Goal:** Consolidar cuatro carpetas locales en un solo repo `carbonbox-ops` respaldado en GitHub, con un `CLAUDE.md` que elimine la ambigüedad sobre dónde vive el código.

**Architecture:** El repo `carbonbox-crm` (ya verificado como superconjunto de `CRM CarbonBox` y reflejo exacto del VPS) se renombra a `carbonbox-ops` y absorbe el motor de cotizaciones (`tools/cotizar/`) y el SOP de cobros (`cobros/`). Las carpetas viejas se archivan con prefijo `_VIEJO_`, no se borran.

**Tech Stack:** git, GitHub CLI (`gh`), Python 3 (stdlib), Node + pptxgenjs.

## Global Constraints

- **El VPS no se toca.** Verificado 16-jul: no tiene clon del repo, el cron no usa git, los scripts llegan por copia manual. Ningún paso de este plan ejecuta nada en `72.60.125.170`. Twenty sigue corriendo.
- **Datos de clientes fuera de git.** El README declara: "no contiene datos de clientes ni secretos". Aplica a los CSV de HubSpot, transcripciones y `Cotizaciones/`.
- **Línea de corte para binarios:** lo que el código **consume** entra al repo (`Recursos/`, `Logos/`); lo que **produce** queda fuera (`Cotizaciones/`).
- **Nada se borra.** Las carpetas viejas se renombran con prefijo `_VIEJO_`. El borrado lo decide Viviana después.
- **Las credenciales de Helisa las maneja Viviana, no el agente.** Tarea 0 es humana y bloqueante.
- **Rutas con espacios y tildes**: siempre entre comillas. Base: `C:\Users\USUARIO\Claude\Projects\`.

---

## Tarea 0: Sacar las credenciales de Helisa — HUMANA, BLOQUEANTE

**Responsable: Viviana. El agente no toca este archivo.**

**Files:**
- Eliminar: `Cobros CMR CarbonBox/terminal Helisa.txt`

Contiene dos juegos de usuario/contraseña del portal Helisa Cloud en texto plano. **Debe salir antes de la Tarea 7** (cuando `cobros/` entra a git). Después de un commit, borrarlo no lo saca del historial.

- [ ] **Paso 1: Viviana copia las credenciales a su gestor de contraseñas**

- [ ] **Paso 2: Viviana elimina el archivo del disco**

- [ ] **Paso 3: El agente verifica que ya no existe**

```bash
cd "C:/Users/USUARIO/Claude/Projects"
ls "Cobros CMR CarbonBox/terminal Helisa.txt" 2>&1
```
Esperado: `No such file or directory`

**Si el archivo sigue ahí, DETENER.** No continuar a la Tarea 7.

---

## Tarea 1: Copia de seguridad

**Files:**
- Crear: `C:/Users/USUARIO/Claude/_BACKUP_2026-07-16/` (4 carpetas)

- [ ] **Paso 1: Copiar las cuatro carpetas**

```bash
cd "C:/Users/USUARIO/Claude/Projects"
mkdir -p "C:/Users/USUARIO/Claude/_BACKUP_2026-07-16"
cp -r "CRM CarbonBox" "C:/Users/USUARIO/Claude/_BACKUP_2026-07-16/"
cp -r "carbonbox-crm" "C:/Users/USUARIO/Claude/_BACKUP_2026-07-16/"
cp -r "Cobros CMR CarbonBox" "C:/Users/USUARIO/Claude/_BACKUP_2026-07-16/"
cp -r "Automatización de cotizaciones CarbonBox" "C:/Users/USUARIO/Claude/_BACKUP_2026-07-16/"
```

- [ ] **Paso 2: Verificar que las cuatro llegaron**

```bash
ls -la "C:/Users/USUARIO/Claude/_BACKUP_2026-07-16/"
du -sh "C:/Users/USUARIO/Claude/_BACKUP_2026-07-16/"*
```
Esperado: 4 carpetas. `Automatización de cotizaciones CarbonBox` ≈ 80 MB, `carbonbox-crm` ≈ 14 MB, `CRM CarbonBox` ≈ 3 MB, `Cobros CMR CarbonBox` ≈ 30 KB.

**Si falta alguna, DETENER.** Sin backup no se sigue.

---

## Tarea 2: Línea base de tests

Confirma que el repo está sano antes de tocarlo.

**Files:**
- Test: `carbonbox-crm/crm-scripts/test_*.py`

- [ ] **Paso 1: Sincronizar con GitHub**

```bash
cd "C:/Users/USUARIO/Claude/Projects/carbonbox-crm"
git fetch origin && git status
```
Esperado: `Your branch is up to date with 'origin/main'` (o `ahead` por los commits de spec).

- [ ] **Paso 2: Correr los tests**

```bash
cd "C:/Users/USUARIO/Claude/Projects/carbonbox-crm/crm-scripts"
python -m unittest discover -p "test_*.py" -v 2>&1 | tail -20
```
Esperado: `OK`.

**Anotar el número de tests.** Debe seguir igual al final de la migración. Si algo falla ya, investigar antes de seguir — no se migra sobre un repo roto.

---

## Tarea 3: Preparar el `.gitignore` para cotizar

**Antes** de copiar un solo archivo de cotizar, para que `Cotizaciones/` y `node_modules/` nunca toquen el historial.

**Files:**
- Modificar: `carbonbox-crm/.gitignore`

- [ ] **Paso 1: Añadir el bloque de cotizar al final del `.gitignore`**

```gitignore

# === tools/cotizar ===
# Regla: lo que el código CONSUME entra (Recursos/, Logos/);
# lo que PRODUCE queda fuera. Los decks se respaldan por correo.
tools/cotizar/Cotizaciones/
tools/cotizar/node_modules/
node_modules/

# Temporales de LibreOffice (quedan al convertir a PDF)
*.tmp
.~lock.*#
```

- [ ] **Paso 2: Commit**

```bash
cd "C:/Users/USUARIO/Claude/Projects/carbonbox-crm"
git add .gitignore
git commit -m "chore(gitignore): preparar exclusiones para tools/cotizar"
```

---

## Tarea 4: Mover el motor de cotizar a `tools/cotizar/`

Lo único sin respaldo en todo CarbonBox. Es la tarea urgente.

**Files:**
- Crear: `carbonbox-crm/tools/cotizar/` (desde `Automatización de cotizaciones CarbonBox`)
- Modificar: `carbonbox-crm/tools/cotizar/package.json`

**Interfaces:**
- Produce: la ruta `tools/cotizar/Generadores/calcular-precio.py` y `tools/cotizar/Insumos/`, que la Etapa 1 de cotizar consumirá junto a `crm-scripts/crm_lib.py`.

- [ ] **Paso 1: Copiar lo que se versiona**

```bash
cd "C:/Users/USUARIO/Claude/Projects"
SRC="Automatización de cotizaciones CarbonBox"
DST="carbonbox-crm/tools/cotizar"
mkdir -p "$DST"
cp -r "$SRC/Generadores" "$DST/"
cp -r "$SRC/Insumos" "$DST/"
cp -r "$SRC/Recursos" "$DST/"
cp -r "$SRC/Logos" "$DST/"
cp -r "$SRC/Sistema de diseño CarbonBox" "$DST/"
cp "$SRC/README.md" "$DST/"
cp "$SRC/package.json" "$DST/"
cp "$SRC/package-lock.json" "$DST/"
```

- [ ] **Paso 2: Copiar los entregables (van al disco, no a git)**

```bash
cd "C:/Users/USUARIO/Claude/Projects"
cp -r "Automatización de cotizaciones CarbonBox/Cotizaciones" "carbonbox-crm/tools/cotizar/"
```

- [ ] **Paso 3: Copiar los docs de cotizar al árbol de docs del repo**

```bash
cd "C:/Users/USUARIO/Claude/Projects"
SRC="Automatización de cotizaciones CarbonBox/docs/superpowers"
cp "$SRC/specs/2026-07-06-motor-contenido-cotizaciones-design.md" "carbonbox-crm/docs/superpowers/specs/"
cp "$SRC/plans/2026-07-06-cotizar-etapa1.md" "carbonbox-crm/docs/superpowers/plans/"
```

- [ ] **Paso 4: Limpiar los temporales de LibreOffice**

```bash
cd "C:/Users/USUARIO/Claude/Projects/carbonbox-crm/tools/cotizar"
find . -name "*.tmp" -delete
find . -name ".~lock.*#" -delete
```

- [ ] **Paso 5: Arreglar el `package.json`** (hoy no tiene `name` ni `scripts`)

```json
{
  "name": "carbonbox-cotizar",
  "version": "1.0.0",
  "description": "Generador de decks de cotización de CarbonBox",
  "private": true,
  "scripts": {
    "precio": "python Generadores/calcular-precio.py",
    "precio:eventos": "python Generadores/calcular-precio-eventos.py"
  },
  "dependencies": {
    "pptxgenjs": "^4.0.1"
  }
}
```

- [ ] **Paso 6: Verificar que git ve lo correcto y NO ve lo excluido**

```bash
cd "C:/Users/USUARIO/Claude/Projects/carbonbox-crm"
echo "--- ¿Cotizaciones excluida? (debe decir nada) ---"
git status --porcelain | grep -i "Cotizaciones/" || echo "OK: Cotizaciones excluida"
echo "--- ¿node_modules excluida? ---"
git status --porcelain | grep -i "node_modules" || echo "OK: node_modules excluida"
echo "--- ¿Recursos y Logos SÍ incluidos? ---"
git status --porcelain | grep -ciE "tools/cotizar/(Recursos|Logos)/"
```
Esperado: las dos primeras dicen `OK: ... excluida`. La tercera devuelve un número **mayor que 0** (34 archivos: 27 de Recursos + 7 de Logos).

**Si `Cotizaciones/` aparece, DETENER** y arreglar el `.gitignore` antes de commitear. Después del commit ya no sale del historial.

- [ ] **Paso 7: Commit**

```bash
cd "C:/Users/USUARIO/Claude/Projects/carbonbox-crm"
git add tools/ docs/
git commit -m "feat(cotizar): incorporar el motor de cotizaciones como tools/cotizar

Primer respaldo de este trabajo: la carpeta original no tenía git.
Entran generadores, insumos, assets (Recursos/, Logos/) y sistema
de diseño. Los decks entregados quedan fuera: su respaldo es el
correo con que se envían al cliente."
```

- [ ] **Paso 8: Confirmar el peso del repo**

```bash
cd "C:/Users/USUARIO/Claude/Projects/carbonbox-crm"
git count-objects -vH | grep size-pack
```
Esperado: bastante por debajo de 100 MB. Si se disparó, algo grande entró — revisar antes de subir.

---

## Tarea 5: Verificar que un clon fresco puede generar un deck

La prueba de que la línea consume/produce quedó bien trazada. **Si esto falla, el repo está incompleto** aunque los tests pasen.

**Files:**
- Temporal: `C:/Users/USUARIO/AppData/Local/Temp/claude-clone-test/`

- [ ] **Paso 1: Clonar el repo local en una carpeta limpia**

```bash
rm -rf "C:/Users/USUARIO/AppData/Local/Temp/claude-clone-test"
git clone "C:/Users/USUARIO/Claude/Projects/carbonbox-crm" "C:/Users/USUARIO/AppData/Local/Temp/claude-clone-test"
```

- [ ] **Paso 2: Confirmar que los assets viajaron y los entregables no**

```bash
cd "C:/Users/USUARIO/AppData/Local/Temp/claude-clone-test/tools/cotizar"
echo "Recursos: $(ls Recursos/*.png 2>/dev/null | wc -l) png (esperado: 27)"
echo "Logos: $(ls Logos/*.png 2>/dev/null | wc -l) png (esperado: 7)"
echo "Cotizaciones existe?: $(test -d Cotizaciones && echo 'SI - MAL' || echo 'no - OK')"
```

- [ ] **Paso 3: Instalar dependencias y generar un deck**

```bash
cd "C:/Users/USUARIO/AppData/Local/Temp/claude-clone-test/tools/cotizar"
npm install 2>&1 | tail -3
node Generadores/generador-pptx-pepsico.js 2>&1 | tail -5
```
Esperado: se escribe un `.pptx` sin errores de archivo faltante.

**Si truena por un asset que no existe**, ese asset se consume y quedó fuera. Añadirlo al repo (quitarlo del `.gitignore`), commitear, y repetir esta tarea.

- [ ] **Paso 4: Limpiar el clon de prueba**

```bash
rm -rf "C:/Users/USUARIO/AppData/Local/Temp/claude-clone-test"
```

---

## Tarea 6: Rescatar lo aprovechable de `CRM CarbonBox`

No tiene código propio (verificado por diff: el repo le gana en todo). Solo hay dos artefactos que no están en el repo, y **son datos de clientes: no entran a git.**

**Files:**
- Crear: `C:/Users/USUARIO/Claude/_DATOS_CarbonBox/`

- [ ] **Paso 1: Mover los datos a una carpeta fuera del repo**

```bash
cd "C:/Users/USUARIO/Claude/Projects"
mkdir -p "C:/Users/USUARIO/Claude/_DATOS_CarbonBox"
cp -r "CRM CarbonBox/Archivos Hubspot" "C:/Users/USUARIO/Claude/_DATOS_CarbonBox/"
cp "CRM CarbonBox/transcripción video de youtube.docx" "C:/Users/USUARIO/Claude/_DATOS_CarbonBox/"
ls -la "C:/Users/USUARIO/Claude/_DATOS_CarbonBox/"
```
Esperado: `Archivos Hubspot/` (2 CSV, 2.3 MB) y el `.docx` (184 KB).

- [ ] **Paso 2: Confirmar que no queda código sin rescatar**

```bash
cd "C:/Users/USUARIO/Claude/Projects"
diff -rq "CRM CarbonBox/vps/crm-scripts" "carbonbox-crm/crm-scripts" 2>&1 | grep "^Only in CRM CarbonBox" || echo "OK: CRM CarbonBox no tiene ningún script propio"
```
Esperado: `OK: CRM CarbonBox no tiene ningún script propio`.

**Si aparece algún archivo, DETENER** y evaluarlo antes de archivar la carpeta.

Se descarta sin rescatar: `.playwright-mcp/` (snapshots del 06-jul), `__pycache__/`, `nul` (artefacto de `> nul` en shell POSIX).

---

## Tarea 7: Incorporar cobros

**Requiere la Tarea 0 completada.**

**Files:**
- Crear: `carbonbox-crm/cobros/` (3 `.md` desde `Cobros CMR CarbonBox`)

- [ ] **Paso 1: Verificar de nuevo que las credenciales no están**

```bash
cd "C:/Users/USUARIO/Claude/Projects"
ls "Cobros CMR CarbonBox/terminal Helisa.txt" 2>&1
```
Esperado: `No such file or directory`.

**Si existe, DETENER.** Volver a la Tarea 0.

- [ ] **Paso 2: Copiar solo los tres documentos, por nombre explícito**

No usar `cp -r` de la carpeta entera: copiar archivo por archivo evita arrastrar algo no visto.

```bash
cd "C:/Users/USUARIO/Claude/Projects"
mkdir -p "carbonbox-crm/cobros"
cp "Cobros CMR CarbonBox/Estado y memoria del proyecto.md" "carbonbox-crm/cobros/"
cp "Cobros CMR CarbonBox/Instrucciones - Flujo mensual Cobros.md" "carbonbox-crm/cobros/"
cp "Cobros CMR CarbonBox/Plan - Flujo Cobros CarbonBox.md" "carbonbox-crm/cobros/"
ls -la "carbonbox-crm/cobros/"
```
Esperado: exactamente 3 archivos `.md`. (El `CLAUDE.md` de origen está vacío, 0 bytes — no se copia.)

- [ ] **Paso 3: Revisar que no quedaron credenciales dentro de los `.md`**

```bash
cd "C:/Users/USUARIO/Claude/Projects/carbonbox-crm/cobros"
grep -rniE "contrase|password|passw|usuario:|clave" . | head -10 || echo "OK: sin rastros evidentes"
```

**Leer lo que salga.** Si hay una credencial real en un `.md`, quitarla antes de commitear. Menciones inocuas ("el usuario debe ingresar a Helisa") están bien.

- [ ] **Paso 4: Commit**

```bash
cd "C:/Users/USUARIO/Claude/Projects/carbonbox-crm"
git add cobros/
git commit -m "feat(cobros): incorporar el SOP de cobros Helisa -> Twenty

Solo documentos. Las credenciales de Helisa se sacaron a un gestor
de contraseñas antes de este commit y no entran al historial."
```

---

## Tarea 8: Escribir el `CLAUDE.md`

La pieza que impide la recaída. Debe responder sin ambigüedad: dónde vive el código, cómo llega al VPS, **cómo sincronizar antes de trabajar** (el fallo que causó el desfase), y qué se versiona.

**Files:**
- Crear: `carbonbox-crm/CLAUDE.md`

- [ ] **Paso 1: Escribir el archivo**

````markdown
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
| `cobros/` | SOP del flujo mensual de cobros (Helisa → Twenty). Solo documentos. |
| `deploy/` | Docker Compose, Caddy, systemd, cron del CRM. |
| `rebrand/` | Parche para reconstruir la imagen personalizada de Twenty. |
| `branding/` | Logos, tokens de color, guías HTML. |
| `docs/` | Planes y specs. **Historia, no instrucciones** — ver abajo. |

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

```bash
cd crm-scripts && python -m unittest discover -p "test_*.py" -v
```
````

- [ ] **Paso 2: Decidir sobre `.superpowers/`** (hoy sin trackear)

```bash
cd "C:/Users/USUARIO/Claude/Projects/carbonbox-crm"
cat .superpowers/sdd/progress.md
```

Es el checklist de una rama ya terminada (`feat/transcripts-por-empresa`, 7/7). Es estado efímero, no documentación: añadir `.superpowers/` al `.gitignore`.

- [ ] **Paso 3: Commit**

```bash
cd "C:/Users/USUARIO/Claude/Projects/carbonbox-crm"
echo "" >> .gitignore
echo "# Estado efímero de sesiones de trabajo" >> .gitignore
echo ".superpowers/" >> .gitignore
git add CLAUDE.md .gitignore
git commit -m "docs: CLAUDE.md como fuente única de verdad

Declara dónde vive el código, cómo se despliega al VPS (sin git),
qué se versiona, y la regla de sincronizar antes de trabajar."
```

---

## Tarea 9: Renombrar a `carbonbox-ops`

Se hace **al final**: si algo sale mal antes, el repo sigue con su nombre conocido.

**El VPS no se ve afectado** — verificado: no tiene clon del repo.

- [ ] **Paso 1: Subir todo lo anterior a GitHub, con el nombre viejo todavía**

```bash
cd "C:/Users/USUARIO/Claude/Projects/carbonbox-crm"
git push origin main
```

**Este es el momento en que el trabajo de cotizar queda respaldado fuera de tu equipo.** Verificar en `https://github.com/ViviBohoLo/carbonbox-crm` que `tools/cotizar/` está ahí y que `Cotizaciones/` **no**.

- [ ] **Paso 2: Renombrar el repo en GitHub**

```bash
gh repo rename carbonbox-ops --repo ViviBohoLo/carbonbox-crm
```

Si `gh` no está autenticado, Viviana lo hace desde la web: Settings → Repository name → `carbonbox-ops` → Rename.

- [ ] **Paso 3: Actualizar el remoto local**

```bash
cd "C:/Users/USUARIO/Claude/Projects/carbonbox-crm"
git remote set-url origin https://github.com/ViviBohoLo/carbonbox-ops.git
git remote -v
git fetch origin && echo ">>> el remoto nuevo responde"
```

- [ ] **Paso 4: Renombrar la carpeta local**

```bash
cd "C:/Users/USUARIO/Claude/Projects"
mv "carbonbox-crm" "carbonbox-ops"
cd "carbonbox-ops" && git status
```
Esperado: repo limpio, `up to date with 'origin/main'`.

---

## Tarea 10: Archivar las carpetas viejas

**Nada se borra.** Se marcan y se quedan hasta que Viviana confirme.

- [ ] **Paso 1: Renombrar con prefijo `_VIEJO_`**

```bash
cd "C:/Users/USUARIO/Claude/Projects"
mv "CRM CarbonBox" "_VIEJO_CRM CarbonBox"
mv "Cobros CMR CarbonBox" "_VIEJO_Cobros CMR CarbonBox"
mv "Automatización de cotizaciones CarbonBox" "_VIEJO_Automatización de cotizaciones CarbonBox"
ls -d "C:/Users/USUARIO/Claude/Projects/"*CarbonBox* "C:/Users/USUARIO/Claude/Projects/carbonbox-ops"
```
Esperado: tres `_VIEJO_*` y `carbonbox-ops`.

- [ ] **Paso 2: Verificación final contra los criterios de éxito del spec**

```bash
cd "C:/Users/USUARIO/Claude/Projects/carbonbox-ops"
echo "=== 1. Repo único y sincronizado ==="
git remote -v | head -1 && git status -sb | head -1
echo "=== 2/9. Cotizaciones fuera del historial ==="
git log --all --numstat --format="" | grep -ci "Cotizaciones/" || echo "OK: nunca entró"
echo "=== 5. Tests ==="
cd crm-scripts && python -m unittest discover -p "test_*.py" 2>&1 | tail -3
echo "=== 6. Credenciales de Helisa fuera del historial ==="
cd .. && git log --all --numstat --format="" | grep -ci "terminal Helisa" || echo "OK: nunca entró"
echo "=== 7. CLAUDE.md existe ==="
test -f CLAUDE.md && echo "OK"
echo "=== 11. El CRM sigue arriba ==="
ssh -i "C:/Users/USUARIO/.ssh/hostinger_vps" -o ConnectTimeout=15 root@72.60.125.170 'docker ps --format "{{.Names}} | {{.Status}}"'
```

Esperado: los tests pasan con el mismo número que la Tarea 2; `Cotizaciones/` y `terminal Helisa` dicen `OK: nunca entró`; los cuatro contenedores de Twenty siguen `Up`.

- [ ] **Paso 3: Avisar a Viviana**

Reportar: qué quedó dónde, que las carpetas viejas siguen en disco marcadas con `_VIEJO_`, dónde está el backup (`C:/Users/USUARIO/Claude/_BACKUP_2026-07-16/`), y que **el borrado es decisión suya, cuando esté tranquila**.

---

## Fuera de este plan

**Conectar `/cotizar` con el CRM** — Etapa 1 de `docs/superpowers/plans/2026-07-06-cotizar-etapa1.md` (8 tareas, ninguna ejecutada). Al retomarlo: hoy el patrón es duplicar un generador de ~26 KB por cliente (3 copias con ~90% de código idéntico). El plan ya propone separar `contenido.yml` de `render.js`. El skill `/cotizar` es la tarea 8, no la primera.

**Subir `Cotizaciones/` a Drive automáticamente** — Etapa 2 de cotizar. Es una mejora de comodidad: el respaldo ya lo da el correo con que se envían los decks.
