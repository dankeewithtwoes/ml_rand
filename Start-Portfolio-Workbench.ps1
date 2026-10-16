$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    & python.exe -m venv (Join-Path $root ".venv")
    if ($LASTEXITCODE -ne 0) { throw "Не удалось создать окружение Python" }
}
& $python -c "import fastapi, uvicorn, pydantic, jsonschema"
if ($LASTEXITCODE -ne 0) {
    & $python -m pip install -r (Join-Path $root "requirements-web.txt")
    if ($LASTEXITCODE -ne 0) { throw "Не удалось установить зависимости интерфейса" }
}
& $python (Join-Path $root "portfolio_app.py") --open
