$ErrorActionPreference = "Stop"
Write-Host "Cookie Cat startup helper" -ForegroundColor Green
if (-not (Test-Path ".\data\raw\cookie_cats.csv")) {
    python run_all.py
}
python -m streamlit run app.py
