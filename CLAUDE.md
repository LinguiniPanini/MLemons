# CLAUDE.md — MLemons (repo entregable)

> Este archivo se carga si Claude Code se abre directamente en `MLemons/`.
> El **contexto completo** del proyecto vive en el repo padre `MLemons-ClaudePot/`. Si trabajas con ese repo padre como working dir, las reglas de su `CLAUDE.md` aplican y este archivo es complementario.

---

## 🚨 Identifica primero CON QUIÉN estás trabajando

- **Si es Luis** → área ML/datos/modelos.
- **Si es Francisco** → área AWS/infra/pipeline.

Si no estás seguro, pregúntale antes de modificar nada.

## 🚨 Tabla de ownership

| Carpeta / Archivo | Owner |
|---|---|
| `src/modelo_a/`, `src/modelo_b/`, `src/synthetic_dataset/`, `src/lambda_code/compute_score/scoring_logic.py`, `notebooks/`, `data/` | **Luis** |
| `infra/*.tf`, `src/lambda_code/*/handler.py`, `src/inference_server/`, `scripts/setup_ec2.py`, `.github/workflows/` | **Francisco** |
| `requirements.txt`, `Makefile`, `README.md`, `pyproject.toml` | **Compartido (PR review obligatorio)** |

---

## Cómo funciona

Este repo (`MLemons/`) es el **entregable** del proyecto. Aquí va:
- Código Python (modelos, Lambdas, FastAPI server).
- Terraform (todo `infra/`).
- Notebooks de exploración y demo.
- Tests.
- DVC metafiles (los datos crudos viven en S3).

**El contexto, conocimiento y planes** vive en el repo padre `MLemons-ClaudePot/`. Lee desde paths relativos cuando lo necesites:
- `../.claude/memory/` — memorias compartidas
- `../knowledge/slide-XX-*.md` — extractos del curso
- `../plans/` — roadmap, división, branching, prompts
- `../docs/superpowers/specs/*.md` — diseño aprobado

## Reglas cortas (ver detalle en `../CLAUDE.md`)

1. **Stack y estilo**: solo lo enseñado en `../slides/`. Patrones canónicos en `../knowledge/`. Estilo del profesor en `../.claude/memory/class_style.md`.
2. **Anti-IA**: aplicar `../plans/02-anti-ai-style-guide.md` antes de cualquier código generado.
3. **Branching**: ver `../plans/04-branching-and-push-rules.md`. Una rama por feature, naming `<luis|francisco>-<scope>-<descripcion>`.
4. **Push**: nunca automático. Dar comandos al estudiante.
5. **Cleanup**: `terraform destroy`, `make endpoint-down` al fin de cada lab.
6. **NO modificar archivos del compañero** sin coordinar. Ver tabla de ownership arriba.

## Estructura

```
MLemons/
├── src/
│   ├── modelo_a/, modelo_b/        Luis (PyTorch)
│   ├── lambda_code/                Francisco (handlers); scoring_logic.py es de Luis
│   ├── inference_server/           Francisco (FastAPI Modelo A)
│   ├── synthetic_dataset/          Luis
│   └── shared/
├── infra/                          Francisco (Terraform)
├── notebooks/                      Luis
├── scripts/                        Francisco (Paramiko/SCP)
├── tests/
├── data/                           DVC + S3
├── docs/
└── .github/workflows/              Francisco (CI/CD GHA)
```
