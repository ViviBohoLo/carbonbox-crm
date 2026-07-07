# Rebranding de Twenty → CarbonBox CRM

La imagen de producción `carbonbox/crm:latest` es Twenty con una capa de personalización
(logos, colores, fuente, textos de login) más el parche del alias de envío de correos.

## Contenido

- **`twenty-carbonbox-rebrand.patch`** — parche `git diff --binary` con TODOS los cambios
  (código + assets binarios: ~100 íconos/logos). Es autocontenido: restaura todo con un
  solo `git apply`.
- **`BASE_COMMIT.txt`** — commit de Twenty sobre el que se hizo el parche
  (`9f4efa57ff5f2161d350e1463636489bc164cd2c`, 2026-07-03).

## Qué cambia el parche

- **Logos / íconos** (`packages/twenty-front/public/images/icons/**`, `manifest.json`) → marca CarbonBox.
- **Colores** (`packages/twenty-ui/src/theme/constants/*` — Accent/MainColors light+dark) → primario `#1620A4`.
- **Fuente** (`FontCommon.ts`).
- **Login** (`SignInUp.tsx`, `SignInUpV2.tsx`, `index.html`, `index.css`).
- **Alias de correo** (`gmail-message-outbound.service.ts`): envía desde
  `EMAIL_SEND_FROM_ALIAS` / `EMAIL_SEND_FROM_NAME` (ver `deploy/.env.example`).

## Cómo reconstruir la imagen desde cero

```bash
# 1. Clonar Twenty en el commit base
git clone https://github.com/twentyhq/twenty.git twenty-src
cd twenty-src
git checkout 9f4efa57ff5f2161d350e1463636489bc164cd2c

# 2. Aplicar el parche de CarbonBox
git apply /ruta/a/twenty-carbonbox-rebrand.patch

# 3. Compilar la imagen (en una máquina con CPU suficiente, NO en el VPS de 1 vCPU)
docker build -t carbonbox/crm:latest -f packages/twenty-docker/twenty/Dockerfile .

# 4. Subir al VPS
docker save carbonbox/crm:latest | gzip | ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'gunzip | docker load'
```

> El fuente completo con estos cambios vive (al 2026-07-07) en WSL `Ubuntu-24.04:/root/twenty-src`.
> Este parche existe para no depender de esa copia: preservarlo aquí ES la copia de seguridad.
