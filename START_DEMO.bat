@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo  SkillCraft Hybrid RAG Studio - Task 01
echo ==============================================
echo.

where py >nul 2>nul
if errorlevel 1 (
    echo Python Launcher ^(py^) was not found.
    echo Install Python 3.10 or later, then try again.
    goto :failed
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating local virtual environment...
    py -m venv .venv
    if errorlevel 1 goto :failed
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :failed

python -c "import streamlit, pandas, pypdf, rank_bm25, sentence_transformers, numpy" >nul 2>nul
if errorlevel 1 (
    echo Installing project dependencies. First setup may take several minutes...
    python -m pip install --upgrade pip
    if errorlevel 1 goto :failed
    python -m pip install -r requirements.txt
    if errorlevel 1 goto :failed
)

echo.
echo Launching the local demo at http://localhost:8501
echo First Dense query may download the embedding model.
echo Close this window to stop the app.
echo.
python -m streamlit run streamlit_app.py --server.address=127.0.0.1 --server.port=8501
if errorlevel 1 goto :failed
goto :eof

:failed
echo.
echo Demo startup stopped. Check the error above and confirm internet access
echo is available for dependency and model downloads.
pause
exit /b 1
