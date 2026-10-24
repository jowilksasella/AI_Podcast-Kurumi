param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $Arguments
)
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
$Caller = (Get-Location).Path
$ConfigArg = $null
$IndexHomeArg = $null
for ($i = 0; $i -lt $Arguments.Count - 1; $i++) {
    if ($Arguments[$i] -eq "--config") { $ConfigArg = $Arguments[$i + 1] }
    if ($Arguments[$i] -eq "--index-home") { $IndexHomeArg = $Arguments[$i + 1] }
}
$IndexHome = if ($IndexHomeArg) { $IndexHomeArg } else { $env:INDEXTTS_HOME }
if (-not $IndexHome -and $ConfigArg) {
    $ConfigPath = if ([IO.Path]::IsPathRooted($ConfigArg)) { $ConfigArg } else { Join-Path $Caller $ConfigArg }
    # A variant config carries no index_home; follow base_config to the bound original.
    for ($Hop = 0; $Hop -lt 3 -and -not $IndexHome -and $ConfigPath; $Hop++) {
        $Config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $ConfigDir = Split-Path -Parent $ConfigPath
        if ($Config.index_home) {
            $IndexHome = if ([IO.Path]::IsPathRooted($Config.index_home)) {
                $Config.index_home
            } else {
                Join-Path $ConfigDir $Config.index_home
            }
        } elseif ($Config.base_config) {
            $ConfigPath = if ([IO.Path]::IsPathRooted($Config.base_config)) {
                $Config.base_config
            } else {
                Join-Path $ConfigDir $Config.base_config
            }
        } else {
            $ConfigPath = $null
        }
    }
}
# Only these commands take --index-home themselves; for the rest it only locates the model.
$Command = if ($Arguments.Count) { $Arguments[0] } else { "" }
if ($IndexHomeArg -and $Command -notin @("bind-original", "find-speaker")) {
    $Kept = @()
    for ($i = 0; $i -lt $Arguments.Count; $i++) {
        if ($Arguments[$i] -eq "--index-home") { $i++; continue }
        $Kept += $Arguments[$i]
    }
    $Arguments = $Kept
}
if (-not $IndexHome) { throw "Pass --index-home, set INDEXTTS_HOME, or use --config with index_home for the existing IndexTTS 2.5 directory." }
$IndexHome = (Resolve-Path -LiteralPath $IndexHome).Path
$Python = Join-Path $IndexHome ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    $Python = Join-Path $IndexHome "python.exe"
}
if (-not (Test-Path -LiteralPath $Python)) {
    throw "No package Python found. Activate the existing model environment and use the Python CLI."
}
$OldHome = $env:PYTHONHOME
$OldPath = $env:PYTHONPATH
$OldCaller = $env:KURUMI_CALLER_CWD
$Code = 1
try {
    $env:PYTHONHOME = $null
    $env:PYTHONPATH = $Repo
    $env:KURUMI_CALLER_CWD = $Caller
    Set-Location -LiteralPath $IndexHome
    # Windows PowerShell wraps redirected native stderr (e.g. model warnings) in
    # ErrorRecords; under "Stop" that aborts the run. The exit code decides failure.
    $ErrorActionPreference = "Continue"
    & $Python -X utf8 -m kurumi_podcast @Arguments
    $Code = $LASTEXITCODE
} finally {
    Set-Location -LiteralPath $Caller
    $env:PYTHONHOME = $OldHome
    $env:PYTHONPATH = $OldPath
    $env:KURUMI_CALLER_CWD = $OldCaller
}
exit $Code
