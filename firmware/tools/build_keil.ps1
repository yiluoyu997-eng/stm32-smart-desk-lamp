$ErrorActionPreference = 'Stop'

$uv4 = Join-Path $env:LOCALAPPDATA 'Keil_v5\UV4\UV4.exe'
$projectDir = Join-Path (Split-Path -Parent $PSScriptRoot) 'STM32F411RE\MDK-ARM'
$project = Join-Path $projectDir 'Project.uvprojx'
$log = Join-Path $projectDir 'build.log'

if (-not (Test-Path -LiteralPath $uv4)) { throw "Keil uVision not found at $uv4" }
if (-not (Test-Path -LiteralPath $project)) { throw "Project not found at $project" }

$process = Start-Process -FilePath $uv4 -ArgumentList @('-b', 'Project.uvprojx', '-j0', '-o', 'build.log') `
    -WorkingDirectory $projectDir -WindowStyle Hidden -Wait -PassThru
if (-not (Test-Path -LiteralPath $log)) { throw 'Keil did not produce build.log' }

$text = Get-Content -LiteralPath $log -Raw
Write-Host $text
if ($text -notmatch '0 Error\(s\), 0 Warning\(s\)') {
    throw "Keil build failed; process exit code $($process.ExitCode)"
}
Write-Host 'Keil build OK: 0 errors, 0 warnings.'
