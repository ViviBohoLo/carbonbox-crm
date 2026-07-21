#!/bin/bash
# render-pdf.sh <archivo.pptx> — exporta a PDF con LibreOffice en la misma carpeta
set -e
PPTX="$1"; DIR="$(dirname "$PPTX")"
soffice --headless --convert-to pdf --outdir "$DIR" "$PPTX"
echo "PDF: ${PPTX%.pptx}.pdf"
