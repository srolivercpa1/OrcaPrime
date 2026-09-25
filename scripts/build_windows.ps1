$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
function Run-Python {
    & python @args
    if ($LASTEXITCODE -ne 0) { throw "Etapa Python falhou: $args" }
}
Run-Python -m pytest -q
Run-Python scripts/make_icon.py
Run-Python -m PyInstaller --clean --noconfirm OrcaPrime.spec
$process = Start-Process '.\dist\OrcaPrime\OrcaPrime.exe' -PassThru
Start-Sleep -Seconds 6
$process.Refresh()
if ($process.HasExited) { throw 'O aplicativo encerrou durante a verificação de abertura.' }
$null = $process.CloseMainWindow()
if (-not $process.WaitForExit(5000)) { Stop-Process -Id $process.Id }
$iscc = Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'
if (-not (Test-Path $iscc)) { throw 'Instale Inno Setup 6 antes de executar este script.' }
& $iscc '.\installer\OrcaPrime.iss'
if ($LASTEXITCODE -ne 0) { throw 'Falha ao gerar o instalador.' }
$setup = Resolve-Path '.\release\OrcaPrime-Setup.exe'
$hash = (Get-FileHash $setup -Algorithm SHA256).Hash.ToLower()
[IO.File]::WriteAllText("$setup.sha256", "$hash  OrcaPrime-Setup.exe`n", [Text.Encoding]::ASCII)
Write-Host "Instalador: $setup"

# Portable distribution retains the full PyInstaller runtime beside the EXE.
$portable = Join-Path (Get-Location) 'release\OrcaPrime-Portable.zip'
Compress-Archive -Path '.\dist\OrcaPrime' -DestinationPath $portable -Force
$portableHash = (Get-FileHash $portable -Algorithm SHA256).Hash.ToLower()
[IO.File]::WriteAllText("$portable.sha256", "$portableHash  OrcaPrime-Portable.zip`n", [Text.Encoding]::ASCII)
