@echo off
cd /d "%~dp0"
docker compose -f compose.mkx.yaml stop
pause
