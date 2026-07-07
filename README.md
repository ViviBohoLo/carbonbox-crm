# CarbonBox CRM — infraestructura y automatizaciones

Config, scripts y personalización del CRM de CarbonBox (basado en [Twenty](https://twenty.com))
en producción: **https://crm.carbonbox.app** (VPS Hostinger `72.60.125.170`).

Este repo es la **fuente de verdad de ops**: permite reconstruir el CRM desde cero. No contiene
datos de clientes ni secretos (esos viven fuera del repo, ver más abajo).

## Arquitectura

```
Formulario web (carbonbox.app, Vercel/Astro)
        │  POST /intake  (tiempo real)
        ▼
   Caddy (HTTPS, Let's Encrypt)  ── /intake* ──► intake_server.py (:8088, systemd)
        │  resto                                         │
        ▼                                                ▼
   Twenty CRM (Docker: server + worker + postgres + redis, :3000)  ◄── crm-scripts (crons)
```

- **CRM**: imagen `carbonbox/crm:latest` (Twenty personalizado, ver `rebrand/`), Docker Compose.
- **Proxy**: Caddy termina TLS y enruta `/intake*` al servidor de intake y el resto a Twenty.
- **Intake**: el formulario web postea directo (antes iba por sondeo a HubSpot).
- **Crons**: vigía de SLAs, reporte semanal, puente HubSpot (red de seguridad), backup diario.

## Estructura del repo

| Carpeta | Qué hay |
|---|---|
| `deploy/` | `docker-compose.yml` + `override` (fija `carbonbox/crm:latest`), `.env.example`, `Caddyfile`, crons (`cron/`), unit de systemd (`systemd/`), `backup-db.sh`. |
| `crm-scripts/` | Scripts Python (stdlib) del CRM: `crm_lib.py` (cliente API Twenty), `lead_intake.py` + `intake_server.py` (intake del formulario), `vigia_sla.py` (SLAs + renovaciones), `reporte_semanal.py`, `hubspot_bridge.py` (puente de respaldo), tests. |
| `rebrand/` | Parche `git diff --binary` para reconstruir la imagen personalizada de Twenty desde el commit base. Ver `rebrand/README.md`. |
| `branding/` | Logos, tokens de color y guías HTML (funnel, Google OAuth). |
| `docs/` | Specs y planes (superpowers) del webhook de intake. |

## Secretos (NO están en el repo)

Viven solo en el VPS y se referencian por ruta:

| Qué | Dónde (VPS) |
|---|---|
| `.env` de Twenty (DB pass, `ENCRYPTION_KEY`, Google OAuth secret) | `/root/twenty/.env` — plantilla en `deploy/.env.example` |
| Token API de Twenty (para los scripts) | `/root/.twenty_api_token` |
| Token de app privada de HubSpot | `/root/.hubspot_token` |
| Llave SSH del VPS | en el PC: `~/.ssh/hostinger_vps` |

## Reconstruir el CRM desde cero (resumen)

1. **VPS**: Ubuntu 24.04, swap 4 GB, Docker + Compose.
2. **Imagen**: aplicar `rebrand/` sobre Twenty y compilar `carbonbox/crm:latest` (ver `rebrand/README.md`). Compilar fuera del VPS (1 vCPU no aguanta) y subir con `docker save | ssh 'docker load'`.
3. **Config**: copiar `deploy/` a `/root/twenty/` y `/etc/`, crear `/root/twenty/.env` desde `.env.example`.
4. **Arrancar**: `cd /root/twenty && docker compose up -d`.
5. **Datos**: restaurar el dump de Postgres (`pg_restore --no-owner`) — los dumps NO están en el repo (`/root/backups/`, copia off-site en `Documents/CarbonBox/CRM-backups/`).
6. **Proxy/DNS/OAuth**: desplegar `Caddyfile`, apuntar `crm.carbonbox.app` al VPS (DNS en Namecheap), registrar redirect URIs en Google Cloud.
7. **Automatizaciones**: colocar `crm-scripts/` en `/root/crm-scripts/`, instalar los crons (`deploy/cron/`) y el servicio de intake (`deploy/systemd/`), crear los archivos de token.

## Notas

- El stack en WSL (PC) queda de **respaldo dormido**; producción es el VPS.
- Backups: dump diario 3:15am en `/root/backups` (retiene 14 días) + copia off-site en el PC.
