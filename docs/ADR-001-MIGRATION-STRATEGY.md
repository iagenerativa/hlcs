# ADR-001: sarai-agi Component Migration Strategy

**Status**: 🟡 PROPOSED  
**Date**: 8 de noviembre de 2025  
**Decision Makers**: HLCS Lead, sarai-agi Lead, Product Owner  
**Related**: `docs/MIGRATION_CONFLICT_ANALYSIS.md`

---

## Context

HLCS v3.0 está en producción con sistemas autónomos completos:
- Meta-Consciousness Layer v0.2
- Strategic Planning System v0.5
- Multi-Stakeholder SCI v0.4
- KnowledgeRAG v2.0
- Phi4MiniAGI System

Se planea migrar componentes desde `sarai-agi` que tienen **colisiones arquitecturales** con sistemas existentes.

---

## Decision

Adoptar **HYBRID APPROACH** con 4 estrategias diferenciadas:

### 1. MIGRATE (Safe Components) ✅
**Components**: Emotion System, Monitoring & Observability  
**Timeline**: Day 3-8  
**Risk**: 🟢 LOW

### 2. COEXIST (Complementary Components) ⚠️
**Components**: Meta-Reasoner + Strategic Planning, Active Learning + KnowledgeRAG  
**Timeline**: Day 9-14  
**Risk**: 🟡 MEDIUM

### 3. DEFER (Blockers) 🔴
**Components**: LoRA Trainer  
**Timeline**: FEB 2026 (HLCS v0.4)  
**Risk**: 🟢 LOW (no immediate impact)

### 4. MERGE (Future) 🔮
**Components**: IntegratedConsciousness ↔ MetaConsciousnessLayer  
**Timeline**: FEB-MAR 2026 (HLCS v0.4)  
**Risk**: 🔴 HIGH (architectural refactor)

---

## Consequences

### Positive
- ✅ Entrega valor inmediato (Emotion + Monitoring)
- ✅ Evita regresiones en sistemas críticos
- ✅ Especialización de componentes (separation of concerns)
- ✅ Tiempo para planificar merge correcto (v0.4)

### Negative
- ❌ Posible duplicación temporal de lógica (Meta-Reasoner + Planning)
- ❌ Overhead de coordinación entre sistemas coexistentes
- ❌ LoRA features no disponibles hasta v0.4

### Neutral
- 🟡 Requiere definir APIs de integración claras
- 🟡 Aumenta complejidad arquitectural temporalmente

---

## Alternatives Considered

### A. MERGE ALL (Fusión Total)
**Rejected**: Muy riesgo, 10-15 días de refactor, posibles regresiones

### B. REPLACE (Reemplazo)
**Rejected**: Pérdida de features HLCS v3.0 ya en producción

### C. DEFER ALL (Postponer Todo)
**Rejected**: No aprovecha features valiosos (Emotion, Active Learning)

---

## Implementation Plan

### Phase 1: Safe Migrations (Day 3-8)
```
src/hlcs/emotion/           # NEW
  emotion_engine.py
  sentiment_analyzer.py
  
src/hlcs/monitoring/        # UPGRADE
  prometheus_metrics.py
  health_checks.py
```

### Phase 2: Coexistence Setup (Day 9-14)
```
src/hlcs/reasoning/         # NEW (Meta-Reasoner)
  meta_reasoner.py          # CoT reasoning primitives
  chain_of_thought.py
  
src/hlcs/learning/          # NEW (Active Learning)
  active_learning.py
  feedback_loop.py
  preference_learner.py
```

**Integration Points**:
- `MetaReasoner` → `ScenarioSimulator` (feed reasoning)
- `ActiveLearning` → `KnowledgeRAG` (consolidation events)

### Phase 3: Documentation & Testing (Day 15-18)
- Integration API docs
- End-to-end tests
- Performance benchmarks

---

## Risks & Mitigation

| Risk | Severity | Mitigation |
|------|----------|------------|
| Duplicación de lógica | 🟡 MEDIUM | APIs claras, integration tests |
| Regresión Meta-Consciousness | 🔴 HIGH | NO tocar hasta v0.4, feature flags |
| Overhead coordinación | 🟡 MEDIUM | Event-driven architecture |
| Dependency hell (LoRA) | 🔴 HIGH | **DEFER a v0.4** |

---

## Success Metrics

- ✅ 0 regresiones en tests existentes (58/84 passing)
- ✅ Emotion System integrado en < 3 días
- ✅ Monitoring metrics operational en < 5 días
- ✅ Active Learning + KnowledgeRAG working en < 7 días
- ✅ Documentation completa en < 2 días

---

## Approval

- [ ] **HLCS Lead**: ______________________ Date: ______
- [ ] **sarai-agi Lead**: _________________ Date: ______
- [ ] **Product Owner**: __________________ Date: ______
- [ ] **DevOps**: _________________________ Date: ______

---

## References

- [MIGRATION_CONFLICT_ANALYSIS.md](./MIGRATION_CONFLICT_ANALYSIS.md)
- [AUTONOMOUS_HLCS.md](./AUTONOMOUS_HLCS.md)
- [PROGRESS_REPORT.md](../PROGRESS_REPORT.md)

---

**ADR Status**: 🟡 AWAITING APPROVAL  
**Next Action**: Schedule Architecture Alignment Meeting
