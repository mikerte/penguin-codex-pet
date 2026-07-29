[CmdletBinding()]
param(
    [string]$CodexHome
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$sourceDirectory = Join-Path $projectRoot "pet"

if ([string]::IsNullOrWhiteSpace($CodexHome)) {
    if (-not [string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
        $resolvedCodexHome = [System.IO.Path]::GetFullPath($env:CODEX_HOME)
    }
    else {
        $userProfile = [Environment]::GetFolderPath("UserProfile")
        $resolvedCodexHome = Join-Path $userProfile ".codex"
    }
}
else {
    $resolvedCodexHome = [System.IO.Path]::GetFullPath($CodexHome)
}

$targetDirectory = Join-Path $resolvedCodexHome "pets\pingo"

foreach ($requiredFile in @("pet.json", "spritesheet.webp")) {
    $sourceFile = Join-Path $sourceDirectory $requiredFile
    if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
        throw "Missing required package file: $sourceFile"
    }
}

New-Item -ItemType Directory -Force -Path $targetDirectory | Out-Null
Copy-Item -LiteralPath (Join-Path $sourceDirectory "pet.json") -Destination $targetDirectory -Force
Copy-Item -LiteralPath (Join-Path $sourceDirectory "spritesheet.webp") -Destination $targetDirectory -Force

$installedHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $targetDirectory "spritesheet.webp")).Hash.ToLowerInvariant()
Write-Host "Installed Pingo to $targetDirectory"
Write-Host "Spritesheet SHA-256: $installedHash"
