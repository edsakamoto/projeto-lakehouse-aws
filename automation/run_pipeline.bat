@echo off
setlocal EnableDelayedExpansion

REM ====================================
REM RESOLUCAO DE CAMINHOS
REM ====================================
set PROJECT_DIR=D:\downloads\materiais - aws para gestao de dados\clone-github-pasta\projeto-lakehouse-aws

REM ====================================
REM CONFIGURACOES
REM ====================================
set PYTHON_EXE=D:\downloads\materiais - aws para gestao de dados\clone-github-pasta\projeto-lakehouse-aws\venv\Scripts\python.exe
set AWS_PROFILE=pos-eng-dados
set LOG_DIR=D:\downloads\materiais - aws para gestao de dados\clone-github-pasta\projeto-lakehouse-aws\log

echo ===================================
echo pipeline lakehouse pos-eng-dados
echo ===================================

REM ====================================
REM CRIA DIRETORIO DE LOG
REM ====================================
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM =========================================
REM TIMESTAMP SEGURO (INDEPENDENTE DE LOCALE)
REM =========================================
for /f "tokens=1-3 delims=/- " %%a in ("%date%") do (
    set DD=%%a
    set MM=%%b
    set YYYY=%%c
)

for /f "tokens=1-3 delims=:." %%a in ("%time%") do (
    set HH=%%a
    set MI=%%b
    set SS=%%c
)
set HH=%HH: =0%

set LOGFILE=%LOG_DIR%\pipeline_pos_%YYYY%-%MM%-%DD%_%HH%%MI%.log

REM ===========================================
REM EXECUCAO
REM ===========================================
echo ====== INICIO %date% %time% =========== >> "%LOGFILE%"

"%PYTHON_EXE%" "%PROJECT_DIR%\ETL\legado\legado_upload.py" >> "%LOGFILE%" 2>&1
if errorlevel 1 goto erro

"%PYTHON_EXE%" "%PROJECT_DIR%\ETL\raw\legado_to_raw.py" >> "%LOGFILE%" 2>&1
if errorlevel 1 goto erro

"%PYTHON_EXE%" "%PROJECT_DIR%\ETL\trusted\raw_to_trusted.py" >> "%LOGFILE%" 2>&1
if errorlevel 1 goto erro

"%PYTHON_EXE%" "%PROJECT_DIR%\ETL\curated\run_ctas_athena.py" >> "%LOGFILE%" 2>&1
if errorlevel 1 goto erro

echo ======== FIM %date% %time% - SUCESSO ======== >> "%LOGFILE%"
exit /b 0

:erro
echo ========= FIM %date% %time% - ERRO ======= >> "%LOGFILE%"
exit /b 1