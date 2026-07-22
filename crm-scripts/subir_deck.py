#!/usr/bin/env python3
"""Sube un archivo al Drive de CarbonBox y devuelve su link.

Existe porque el puente de Composio con Drive no puede subir archivos desde el disco
del PC: sus herramientas piden un `s3key` (bytes ya en el almacenamiento de Composio)
o una URL pública. El VPS sí puede — su token de Google incluye el permiso
`auth/drive` sobre `info@carbonbox.app`, la cuenta dueña de las carpetas.

Flujo desde el PC:
    scp -i ~/.ssh/hostinger_vps "<deck>.pdf" root@72.60.125.170:/tmp/
    ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 \
        'cd /root/crm-scripts && python3 subir_deck.py /tmp/<deck>.pdf <ID_CARPETA>'

Imprime el webViewLink del archivo subido. Borra el temporal después.

NO crea carpetas: la carpeta destino debe existir y pasarse por ID.
"""
import json
import mimetypes
import os
import sys
import urllib.request
import uuid

from crm_lib import google_access_token

UPLOAD_URL = ("https://www.googleapis.com/upload/drive/v3/files"
              "?uploadType=multipart&supportsAllDrives=true&fields=id,name,webViewLink")


def tipo_mime(ruta):
    """MIME del archivo por su extensión. Los de Office no siempre están registrados."""
    fijos = {
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pdf": "application/pdf",
    }
    ext = os.path.splitext(ruta)[1].lower()
    if ext in fijos:
        return fijos[ext]
    return mimetypes.guess_type(ruta)[0] or "application/octet-stream"


def cuerpo_multipart(metadatos, contenido, mime, frontera):
    """Arma el cuerpo multipart/related que espera la Drive API (metadatos + bytes)."""
    sep = f"--{frontera}\r\n".encode()
    partes = [
        sep,
        b"Content-Type: application/json; charset=UTF-8\r\n\r\n",
        json.dumps(metadatos).encode("utf-8"), b"\r\n",
        sep,
        f"Content-Type: {mime}\r\n\r\n".encode(),
        contenido, b"\r\n",
        f"--{frontera}--\r\n".encode(),
    ]
    return b"".join(partes)


def subir(ruta, carpeta_id, nombre=None):
    """Sube `ruta` a la carpeta `carpeta_id`. Devuelve el dict de la Drive API."""
    if not os.path.isfile(ruta):
        raise SystemExit(f"No existe el archivo: {ruta}")
    nombre = nombre or os.path.basename(ruta)
    mime = tipo_mime(ruta)
    with open(ruta, "rb") as f:
        contenido = f.read()

    frontera = uuid.uuid4().hex
    metadatos = {"name": nombre, "parents": [carpeta_id]}
    cuerpo = cuerpo_multipart(metadatos, contenido, mime, frontera)

    req = urllib.request.Request(UPLOAD_URL, data=cuerpo, headers={
        "Authorization": f"Bearer {google_access_token()}",
        "Content-Type": f"multipart/related; boundary={frontera}",
        "Content-Length": str(len(cuerpo)),
    })
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


def main(argv):
    if len(argv) < 2:
        print("uso: python3 subir_deck.py <archivo> <id_carpeta> [nombre_en_drive]")
        return 2
    ruta, carpeta = argv[0], argv[1]
    nombre = argv[2] if len(argv) > 2 else None
    d = subir(ruta, carpeta, nombre)
    print(f"OK  {d.get('name')}")
    print(f"id  {d.get('id')}")
    print(f"link {d.get('webViewLink')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
