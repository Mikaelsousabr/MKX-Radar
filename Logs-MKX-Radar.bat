@echo off
cd /d "%~dp0"
docker compose -f compose.mkx.yaml logs --tail 100 -f
pause
