@echo off
cd /d "%~dp0"
if not exist node_modules call npm install
echo Preparing the fast version of the website (about 1 minute)...
call npm run build
if errorlevel 1 (
  echo Fast build failed - starting the slower development version instead.
  call npm run dev -- -p 3001
) else (
  call npm run start -- -p 3001
)
pause
