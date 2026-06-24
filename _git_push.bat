@echo off
cd /d "C:\Users\Claudio Guedez\Desktop\sistema-reservaciones"
del ".git\index.lock" 2>nul
git config user.email "claudioguedez12@gmail.com"
git config user.name "Claudio Guedez"
git push
echo.
echo === Done! Press any key to close ===
pause
