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
dvc push                                                       # sube data/lemons/
aws s3 sync data/lemons s3://mlemons-raw-<acct>/lemons/        # estructura plana para SageMaker
```

### 3. Entrenar Modelo A en SageMaker
Abrir `notebooks/03_modelo_a_sagemaker.ipynb` y ejecutar celdas. Produce:
- Training job (`mlemons-modelo-a-*`)
- `model_data.tar.gz` en `s3://mlemons-models-<acct>/modelo-a/...`
- Run de MLflow local en `mlruns/`
- Model Package en `mlemons-modelo-a-group` con `ApprovalStatus = Approved`

### 4. Crear endpoint con el Model Package aprobado
```bash
# tomar el ARN del notebook 03
cd infra
terraform apply -var "model_package_arn=arn:aws:sagemaker:us-east-2:<acct>:model-package/mlemons-modelo-a-group/1"
```

### 5. Demo end-to-end
Abrir `notebooks/04_demo_e2e.ipynb`: sube 6 imagenes del test set, dispara la Step Function, valida DynamoDB.

## Cleanup

```bash
make endpoint-down           # apaga endpoint SageMaker (mas costo)
make destroy                 # terraform destroy de todo
```

## Tests

```bash
make test                    # pytest del scoring_logic + lint
```

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
    build_notebook_03.py     # regenera notebook 03 desde Python
    build_notebook_04.py     # idem 04
    run_training.py          # corre el training sin Jupyter
  tests/
    test_scoring_logic.py    # 9 tests del scoring puro
  data/                      # ignorado, gestionado por DVC
  .dvc/                      # config DVC
  .github/workflows/         # CI: black --check + pytest
```
