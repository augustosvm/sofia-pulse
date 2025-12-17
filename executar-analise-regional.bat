@echo off
REM ============================================================================
REM Sofia Pulse - Análise Regional de Papers (ROOT)
REM ============================================================================

echo.
echo ================================================================================
echo Sofia Pulse - Analise Regional de Papers
echo ================================================================================
echo.

REM Copiar script para o servidor
echo Copiando script para o servidor...
scp analise-regional-simples.py root@91.98.158.19:/tmp/

echo.
echo Executando analise no servidor como ROOT...
echo.

ssh root@91.98.158.19 "cd /home/ubuntu/sofia-pulse && python3 /tmp/analise-regional-simples.py"

echo.
echo ================================================================================
echo Analise concluida!
echo ================================================================================
echo.
pause
