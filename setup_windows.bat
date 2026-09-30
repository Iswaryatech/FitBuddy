@echo off
echo ==========================================
echo MoveMap - Windows Setup
echo ==========================================
py -m venv venv
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt
if not exist .env copy .env.example .env
echo.
echo Setup complete.
echo Optional: open .env and add a Gemini API key for AI-written plans.
echo MoveMap also works without a key using its built-in planner.
echo.
echo Start the app with:
echo venv\Scripts\python.exe -m uvicorn app.main:app --reload
pause
