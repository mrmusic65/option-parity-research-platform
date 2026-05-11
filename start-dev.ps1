$projectRoot = "C:\Users\User\OneDrive\Desktop\option_parity_scanner"

Write-Host "Starting Options Relative Value Platform..." -ForegroundColor Green

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectRoot'; .venv\Scripts\activate; uvicorn backend.api:app --reload"
)

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectRoot\frontend'; npm run dev"
)

Start-Sleep -Seconds 4

Start-Process "http://localhost:5173"

Write-Host "Backend:  http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan