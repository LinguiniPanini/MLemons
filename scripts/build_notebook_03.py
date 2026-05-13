"""Genera notebooks/03_modelo_a_sagemaker.ipynb desde codigo Python.

Idempotente: regenera el notebook completo. Util para mantener notebooks bajo
control de version legible (los .ipynb son JSON ruidoso).

Uso:
    python scripts/build_notebook_03.py
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
    "# 03 - Entrenamiento Modelo A en SageMaker\n\n"
    "Toma el mismo `script.py` que corrimos local en el notebook 01/02 y lo ejecuta como SageMaker Training Job.\n\n"
    "**Patron canonico**: slide 02 (estimator + fit + metric_definitions) + slide 04 (registro en Model Registry).\n\n"
    "## Pre-requisitos\n"
    "- Buckets y roles aplicados con `make apply` (Bloque 1).\n"
    "- Dataset subido a `s3://mlemons-raw-<acct>/lemons/` (script: `aws s3 sync data/lemons s3://.../lemons/`).\n"
    "- AWS CLI con sesion activa (`aws configure export-credentials` funciona)."
))

cells.append(nbf.v4.new_code_cell(
    "import os\n"
    "import subprocess\n"
    "import boto3\n"
    "import sagemaker\n"
    "from sagemaker.pytorch import PyTorch\n"
    "\n"
    "# Cargar credenciales temporales (AWS CLI v2 usa session login en este equipo)\n"
    "creds = subprocess.check_output(['aws', 'configure', 'export-credentials', '--format', 'env-no-export']).decode()\n"
    "for line in creds.strip().split('\\n'):\n"
    "    k, _, v = line.partition('=')\n"
    "    os.environ[k] = v\n"
    "\n"
    "region = 'us-east-2'\n"
    "boto_sess = boto3.Session(region_name=region)\n"
    "sm_session = sagemaker.Session(boto_session=boto_sess)\n"
    "account = boto_sess.client('sts').get_caller_identity()['Account']\n"
    "role = f'arn:aws:iam::{account}:role/mlemons-sagemaker-role'\n"
    "\n"
    "bucket_raw = f'mlemons-raw-{account}'\n"
    "bucket_models = f'mlemons-models-{account}'\n"
    "print('Account :', account)\n"
    "print('Region  :', region)\n"
    "print('Role    :', role)\n"
    "print('Raw     :', bucket_raw)\n"
    "print('Models  :', bucket_models)"
))

cells.append(nbf.v4.new_markdown_cell(
    "## Datos\n\n"
    "Dataset ya esta en `s3://mlemons-raw-<acct>/lemons/`. Sanity check de objetos:"
))

cells.append(nbf.v4.new_code_cell(
    "train_s3 = f's3://{bucket_raw}/lemons'\n"
    "print('Train channel:', train_s3)\n"
    "\n"
    "s3 = boto_sess.client('s3')\n"
    "paginator = s3.get_paginator('list_objects_v2')\n"
    "count = sum(len(p.get('Contents', [])) for p in paginator.paginate(Bucket=bucket_raw, Prefix='lemons/'))\n"
    "print(f'Objetos en train channel: {count}')"
))

cells.append(nbf.v4.new_markdown_cell(
    "## PyTorch estimator\n\n"
    "- `framework_version = '2.0.1'`, `py_version = 'py310'` alineado con el container ECR del slide 05.\n"
    "- `instance_type = 'ml.t3.medium'` (default account quota).\n"
    "- `metric_definitions` capturan los prints de `Test accuracy/Test loss` del script.\n"
    "- `source_dir = '../src/modelo_a'` para que SageMaker incluya `dataset.py` y `transforms.py`."
))

cells.append(nbf.v4.new_code_cell(
    "estimator = PyTorch(\n"
    "    entry_point='script.py',\n"
    "    source_dir='../src/modelo_a',\n"
    "    role=role,\n"
    "    framework_version='2.0.1',\n"
    "    py_version='py310',\n"
    "    instance_count=1,\n"
    "    instance_type='ml.t3.medium',\n"
    "    output_path=f's3://{bucket_models}/modelo-a/',\n"
    "    base_job_name='mlemons-modelo-a',\n"
    "    hyperparameters={\n"
    "        'epochs': 3,\n"
    "        'batch_size': 32,\n"
    "        'lr': 1e-3,\n"
    "    },\n"
    "    metric_definitions=[\n"
    "        {'Name': 'test:accuracy', 'Regex': r'Test accuracy: ([0-9.]+)'},\n"
    "        {'Name': 'test:loss',     'Regex': r'Test loss: ([0-9.]+)'},\n"
    "    ],\n"
    "    sagemaker_session=sm_session,\n"
    "    max_run=3600,\n"
    ")"
))

cells.append(nbf.v4.new_code_cell(
    "estimator.fit({'train': train_s3}, wait=True)\n"
    "job_name = estimator.latest_training_job.name\n"
    "model_data = estimator.model_data\n"
    "print('Job   :', job_name)\n"
    "print('Model :', model_data)"
))

cells.append(nbf.v4.new_markdown_cell(
    "## Metricas finales del job"
))

cells.append(nbf.v4.new_code_cell(
    "sm = boto_sess.client('sagemaker')\n"
    "desc = sm.describe_training_job(TrainingJobName=job_name)\n"
    "metrics = {m['MetricName']: m['Value'] for m in desc.get('FinalMetricDataList', [])}\n"
    "print('Final metrics:')\n"
    "for k, v in metrics.items():\n"
    "    print(f'  {k:18s} = {v}')"
))

cells.append(nbf.v4.new_markdown_cell(
    "## MLflow tracking (backend local)\n\n"
    "Patron del slide 04 con backend file-based en `mlruns/` (gitignored). "
    "Para Databricks CE en el futuro: `mlflow.set_tracking_uri('databricks')`."
))

cells.append(nbf.v4.new_code_cell(
    "import mlflow\n"
    "\n"
    "mlflow.set_tracking_uri('file:./mlruns')\n"
    "mlflow.set_experiment('MLemons-ModeloA')\n"
    "\n"
    "with mlflow.start_run(run_name=job_name) as run:\n"
    "    mlflow.log_param('framework', 'pytorch-2.0.1')\n"
    "    mlflow.log_param('instance_type', 'ml.t3.medium')\n"
    "    mlflow.log_param('epochs', 3)\n"
    "    mlflow.log_param('batch_size', 32)\n"
    "    mlflow.log_param('lr', 1e-3)\n"
    "    for k, v in metrics.items():\n"
    "        mlflow.log_metric(k.replace(':', '_'), v)\n"
    "    mlflow.log_param('model_data_s3', model_data)\n"
    "    mlflow.log_param('training_job_name', job_name)\n"
    "    print('MLflow run:', run.info.run_id)"
))

cells.append(nbf.v4.new_markdown_cell(
    "## Registrar Model Package\n\n"
    "Crear `ModelPackageGroup` (idempotente) + Model Package con `PendingManualApproval`. "
    "Aprobacion manual antes de promover a endpoint."
))

cells.append(nbf.v4.new_code_cell(
    "group_name = 'mlemons-modelo-a-group'\n"
    "\n"
    "try:\n"
    "    sm.create_model_package_group(\n"
    "        ModelPackageGroupName=group_name,\n"
    "        ModelPackageGroupDescription='Modelo A binario (sano vs defectuoso) - clasificacion de limones',\n"
    "    )\n"
    "    print('Grupo creado:', group_name)\n"
    "except sm.exceptions.ResourceInUse:\n"
    "    print('Grupo ya existe:', group_name)\n"
    "\n"
    "image_uri = sagemaker.image_uris.retrieve(\n"
    "    framework='pytorch',\n"
    "    region=region,\n"
    "    version='2.0.1',\n"
    "    py_version='py310',\n"
    "    instance_type='ml.t3.medium',\n"
    "    image_scope='inference',\n"
    ")\n"
    "print('Inference image:', image_uri)\n"
    "\n"
    "resp = sm.create_model_package(\n"
    "    ModelPackageGroupName=group_name,\n"
    "    ModelPackageDescription=f'Trained job {job_name}',\n"
    "    InferenceSpecification={\n"
    "        'Containers': [{\n"
    "            'Image': image_uri,\n"
    "            'ModelDataUrl': model_data,\n"
    "        }],\n"
    "        'SupportedContentTypes': ['application/x-image'],\n"
    "        'SupportedResponseMIMETypes': ['application/json'],\n"
    "    },\n"
    "    ModelApprovalStatus='PendingManualApproval',\n"
    ")\n"
    "package_arn = resp['ModelPackageArn']\n"
    "print('Model package:', package_arn)"
))

cells.append(nbf.v4.new_markdown_cell(
    "## Aprobar manualmente\n\n"
    "Tras revisar las metricas:"
))

cells.append(nbf.v4.new_code_cell(
    "sm.update_model_package(\n"
    "    ModelPackageArn=package_arn,\n"
    "    ModelApprovalStatus='Approved',\n"
    "    ApprovalDescription='Cumple objetivo accuracy >= 0.90',\n"
    ")\n"
    "print('Aprobado:', package_arn)"
))

cells.append(nbf.v4.new_markdown_cell(
    "## Salida para el Bloque 3\n\n"
    "Bloque 3 (endpoint) consume:\n"
    "- `MODEL_PACKAGE_ARN`\n"
    "- `MODEL_DATA_S3`\n"
    "- `IMAGE_URI`"
))

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11"}
}

out = "notebooks/03_modelo_a_sagemaker.ipynb"
nbf.write(nb, out)
print("Wrote", out, "with", len(cells), "cells")
