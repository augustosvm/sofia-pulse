#!/bin/bash

echo "=== INSTALANDO FERRAMENTAS ==="
sudo apt install -y pylint python3-radon python3-flake8

echo -e "\n=== 1. PYLINT - Qualidade Geral ==="
pylint backend/ --reports=y | tee pylint-report.txt

echo -e "\n=== 2. CÓDIGO DUPLICADO ==="
pylint backend/ --disable=all --enable=duplicate-code | tee duplicate-code.txt

echo -e "\n=== 3. COMPLEXIDADE CICLOMÁTICA ==="
radon cc backend/ -a -s | tee complexity.txt

echo -e "\n=== 4. ÍNDICE DE MANUTENIBILIDADE ==="
radon mi backend/ -s | tee maintainability.txt

echo -e "\n=== 5. STYLE ISSUES ==="
flake8 backend/ --statistics | tee flake8-report.txt

echo -e "\n=== RELATÓRIOS SALVOS ==="
ls -lh *-report.txt *.txt | grep -E "report|complexity|maintainability|duplicate"
