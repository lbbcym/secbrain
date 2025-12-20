# Repo-scoped PowerShell profile for this workspace.
# Import manually in your user profile with:
#   . "$PSScriptRoot/pwsh.profile.ps1"

$workspaceRoot = Split-Path -Path $PSCommandPath
$venvActivate = Join-Path $workspaceRoot '.venv/Scripts/Activate.ps1'

if (Test-Path $venvActivate) {
    . $venvActivate
}

# Quality-of-life aliases
Set-Alias pipr "python -m pip"
Set-Alias ruff "python -m ruff"

function sb-test {
    param(
        [string]$Filter = ""
    )
    $args = @("-m", "pytest", "secbrain/tests")
    if ($Filter -ne "") { $args += @("-k", $Filter) }
    python @args
}

function sb-lint {
    ruff check secbrain
}

function sb-fmt {
    ruff format secbrain
    ruff check --fix secbrain
}

function sb-env {
    Write-Host "PYTHONPATH: $env:PYTHONPATH"
    Write-Host "VIRTUAL_ENV: $env:VIRTUAL_ENV"
}
