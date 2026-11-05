$ErrorActionPreference = 'Stop'

$compiler = Join-Path $env:LOCALAPPDATA 'Keil_v5\ARM\ARMCLANG\bin\armclang.exe'
$root = Split-Path -Parent $PSScriptRoot
$include = Join-Path $root 'Core\Inc'
$source = Join-Path $root 'Core\Src\lamp_core.c'
$outputDir = Join-Path $root 'build\armclang'
$output = Join-Path $outputDir 'lamp_core.o'

if (-not (Test-Path -LiteralPath $compiler)) {
    throw "Arm Compiler 6 not found at $compiler"
}

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
& $compiler --target=arm-arm-none-eabi -mcpu=cortex-m4 -mthumb `
    -std=c11 -Wall -Wextra -Werror -O1 -I $include -c $source -o $output
if ($LASTEXITCODE -ne 0) {
    throw "armclang failed with exit code $LASTEXITCODE"
}
Write-Host "ARM compile OK: $output"
