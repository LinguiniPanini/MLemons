# MLemons

Sistema de vision por computadora para clasificacion de calidad de limones con AWS.

Proyecto del curso MLOps en ITESO (Spring 2026). Autor: Luis Alberto Gonzalez Escamilla.

## Diseno

Ver `../docs/superpowers/specs/2026-04-26-mlemons-architecture-design.md` (en el repo padre `MLemons-ClaudePot/`).

**Scope actual** (recortado 2026-05-12, ver `../STATUS.md`):
- **Modelo A** — clasificacion binaria Sano vs Defectuoso (MobileNetV2 transfer learning, entrenado en SageMaker, desplegado como SageMaker endpoint).
- **Pipeline E2E**: imagen S3 -> Step Functions -> Lambda `invoke_modelo_a` -> SageMaker endpoint -> Lambda `compute_score` -> DynamoDB.
- **Stack**: Terraform + Step Functions + Lambda + DynamoDB + SageMaker endpoint + GitHub Actions (CI).

Componentes recortados de la spec original: Modelo B (deteccion), inferencia hibrida FastAPI/EC2, dataset sintetico de lotes, EventBridge auto-trigger. Documentados como extension futura.

## Setup

### Prerequisitos

- **Python 3.11** (no 3.12+). El stack PyTorch / SageMaker DLC esta fijado a 3.11 en clase.
- **AWS CLI v2** con sesion activa (`aws sts get-caller-identity` debe responder). En este equipo se usa `aws login` (CLI v2.33+) — si la sesion expiro, re-login y `aws configure export-credentials --format env` para Terraform.
- **Terraform** >= 1.5.
- **DVC** instalado en el venv (parte de `requirements.txt`).

### Pasos

```bash
make install                 # crea .venv y instala dependencias
source .venv/bin/activate    # para Jupyter / scripts ad-hoc
make apply                   # terraform apply (exporta creds automaticamente)
```

## Flujo de despliegue end-to-end

### 1. Infra base
```bash
make apply
```
Crea 4 buckets S3, 3 roles IAM, DynamoDB, Lambdas, Step Function, alarmas CloudWatch. El endpoint SageMaker NO se crea aun (depende del Model Package).

### 2. Dataset versionado y subido a S3
```bash
dvc remote add -d s3remote s3://mlemons-raw-<acct>/dvc-store   # primera vez
dvc push                                                       # sube data/lemons/ y models/modelo_a.pth
aws s3 sync data/lemons s3://mlemons-raw-<acct>/lemons/        # estructura plana para SageMaker
```

### 3. Entrenar Modelo A en SageMaker
```bash
python scripts/run_training.py
```
Dispara el training job sin Jupyter. Equivalente al notebook `03_modelo_a_sagemaker.ipynb`. Produce un job `mlemons-modelo-a-*` con `model.tar.gz` en `s3://mlemons-models-<acct>/modelo-a/.../output/`.

### 4. Empaquetar modelo y registrarlo
SageMaker PyTorch container espera `code/inference.py` dentro del `model.tar.gz`; el training job solo guarda `modelo_a.pth`. Por eso hay que repackagear:
```bash
python scripts/repack_model.py            # baja, inyecta code/inference.py, sube a /repacked/
python scripts/register_model_package.py  # crea Model Package Group + Approved
```
El segundo script imprime el ARN del Model Package al final.

### 5. Crear endpoint con el Model Package aprobado
```bash
cd infra
terraform apply -var "model_package_arn=<arn-impreso-en-paso-4>"
```

### 6. Smoke test y demo end-to-end
```bash
python scripts/smoke_test_endpoint.py data/lemons/good_quality/good_quality_0.jpg
# si responde, abrir notebooks/04_demo_e2e.ipynb para correr el pipeline completo
```
El notebook 04 sube 6 imagenes mixtas a S3, dispara la Step Function, valida que DynamoDB tenga el item con score + decision.

## Cleanup

```bash
make endpoint-down           # apaga endpoint SageMaker (mas costo)
make destroy                 # terraform destroy de todo
```

## Tests

```bash
make test                    # pytest tests/ + black --check (19 tests)
```

Cobertura:
- `test_scoring_logic.py` (9 tests) — logica pura del score sin AWS.
- `test_invoke_modelo_a.py` (5 tests) — handler con mocks de S3 y SageMaker runtime.
- `test_compute_score_handler.py` (5 tests) — handler con mock de DynamoDB.

CI corre los 19 tests en GitHub Actions en cada push/PR a `main`.

## Estructura

```
MLemons/
  src/
    modelo_a/                # script.py, dataset.py, transforms.py, eval.py, inference.py
    lambda_code/
      invoke_modelo_a/       # handler.py (invoca endpoint)
      compute_score/         # handler.py + scoring_logic.py (puro, testeable)
  infra/                     # main.tf, s3.tf, iam.tf, dynamodb.tf, lambda.tf, sagemaker.tf, sfn.tf, cloudwatch.tf
  notebooks/
    01_eda.ipynb             # EDA del Kaggle dataset
    02_modelo_a_demo.ipynb   # demo local del modelo entrenado
    03_modelo_a_sagemaker.ipynb  # training en SageMaker + Model Registry
    04_demo_e2e.ipynb        # pipeline end-to-end en AWS
  scripts/
    build_notebook_03.py        # regenera notebook 03 desde Python
    build_notebook_04.py        # idem 04
    run_training.py             # corre el training en SageMaker sin Jupyter
    repack_model.py             # inyecta code/inference.py al model.tar.gz
    register_model_package.py   # registra el modelo en Model Registry (Approved)
    smoke_test_endpoint.py      # invoca el endpoint con una imagen local
  tests/
    test_scoring_logic.py            # 9 tests del scoring puro
    test_invoke_modelo_a.py          # 5 tests del handler con mocks
    test_compute_score_handler.py    # 5 tests del handler con mock DynamoDB
  data/                      # ignorado, gestionado por DVC (data/lemons.dvc)
  models/                    # ignorado, gestionado por DVC (models/modelo_a.pth.dvc)
  .dvc/                      # config DVC
  .github/workflows/         # CI: black --check + pytest tests/
```
