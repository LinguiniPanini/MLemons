"""Genera notebooks/04_demo_e2e.ipynb desde codigo Python.

Demo end-to-end de inferencia: imagen S3 -> Step Functions -> DynamoDB.
Tambien permite invocar el endpoint directamente para comparar tiempos.
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
    "# 04 - Demo end-to-end\n\n"
    "Flujo completo en AWS:\n"
    "1. Subir imagen del test set a `s3://mlemons-raw/inference/<lote>/img.jpg`.\n"
    "2. Disparar Step Function con `{lote_id, images: [...]}`.\n"
    "3. SFN invoca Lambda `invoke_modelo_a` -> endpoint SageMaker -> predicciones.\n"
    "4. SFN invoca Lambda `compute_score` -> score + DynamoDB write.\n"
    "5. Leer registro en DynamoDB y validar.\n\n"
    "Pre-requisitos: notebook 03 ejecutado y Model Package aprobado, `terraform apply` con `-var model_package_arn=<arn>`."
))

cells.append(nbf.v4.new_code_cell(
    "import json\n"
    "import os\n"
    "import subprocess\n"
    "import time\n"
    "import uuid\n"
    "import boto3\n"
    "\n"
    "creds = subprocess.check_output(\n"
    "    ['aws', 'configure', 'export-credentials', '--format', 'env-no-export']\n"
    ").decode()\n"
    "for line in creds.strip().split('\\n'):\n"
    "    k, _, v = line.partition('=')\n"
    "    os.environ[k] = v\n"
    "\n"
    "region = 'us-east-2'\n"
    "sess = boto3.Session(region_name=region)\n"
    "account = sess.client('sts').get_caller_identity()['Account']\n"
    "\n"
    "s3 = sess.client('s3')\n"
    "sfn = sess.client('stepfunctions')\n"
    "dynamodb = sess.resource('dynamodb')\n"
    "\n"
    "BUCKET_RAW = f'mlemons-raw-{account}'\n"
    "STATE_MACHINE_ARN = f'arn:aws:states:{region}:{account}:stateMachine:mlemons-pipeline'\n"
    "TABLE = dynamodb.Table('mlemons_lotes')\n"
    "print('Bucket   :', BUCKET_RAW)\n"
    "print('SFN ARN  :', STATE_MACHINE_ARN)"
))

cells.append(nbf.v4.new_markdown_cell(
    "## Seleccionar imagenes del test set\n\n"
    "Tomo 4 buenas y 2 malas del dataset local para simular un lote mixto."
))

cells.append(nbf.v4.new_code_cell(
    "import glob\n"
    "import random\n"
    "random.seed(42)\n"
    "\n"
    "good = sorted(glob.glob('../data/lemons/good_quality/*.jpg'))\n"
    "bad  = sorted(glob.glob('../data/lemons/bad_quality/*.jpg'))\n"
    "muestras = random.sample(good, 4) + random.sample(bad, 2)\n"
    "print('Imagenes seleccionadas:', len(muestras))\n"
    "for p in muestras:\n"
    "    print(' ', p)"
))

cells.append(nbf.v4.new_markdown_cell(
    "## Subir imagenes a S3 y armar evento"
))

cells.append(nbf.v4.new_code_cell(
    "lote_id = f'demo-{uuid.uuid4().hex[:8]}'\n"
    "images_s3 = []\n"
    "for path in muestras:\n"
    "    name = os.path.basename(path)\n"
    "    key = f'inference/{lote_id}/{name}'\n"
    "    s3.upload_file(path, BUCKET_RAW, key)\n"
    "    images_s3.append(f's3://{BUCKET_RAW}/{key}')\n"
    "print('Lote id:', lote_id)\n"
    "print('Imagenes:')\n"
    "for u in images_s3:\n"
    "    print(' ', u)"
))

cells.append(nbf.v4.new_markdown_cell(
    "## Disparar Step Function"
))

cells.append(nbf.v4.new_code_cell(
    "payload = {'lote_id': lote_id, 'images': images_s3, 'threshold': 75}\n"
    "resp = sfn.start_execution(\n"
    "    stateMachineArn=STATE_MACHINE_ARN,\n"
    "    name=lote_id,\n"
    "    input=json.dumps(payload),\n"
    ")\n"
    "execution_arn = resp['executionArn']\n"
    "print('Execution ARN:', execution_arn)"
))

cells.append(nbf.v4.new_markdown_cell(
    "## Esperar a que termine"
))

cells.append(nbf.v4.new_code_cell(
    "for _ in range(60):\n"
    "    desc = sfn.describe_execution(executionArn=execution_arn)\n"
    "    if desc['status'] != 'RUNNING':\n"
    "        break\n"
    "    time.sleep(2)\n"
    "print('Status:', desc['status'])\n"
    "print('Output:', desc.get('output'))"
))

cells.append(nbf.v4.new_markdown_cell(
    "## Validar registro en DynamoDB"
))

cells.append(nbf.v4.new_code_cell(
    "item = TABLE.get_item(Key={'lote_id': lote_id}).get('Item')\n"
    "assert item is not None, 'No se persistio el lote en DynamoDB'\n"
    "for k, v in item.items():\n"
    "    print(f'  {k:14s} = {v}')"
))

cells.append(nbf.v4.new_markdown_cell(
    "## Cleanup opcional\n\n"
    "Si vas a re-correr el demo, borrar la entrada del lote y las imagenes en S3."
))

cells.append(nbf.v4.new_code_cell(
    "# TABLE.delete_item(Key={'lote_id': lote_id})\n"
    "# for u in images_s3:\n"
    "#     key = u.replace(f's3://{BUCKET_RAW}/', '')\n"
    "#     s3.delete_object(Bucket=BUCKET_RAW, Key=key)\n"
    "# print('cleanup ok')"
))

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11"}
}

out = "notebooks/04_demo_e2e.ipynb"
nbf.write(nb, out)
print("Wrote", out, "with", len(cells), "cells")
