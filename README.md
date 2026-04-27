# MLemons

Sistema de visión por computadora para clasificación de calidad de limones con AWS.

Proyecto del curso MLOps en ITESO (Spring 2026). Autores: Luis Alberto González Escamilla y Francisco de Jesús Delgado Carrasco.

## Diseño

Ver `../docs/superpowers/specs/2026-04-26-mlemons-architecture-design.md` (en el repo padre `MLemons-ClaudePot/`).

Resumen:
- **Modelo A** — clasificación binaria Sano vs Defectuoso (MobileNetV2 transfer learning) → desplegado en EC2/FastAPI/Docker/NGINX.
- **Modelo B** — detección en lote (YOLOv8) → desplegado en SageMaker endpoint.
- **Pipeline E2E**: Cámara → S3 → EventBridge → Step Function → Modelo B → crops → Modelo A (batch) → Lambda scoring → DynamoDB → SNS si rechazado.
- **Stack**: Terraform + Step Functions + Lambda + DynamoDB + SNS + EC2 + GitHub Actions.

## Setup

1. Configurar AWS CLI con region `us-east-2`:
   ```bash
   aws configure --profile mlemons
   export AWS_PROFILE=mlemons
   ```
2. Instalar dependencias Python (crea `.venv/` automáticamente):
   ```bash
   make install
   ```
   Para correr Jupyter o comandos ad-hoc, activa el venv:
   ```bash
   source .venv/bin/activate
   ```
3. Aplicar Terraform base:
   ```bash
   cd infra && terraform init && terraform apply
   ```

## Cómo entrenar Modelo A

Ver `notebooks/03_modelo_a_training.ipynb`.

## Cómo correr la inferencia E2E

Ver `notebooks/05_pipeline_inference.ipynb`.

## Cómo destruir infraestructura

```bash
make destroy
```

## Tests

```bash
make test
```
