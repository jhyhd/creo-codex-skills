# Copies this package's skills without touching existing installations or config.
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$Destination = (Join-Path $env:USERPROFILE '.agents\skills'),
    [ValidateSet('creo-native-model', 'creo-surface-design', 'creo-parametric-edit', 'creo-diagnose', 'creo-toolkit-dev', 'screen-observe-loop')]
    [string[]]$Name = @('creo-native-model', 'creo-surface-design', 'creo-parametric-edit', 'creo-diagnose', 'creo-toolkit-dev', 'screen-observe-loop')
)

$ErrorActionPreference = 'Stop'
$repository = Split-Path -Parent $PSScriptRoot
$sourceRoot = Join-Path $repository 'skills'
$destinationRoot = [System.IO.Path]::GetFullPath($Destination)
$names = @($Name | Select-Object -Unique)

# Validate every source and target before any copy, avoiding a partial install
# caused by an already installed skill. Existing folders are never overwritten.
foreach ($skillName in $names) {
    $source = Join-Path $sourceRoot $skillName
    $target = Join-Path $destinationRoot $skillName
    if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) {
        throw "Missing packaged skill: $skillName"
    }
    if (Test-Path -LiteralPath $target) {
        throw "Target already exists; nothing copied. Back up or choose another destination: $target"
    }
}

foreach ($skillName in $names) {
    $source = Join-Path $sourceRoot $skillName
    $target = Join-Path $destinationRoot $skillName
    if ($PSCmdlet.ShouldProcess($target, 'Install packaged Creo skill')) {
        New-Item -ItemType Directory -Path $destinationRoot -Force | Out-Null
        Copy-Item -LiteralPath $source -Destination $target -Recurse -ErrorAction Stop
        [pscustomobject]@{ Skill = $skillName; InstalledTo = $target }
    }
}
