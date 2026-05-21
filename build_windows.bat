@echo off
echo ===================================================
echo Windows EXE 파일 빌드 스크립트 (PyInstaller)
echo ===================================================
echo.

echo 1. pyinstaller가 설치되어 있는지 확인합니다...
pip install pyinstaller

echo.
echo 2. 빌드를 시작합니다...
echo (이 작업은 다소 시간이 소요될 수 있습니다)

:: ddddocr 모델 파일과 customtkinter 리소스를 포함하기 위한 설정
:: 윈도우에서는 --add-data 구분자로 세미콜론(;)을 사용합니다.
pyinstaller --noconfirm --onedir --windowed --name "CaptchaSolver" ^
  --add-data "%VIRTUAL_ENV%\Lib\site-packages\customtkinter;customtkinter\" ^
  --add-data "%VIRTUAL_ENV%\Lib\site-packages\ddddocr;ddddocr\" ^
  ui_app.py

echo.
echo ===================================================
echo 빌드가 완료되었습니다!
echo 'dist\CaptchaSolver' 폴더 안의 CaptchaSolver.exe 파일을 확인해주세요.
echo ===================================================
pause
