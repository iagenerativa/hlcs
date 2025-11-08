# Python Version Standard - HLCS & SARAi Ecosystem

**Fecha**: 7 de noviembre de 2025  
**Versión Estándar**: **Python >=3.11**

---

## 🎯 Decisión de Versión

**Versión mínima requerida**: Python 3.11+

**Razones**:

1. **Nuevas características requeridas**: 
   - `list[str]` syntax (sin `from typing import List`)
   - ExceptionGroups para manejo de errores concurrentes
   - Mejor soporte para async/await
   - Performance mejorado (~10-20% más rápido que 3.10)
   
2. **Consistencia**: Todos los componentes de SARAi AGI usan la misma versión base
3. **Estabilidad**: Python 3.11+ es estable y ampliamente soportado
4. **Forward compatibility**: Compatible con Python 3.12+ y 3.13 (no-GIL cuando esté disponible)
5. **Modern features**: Type hints mejorados, mejor performance, seguridad

**Recomendado**: Python 3.12+ para mejor rendimiento

---

## 📦 Componentes Actualizados

### HLCS (High-Level Consciousness System)

✅ **Dockerfile**:
```dockerfile
FROM python:3.12-slim as builder
...
FROM python:3.12-slim
```

✅ **README.md**:
```bash
# Python 3.11+ required (3.12+ recommended)
python --version
```

✅ **QUICKSTART.md**:
```bash
python3.11 -m venv .venv  # or python3.12
```

---

### Propuesta de Modularización (PROPUESTA_MODULARIZACION_SARAI.md)

Todos los módulos actualizados a **Python 3.11+** (3.12+ recomendado):

- ✅ **HLCS**: Python 3.11+ (3.12+ recomendado para mejor performance)
- ✅ **SARAi Core**: Python 3.11+ (3.12+ recomendado) 
- ✅ **SAUL**: Python 3.12+
- ✅ **Vision**: Python 3.12+
- ✅ **Audio**: Python 3.12+
- ✅ **RAG**: Python 3.12+
- ✅ **Memory**: Python 3.12+
- ✅ **Skills**: Python 3.12+

---

## 🔄 Migración para Desarrolladores

### Si tienes instalación local existente:

```bash
# 1. Eliminar virtualenv antiguo
cd ~/hlcs
rm -rf .venv

# 2. Verificar versión Python
python3.12 --version
# Output esperado: Python 3.12.x

# 3. Crear nuevo virtualenv
python3.12 -m venv .venv
source .venv/bin/activate

# 4. Reinstalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 5. Verificar instalación
python --version
pytest --version
```

### Si usas Docker:

```bash
# 1. Rebuild imagen
cd ~/hlcs
docker build -t hlcs:latest .

# 2. Verificar versión en container
docker run --rm hlcs:latest python --version
# Output esperado: Python 3.12.x

# 3. Recrear containers
docker-compose down
docker-compose up --build -d
```

---

## ✅ Verificación de Compatibilidad

### Dependencias Core (verificadas con Python 3.12):

```
✅ grpcio==1.60.0
✅ grpcio-tools==1.60.0
✅ fastapi==0.109.0
✅ uvicorn[standard]==0.27.0
✅ pydantic==2.5.3
✅ httpx==0.26.0
✅ pytest==7.4.3
✅ pytest-asyncio==0.21.1
```

Todas las dependencias son **100% compatibles** con Python 3.12+.

---

## 🚀 Python 3.13+ (Futuro)

### No-GIL (PEP 703)

Python 3.13+ introduce **free-threading** (no-GIL):

```bash
# Compilar Python 3.13 con no-GIL
./configure --disable-gil
make
make install

# O usar build oficial (cuando esté disponible)
python3.13t  # 't' = free-threading
```

**Nota**: HLCS y todos los módulos son **compatibles con Python 3.13+**, pero **no dependen** de no-GIL. Cuando esté disponible y estable, se puede actualizar sin cambios de código.

---

## 📋 Checklist de Actualización

Para crear un nuevo módulo en el ecosistema SARAi AGI:

- [ ] **Dockerfile**: `FROM python:3.12-slim`
- [ ] **README.md**: Prerequisites especifica `Python 3.12+`
- [ ] **QUICKSTART**: Comandos usan `python3.12`
- [ ] **requirements.txt**: Todas las deps compatibles con 3.12+
- [ ] **CI/CD**: GitHub Actions matriz incluye Python 3.12
- [ ] **Tests**: Ejecutados y pasados en Python 3.12+

---

## 🔗 Referencias

- **HLCS Dockerfile**: [~/hlcs/Dockerfile](~/hlcs/Dockerfile)
- **HLCS README**: [~/hlcs/README.md](~/hlcs/README.md)
- **Propuesta Arquitectura**: [~/sarai-agi/PROPUESTA_MODULARIZACION_SARAI.md](~/sarai-agi/PROPUESTA_MODULARIZACION_SARAI.md)
- **Python 3.12 Release Notes**: https://docs.python.org/3.12/whatsnew/3.12.html
- **Python 3.13 no-GIL PEP**: https://peps.python.org/pep-0703/

---

## 📞 Soporte

Si encuentras problemas de compatibilidad con Python 3.12+:

1. Verifica que usas las versiones exactas de `requirements.txt`
2. Asegúrate de que `pip` está actualizado: `pip install --upgrade pip`
3. Revisa que no hay conflictos de versiones: `pip check`
4. Reporta en GitHub Issues si el problema persiste

---

**Última actualización**: 6 de noviembre de 2025  
**Mantenedor**: Equipo SARAi AGI
