param(
    [Parameter(Mandatory = $true)]
    [string]$PbipPath
)

$ErrorActionPreference = "Stop"

if (Test-Path -LiteralPath $PbipPath -PathType Leaf) {
    $pbipFile = (Resolve-Path -LiteralPath $PbipPath).Path
    $root = Split-Path -Parent $pbipFile
} elseif (Test-Path -LiteralPath $PbipPath -PathType Container) {
    $root = (Resolve-Path -LiteralPath $PbipPath).Path
    $pbipFile = Get-ChildItem -LiteralPath $root -Filter "*.pbip" -File -ErrorAction SilentlyContinue | Select-Object -First 1
} else {
    throw "Path not found: $PbipPath"
}

$reportDir = Get-ChildItem -LiteralPath $root -Directory -Filter "*.Report" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $reportDir) {
    if ((Split-Path -Leaf $root) -like "*.Report") {
        $reportDir = Get-Item -LiteralPath $root
        $root = Split-Path -Parent $root
    } else {
        throw "No *.Report folder found. Save the PBIX as a Power BI Project (.pbip) first."
    }
}

$patchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$definition = Join-Path $reportDir.FullName "definition"
$resources = Join-Path $reportDir.FullName "StaticResources\RegisteredResources"

if (-not (Test-Path -LiteralPath $definition)) {
    throw "Not a valid PBIP report folder: $($reportDir.FullName)"
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = Join-Path $root "pbip_backup_$stamp"
New-Item -ItemType Directory -Path $backup -Force | Out-Null
Copy-Item -LiteralPath $definition -Destination (Join-Path $backup "definition") -Recurse -Force
if (Test-Path -LiteralPath $resources) {
    Copy-Item -LiteralPath $resources -Destination (Join-Path $backup "RegisteredResources") -Recurse -Force
}
Write-Host "Backup: $backup" -ForegroundColor Cyan

$oldPage = Join-Path $definition "pages\02a89321b64037938c70"
if (Test-Path -LiteralPath $oldPage) {
    Remove-Item -LiteralPath $oldPage -Recurse -Force
    Write-Host "Removed trial page: 02a89321b64037938c70" -ForegroundColor Yellow
}

Copy-Item -Path (Join-Path $patchRoot "definition\*") -Destination $definition -Recurse -Force
Write-Host "Report definition replaced." -ForegroundColor Green

if (-not (Test-Path -LiteralPath $resources)) {
    New-Item -ItemType Directory -Path $resources -Force | Out-Null
}
Copy-Item -Path (Join-Path $patchRoot "StaticResources\RegisteredResources\*") -Destination $resources -Force
Write-Host "Resources copied." -ForegroundColor Green

$pagesFile = Join-Path $definition "pages\pages.json"
if (-not (Test-Path -LiteralPath $pagesFile)) {
    throw "pages.json is missing; patch failed."
}
$pages = Get-Content -LiteralPath $pagesFile -Raw -Encoding UTF8 | ConvertFrom-Json
Write-Host "Pages: $($pages.pageOrder.Count); active: $($pages.activePageName)" -ForegroundColor Cyan

Write-Host ""
Write-Host "Done. Open in Power BI Desktop:" -ForegroundColor Green
if ($pbipFile) {
    Write-Host $pbipFile.FullName
}
Write-Host "If it fails, restore the backup under: $backup" -ForegroundColor DarkYellow