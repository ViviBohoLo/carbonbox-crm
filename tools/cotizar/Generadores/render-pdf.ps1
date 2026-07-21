# render-pdf.ps1 <archivo.pptx> — exporta a PDF usando PowerPoint (Windows).
#
# Alternativa a render-pdf.sh para máquinas sin LibreOffice. Si tienes Office
# instalado no hay que instalar nada más. El PDF queda junto al .pptx.
#
# Uso:
#   powershell -File Generadores/render-pdf.ps1 "Cotizaciones/<Cliente>/<archivo>.pptx"
#
# Extra: con -Png también exporta cada slide como imagen a una subcarpeta _png/,
# útil para revisar el diseño (desbordes de texto, tipografías) sin abrir Office.

param(
  [Parameter(Mandatory = $true)][string]$Pptx,
  [switch]$Png
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Pptx)) { Write-Error "No existe el archivo: $Pptx"; exit 1 }
# PowerPoint por COM exige ruta absoluta.
$full = (Resolve-Path $Pptx).Path
$pdf = [System.IO.Path]::ChangeExtension($full, ".pdf")

$app = $null; $pres = $null
try {
  try {
    $app = New-Object -ComObject PowerPoint.Application -ErrorAction Stop
  } catch {
    Write-Error "No encontré PowerPoint. Usa render-pdf.sh con LibreOffice, o instala Office."
    exit 1
  }

  # ReadOnly=-1 (msoTrue) para no tocar el .pptx original.
  $pres = $app.Presentations.Open($full, -1, 0, 0)
  $pres.SaveAs($pdf, 32)   # 32 = ppSaveAsPDF
  Write-Output "PDF: $pdf"

  if ($Png) {
    $dir = Join-Path ([System.IO.Path]::GetDirectoryName($full)) "_png"
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
    for ($i = 1; $i -le $pres.Slides.Count; $i++) {
      $pres.Slides($i).Export((Join-Path $dir ("slide{0:D2}.png" -f $i)), "PNG", 1600, 900)
    }
    Write-Output "PNG:  $dir ($($pres.Slides.Count) slides)"
  }
} finally {
  if ($pres) { try { $pres.Close() } catch {} }
  if ($app) { try { $app.Quit() } catch {} }
}
