#!/bin/bash
# Test E2E completo de HLCS con servidor mock SARAi
#
# Uso:
#   bash scripts/test_e2e.sh
#
# Este script:
# 1. Inicia el servidor mock SARAi en background
# 2. Espera a que esté listo
# 3. Ejecuta los tests E2E
# 4. Apaga el servidor mock
# 5. Muestra resultados

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MOCK_SERVER_PORT=3100
MOCK_SERVER_PID=""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}HLCS E2E Integration Test${NC}"
echo -e "${GREEN}========================================${NC}"

# Función para cleanup
cleanup() {
    if [ -n "$MOCK_SERVER_PID" ] && kill -0 "$MOCK_SERVER_PID" 2>/dev/null; then
        echo -e "\n${YELLOW}Deteniendo Mock SARAi Server (PID: $MOCK_SERVER_PID)...${NC}"
        kill "$MOCK_SERVER_PID" 2>/dev/null || true
        wait "$MOCK_SERVER_PID" 2>/dev/null || true
        echo -e "${GREEN}✅ Mock server detenido${NC}"
    fi
}

# Trap para cleanup
trap cleanup EXIT INT TERM

# 1. Verificar dependencias
echo -e "\n${YELLOW}[1/5] Verificando dependencias...${NC}"
cd "$PROJECT_ROOT"

# Usar python3 si python no está disponible
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python no encontrado${NC}"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt no encontrado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python encontrado: $($PYTHON_CMD --version)${NC}"

# Verificar que pytest esté instalado
if ! $PYTHON_CMD -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  pytest no encontrado, instalando dependencias...${NC}"
    $PYTHON_CMD -m pip install -q -r requirements.txt
fi

echo -e "${GREEN}✅ Dependencias verificadas${NC}"

# 2. Iniciar Mock SARAi Server
echo -e "\n${YELLOW}[2/5] Iniciando Mock SARAi Server (port $MOCK_SERVER_PORT)...${NC}"

# Verificar si el puerto está libre
if lsof -Pi :$MOCK_SERVER_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}❌ Puerto $MOCK_SERVER_PORT ya está en uso${NC}"
    echo -e "${YELLOW}Intenta: lsof -ti:$MOCK_SERVER_PORT | xargs kill${NC}"
    exit 1
fi

# Iniciar servidor en background
PYTHONPATH="$PROJECT_ROOT/src:$PROJECT_ROOT/tests" $PYTHON_CMD -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/tests')
from mock_sarai_server import run_mock_server
run_mock_server(port=$MOCK_SERVER_PORT)
" > /tmp/mock_sarai_server.log 2>&1 &

MOCK_SERVER_PID=$!
echo -e "${GREEN}✅ Mock server iniciado (PID: $MOCK_SERVER_PID)${NC}"

# 3. Esperar a que el servidor esté listo
echo -e "\n${YELLOW}[3/5] Esperando a que Mock SARAi Server esté listo...${NC}"

MAX_WAIT=10
WAIT_COUNT=0

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if curl -s "http://localhost:$MOCK_SERVER_PORT/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Mock SARAi Server está listo${NC}"
        break
    fi
    
    WAIT_COUNT=$((WAIT_COUNT + 1))
    echo -n "."
    sleep 1
done

if [ $WAIT_COUNT -eq $MAX_WAIT ]; then
    echo -e "\n${RED}❌ Mock SARAi Server no respondió en ${MAX_WAIT}s${NC}"
    echo -e "${YELLOW}Logs del servidor:${NC}"
    cat /tmp/mock_sarai_server.log
    exit 1
fi

# Verificar health
HEALTH_RESPONSE=$(curl -s "http://localhost:$MOCK_SERVER_PORT/health")
echo -e "${GREEN}Health check: $HEALTH_RESPONSE${NC}"

# 4. Ejecutar tests E2E
echo -e "\n${YELLOW}[4/5] Ejecutando tests E2E...${NC}"
echo -e "${GREEN}========================================${NC}"

export SARAI_MCP_URL="http://localhost:$MOCK_SERVER_PORT"
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# Ejecutar tests con pytest
cd "$PROJECT_ROOT"

if pytest tests/test_e2e_integration.py -v -s --tb=short; then
    TEST_RESULT=0
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ TESTS E2E PASARON${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    TEST_RESULT=1
    echo -e "\n${RED}========================================${NC}"
    echo -e "${RED}❌ TESTS E2E FALLARON${NC}"
    echo -e "${RED}========================================${NC}"
fi

# 5. Resultados
echo -e "\n${YELLOW}[5/5] Resultados:${NC}"

if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Integración HLCS ↔ SARAi: OK${NC}"
    echo -e "${GREEN}✅ Workflows: OK${NC}"
    echo -e "${GREEN}✅ Calidad: OK${NC}"
    echo -e "${GREEN}✅ Rendimiento: OK${NC}"
    echo -e "\n${GREEN}🎉 HLCS está listo para producción${NC}"
else
    echo -e "${RED}❌ Algunos tests fallaron${NC}"
    echo -e "${YELLOW}Revisa los logs arriba para detalles${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Logs del servidor mock guardados en: /tmp/mock_sarai_server.log${NC}"
