# Setup (una vez) — Campo `linkTranscripcion` en Opportunity (Twenty CRM)

El skill `/cotizar` (Task 8) lee de cada oportunidad un enlace a la transcripción de la
reunión de ventas (en Drive). Para eso, el objeto **Opportunity** de Twenty necesita un
campo personalizado `linkTranscripcion` de tipo **LINKS**. Esto se crea **una sola vez**.

> ✅ **En `crm.carbonbox.app` este campo YA EXISTE** (verificado 2026-07-21) y es de tipo
> `Links`. Este instructivo solo aplica si hay que recrearlo o montarlo en otro Twenty.
>
> Al ser tipo `Links`, en GraphQL **no se lee como texto plano**: hay que pedir sus
> subcampos. Así:
>
> ```graphql
> linkTranscripcion { primaryLinkUrl primaryLinkLabel secondaryLinks }
> ```
>
> La URL está en `primaryLinkUrl`. Pedir `linkTranscripcion` a secas falla.

> ⚠️ Este paso toca la metadata del CRM en producción (`crm.carbonbox.app`). Requiere el
> token de API de Twenty, que vive en el VPS (`/root/.twenty_api_token`) y **no** está en el
> repo. Ejecútalo tú desde el VPS (o desde una máquina con red al CRM y el token). Claude en
> Cowork no puede hacerlo: su entorno no tiene salida de red al CRM.

## Opción A — desde el VPS (recomendado)

```bash
# 1) Token
TK=$(cat /root/.twenty_api_token)

# 2) Obtener el objectMetadataId de "opportunity"
curl -s -H "Authorization: Bearer $TK" \
  "http://localhost:3000/rest/metadata/objects?filter=nameSingular[eq]:opportunity" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['objects'][0]['id'])"
# → copia el id que imprime (OBJ_ID)

# 3) Crear el campo linkTranscripcion (tipo LINKS)
OBJ_ID="<pega_aqui_el_OBJ_ID>"
curl -s -X POST -H "Authorization: Bearer $TK" -H "Content-Type: application/json" \
  "http://localhost:3000/rest/metadata/fields" \
  -d "{\"name\":\"linkTranscripcion\",\"label\":\"Link transcripción\",\"type\":\"LINKS\",\"objectMetadataId\":\"$OBJ_ID\",\"description\":\"URL de la transcripción de la reunión de ventas (Drive)\"}"

# 4) Verificar que quedó
curl -s -H "Authorization: Bearer $TK" \
  "http://localhost:3000/rest/metadata/fields?filter=name[eq]:linkTranscripcion" | head -c 400
```

Resultado esperado en el paso 4: un JSON con el campo `linkTranscripcion` asociado a
Opportunity. Tras crearlo, aparece como columna editable en cada oportunidad del CRM.

## Opción B — desde la interfaz de Twenty

Configuración → Objetos → **Oportunidades** → Campos → **Añadir campo** →
Tipo **Enlaces (Links)**, Nombre **Link transcripción** (API name: `linkTranscripcion`) → Guardar.

## Notas

- El API name debe quedar exactamente `linkTranscripcion` (el skill lo consulta por ese
  nombre en la query GraphQL de la oportunidad).
- Si prefieres otro nombre, actualízalo también en el `SKILL.md` de `/cotizar`.
- Este cambio de metadata queda en la base del CRM; no hay que tocar el repo de código.
