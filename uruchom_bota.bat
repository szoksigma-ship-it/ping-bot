@echo off
echo ============================================
echo         URUCHAMIANIE PING BOTA
echo ============================================
echo.

:: Sprawdz czy Python jest zainstalowany
python --version >nul 2>&1
if errorlevel 1 (
    echo [BLAD] Python nie jest zainstalowany!
    echo Pobierz z: https://www.python.org/downloads/
    echo Pamietaj zaznaczyc "Add Python to PATH" podczas instalacji!
    pause
    exit
)

:: Zainstaluj biblioteke jesli nie ma
echo [1/2] Sprawdzam biblioteke discord.py...
pip show discord.py >nul 2>&1
if errorlevel 1 (
    echo Instaluje discord.py...
    pip install discord.py
)
echo [2/2] Biblioteka OK.
echo.

:: Sprawdz czy token zostal wklejony
findstr /C:"TUTAJ_WKLEJ_TOKEN_BOTA" ping_bot.py >nul 2>&1
if not errorlevel 1 (
    echo [BLAD] Nie wklejiles tokenu bota!
    echo Otworz ping_bot.py i zamien TUTAJ_WKLEJ_TOKEN_BOTA na swoj token.
    pause
    exit
)

echo Uruchamiam bota...
echo Aby zatrzymac bota nacisnij CTRL+C
echo.
python ping_bot.py

:: Jesli bot sie wylaczy - pokaz blad zamiast zamykac okno
echo.
echo ============================================
echo Bot zakonczyl dzialanie.
echo Jesli widzisz blad powyzej - skopiuj go i wklej do chatu.
echo ============================================
pause
