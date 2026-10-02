param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $Arguments
)
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
$Caller = (Get-Location).Path
$ConfigArg = $null
for ($i = 0; $i -lt $Arguments.Count - 1; $i++) {
    if ($Arguments[$i] -eq "--config") { $ConfigArg = $Arguments[$i + 1] }
}
$IndexHome = $env:INDEXTTS_HOME
if (-not $IndexHome -and $ConfigArg) {
    $ConfigPath = if ([IO.Path]::IsPathRooted($ConfigArg)) { $ConfigArg } else { Join-Path $Caller $ConfigArg }
    $Config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($Config.index_home) {
        $IndexHome = if ([IO.Path]::IsPathRooted($Config.index_home)) {
            $Config.index_home
        } else {
            Join-Path (Split-Path -Parent $ConfigPath) $Config.index_home
        }
    }
}
if (-not $IndexHome) { throw "Set INDEXTTS_HOME to the existing IndexTTS 2.5 directory." }
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
    & $Python -X utf8 -m kurumi_podcast @Arguments
    $Code = $LASTEXITCODE
} finally {
    Set-Location -LiteralPath $Caller
    $env:PYTHONHOME = $OldHome
    $env:PYTHONPATH = $OldPath
    $env:KURUMI_CALLER_CWD = $OldCaller
}
exit $Code

