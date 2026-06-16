@echo off
cd /d "C:\Users\Claudio Guedez\Desktop\sistema-reservaciones"
del ".git\index.lock" 2>nul
git config user.email "claudioguedez12@gmail.com"
git config user.name "Claudio Guedez"
git add app.py notificaciones.py landing.html
git commit -m "Implement 3 Standard plan features: SMS reminders, monthly reports, PDF invoicing"
git push
echo.
echo === Done! Press any key to close ===
pause
