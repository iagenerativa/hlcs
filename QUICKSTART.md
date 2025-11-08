# HLCS Quick Start Guide

## 🚀 Local Development (Without Docker)

### 1. Setup Environment

```bash
cd ~/hlcs

# Create virtual environment (Python 3.11+ required, 3.12+ recommended)
python3.11 -m venv .venv  # or python3.12 for best performance
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 2. Generate Proto Stubs (Optional - for full gRPC)

```bash
bash scripts/generate_proto.sh
```

**Note**: This requires `grpcio-tools`. For MVP, you can skip this and use REST API only.

### 3. Run REST Gateway (Recommended for Development)

```bash
# Make sure SARAi MCP Server is running on http://localhost:3000
# Or update SARAI_MCP_URL in .env

python -m src.hlcs.rest_gateway.server
```

**Output**:
```
INFO: Started server process
INFO: Waiting for application startup.
INFO: HLCS REST Gateway Starting
INFO: Port: 4001
INFO: SARAi MCP URL: http://localhost:3000
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:4001
```

### 4. Test the API

```bash
# Health check
curl http://localhost:4001/health

# Status
curl http://localhost:4001/api/v1/status

# Simple query
curl -X POST http://localhost:4001/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Hola, ¿cómo estás?"}'

# Complex query
curl -X POST http://localhost:4001/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explica qué son los agujeros negros",
    "options": {"quality_threshold": 0.8, "max_iterations": 3}
  }'
```

---

## 🐳 Docker Development

### 1. Build Image

```bash
docker-compose build
```

### 2. Run Services

```bash
# Start HLCS + SARAi (if available)
docker-compose up -d

# Or just HLCS (connect to external SARAi)
docker-compose up -d hlcs
```

### 3. Check Logs

```bash
docker-compose logs -f hlcs
```

### 4. Test

```bash
# From host machine
curl http://localhost:4001/health

# Or exec into container
docker-compose exec hlcs bash
```

---

## 🧪 Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src/hlcs --cov-report=html

# Run specific test file
pytest tests/test_orchestrator.py -v

# Run fast tests only (skip slow ones)
pytest -m "not slow"
```

**Expected Output**:
```
========== test session starts ==========
collected 15 items

tests/test_orchestrator.py ......... [60%]
tests/test_mcp_client.py .....     [93%]
tests/test_rest_api.py ..           [100%]

========== 15 passed in 2.34s ==========
```

---

## 📊 Using Makefile (Recommended)

```bash
# Show all available commands
make help

# Install dependencies
make install

# Generate proto stubs
make proto

# Build Docker image
make build

# Start services
make up

# Check status
make status

# Test query
make test-query

# Run tests
make test

# View logs
make logs

# Stop services
make down
```

---

## 🔧 Troubleshooting

### SARAi MCP Server Not Available

If you get "SARAi MCP Server not reachable":

1. Check if SARAi is running:
   ```bash
   curl http://localhost:3000/health
   ```

2. Update `.env` with correct URL:
   ```bash
   SARAI_MCP_URL=http://your-sarai-host:3000
   ```

3. For testing without SARAi, the orchestrator will use mock responses.

### Port Already in Use

If port 4001 is busy:

```bash
# Change in .env
HLCS_REST_PORT=4002

# Or kill existing process
lsof -ti:4001 | xargs kill -9
```

### Import Errors

Make sure PYTHONPATH is set:

```bash
export PYTHONPATH=$PWD/src:$PYTHONPATH
python -m hlcs.rest_gateway.server
```

---

## 📖 Next Steps

1. **Integrate with SARAi**: Connect to real SARAi MCP Server
2. **Generate Proto Stubs**: Run `make proto` for full gRPC support
3. **Deploy to Production**: Use Docker Compose with proper networking
4. **Monitor**: Add Prometheus metrics endpoint
5. **Scale**: Deploy multiple HLCS instances behind load balancer

---

## 🤝 Contributing

See main `README.md` for contribution guidelines.

---

**Questions?** Check the main README or open an issue.
