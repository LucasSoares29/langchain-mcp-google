@echo off
echo ==========================================
echo Inicializador do Agente MCP Tavily + Google
echo ==========================================
echo.

IF NOT EXIST "venv\Scripts\python.exe" (
    echo [1/2] Ambiente virtual venv nao encontrado. Criando agora...
    python -m venv venv
) ELSE (
    echo [1/2] Ambiente virtual ja existe. Pulando criacao.
)

:: Pulamos a etapa de 'activate' e chamamos o pip da venv diretamente
echo [2/2] Instalando dependencias via executavel direto...
venv\Scripts\python.exe -m pip install -r requirements.txt -q

echo.
echo ==========================================
echo Tudo pronto! Iniciando o agente...
echo ==========================================
echo.

:: Chamamos o client.py usando o Python da venv, isolando o ambiente
venv\Scripts\python.exe agent-google-langchain-plus-tavily.py

pause