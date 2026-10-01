@echo off
where ollama >nul 2>nul
if errorlevel 1 (
  echo Ollama nao encontrado. Abra o Ollama instalado e confira se o comando esta disponivel.
  pause
  exit /b 1
)
echo Encerre o Ollama pelo icone perto do relogio antes de continuar.
echo Este auxiliar inicia o Ollama para acesso do Docker.
echo Restrinja a porta 11434 ao ambiente local/Docker no firewall. Nao libere acesso publico.
echo Mantenha esta janela aberta enquanto usar a IA. Ctrl+C encerra este processo.
pause
set OLLAMA_HOST=0.0.0.0:11434
set OLLAMA_NO_CLOUD=1
ollama serve
if errorlevel 1 (
  echo Nao foi possivel iniciar. Pode haver outra instancia do Ollama usando a porta.
  pause
)
