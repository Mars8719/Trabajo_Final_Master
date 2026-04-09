# SOC-LLM Audit Platform

## Plataforma de Auditoría Compliance para LLMs en SOC

Plataforma full-stack de 4 capas que integra auditoría automatizada, compliance scoring y Human-in-the-Loop (HITL) para operaciones SOC asistidas por LLM.

### Arquitectura

```
┌────────────────────────────────────────────────────────┐
│                    Capa 4: Frontend                     │
│  React 18 + MUI + Redux + Recharts + WebSockets        │
├────────────────────────────────────────────────────────┤
│                    Capa 3: API REST                     │
│  FastAPI + WebSocket + JWT/RBAC                         │
├────────────────────────────────────────────────────────┤
│               Capa 2: Motor de Auditoría                │
│  ComplianceEngine + HITL + BiasChecker + XAI            │
├────────────────────────────────────────────────────────┤
│                    Capa 1: LLM Engine                   │
│  Gateway + Triage + Playbook + Sanitizer                │
└────────────────────────────────────────────────────────┘
```

### Compliance Score

```
CS = Σ(wi × si) donde Σ(wi) = 1.0

Dimensiones:
- data_minimization (0.15)
- legal_basis (0.15)
- transparency (0.15)
- pipeline_security (0.15)
- bias_fairness (0.10)
- retention (0.10)
- incident_reporting (0.10)
- hitl (0.10)
```

### HITL Escalation Levels

| Nivel | Nombre     | Condición       | Acción                    |
|-------|-----------|-----------------|---------------------------|
| L0    | Auto      | CS ≥ 90         | Procesamiento automático  |
| L1    | Async     | CS 70-89        | Revisión asíncrona        |
| L2    | Sync      | CS 50-69        | Revisión síncrona         |
| L3    | Mandatory | CS < 50         | Revisión obligatoria      |
| L4    | Kill      | Inyección/Comp.  | Desactivación total LLM   |

### Quick Start

```bash
# 1. Copiar variables de entorno
cp .env.example .env

# 2. Levantar con Docker Compose
docker compose up -d

# 3. Acceder
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

### Desarrollo Local

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Tests (19 obligatorios)

```bash
cd backend
pytest tests/ -v

# Por módulo:
pytest tests/test_gdpr.py      # 5 tests GDPR
pytest tests/test_nis2.py      # 5 tests NIS2
pytest tests/test_llm_security.py # 6 tests OWASP LLM
pytest tests/test_ethics.py    # 3 tests Ethics/Bias
```

### Normativa Cubierta

- **GDPR** — Art. 5, 6, 13-14, 17, 22, 25, 30, 35
- **NIS2** — Art. 21, 23
- **EU AI Act** — Transparencia, Explicabilidad
- **DORA** — Resiliencia operativa digital
- **OWASP LLM Top 10** — 6 controles testados
- **ISO 42001** — Gobierno AI
- **FinOps** — Cost estimation por transacción
