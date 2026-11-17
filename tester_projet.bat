@echo off
echo ========================================================
echo   SMARTRESTO - TEST ET EXECUTION DU PROJET
echo ========================================================
echo.
echo [1/2] Execution des tests unitaires et d integration...
py -m unittest discover
if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Des tests ont echoue !
    pause
    exit /b %ERRORLEVEL%
)
echo.
echo [2/2] Lancement de la plateforme unifiee Streamlit (app.py)...
echo Vous pouvez tester :
echo   - La Tablette Client
echo   - L Ecran Cuisine KDS
echo   - Les Appels Serveur
echo   - Les Statistiques et Top Ventes
echo.
py -m streamlit run app.py
pause
