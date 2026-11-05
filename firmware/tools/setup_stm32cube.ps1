$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$cube = Join-Path $repoRoot '.tools\STM32CubeF4'
$keilRoot = Join-Path $env:LOCALAPPDATA 'Keil_v5'
$cpackget = Join-Path $keilRoot 'ARM\cmsis-toolbox\bin\cpackget.exe'
$packRoot = Join-Path $keilRoot 'ARM\PACK'
$packDir = Join-Path $packRoot 'Keil\STM32F4xx_DFP\3.1.1'

if (-not (Test-Path -LiteralPath $cube)) {
    git clone --depth 1 --filter=blob:none --sparse `
        https://github.com/STMicroelectronics/STM32CubeF4.git $cube
    if ($LASTEXITCODE -ne 0) { throw 'STM32CubeF4 clone failed' }
}

git -C $cube sparse-checkout set --skip-checks `
    Drivers/CMSIS Drivers/STM32F4xx_HAL_Driver Drivers/BSP/STM32F4xx-Nucleo `
    Projects/STM32F411RE-Nucleo/Templates
if ($LASTEXITCODE -ne 0) { throw 'STM32CubeF4 sparse checkout failed' }

git -C $cube submodule update --init --depth 1 `
    Drivers/CMSIS/Device/ST/STM32F4xx `
    Drivers/STM32F4xx_HAL_Driver `
    Drivers/BSP/STM32F4xx-Nucleo
if ($LASTEXITCODE -ne 0) { throw 'STM32CubeF4 submodule setup failed' }

if (-not (Test-Path -LiteralPath $packDir)) {
    if (-not (Test-Path -LiteralPath $cpackget)) {
        throw "Keil cpackget not found at $cpackget"
    }
    $packFile = Join-Path $env:TEMP 'Keil.STM32F4xx_DFP.3.1.1.pack'
    Invoke-WebRequest `
        -Uri 'https://www.keil.com/pack/Keil.STM32F4xx_DFP.3.1.1.pack' `
        -OutFile $packFile
    & $cpackget add $packFile --agree-embedded-license --pack-root $packRoot --skip-touch
    if ($LASTEXITCODE -ne 0) { throw 'STM32F4 device pack installation failed' }
}

Write-Host 'STM32CubeF4 and Keil STM32F4 device metadata are ready.'
