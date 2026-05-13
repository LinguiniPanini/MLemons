"""Descarga model.tar.gz, agrega code/inference.py + requirements.txt, sube como modelo nuevo.

SageMaker PyTorch container espera handlers en code/inference.py dentro del
tar.gz cuando no se pasa source_dir al Model. El training job de Python solo
guarda modelo_a.pth, por lo que hay que repackagear.
"""
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import boto3


REGION = "us-east-2"
ACCOUNT = "898769391977"
BUCKET = f"mlemons-models-{ACCOUNT}"
ORIGINAL = f"s3://{BUCKET}/modelo-a/mlemons-modelo-a-2026-05-13-00-49-28-886/output/model.tar.gz"
REPACKED_KEY = "modelo-a/repacked/model.tar.gz"


def main(original_uri=ORIGINAL):
    creds = subprocess.check_output(
        ["aws", "configure", "export-credentials", "--format", "env-no-export"]
    ).decode()
    for line in creds.strip().split("\n"):
        k, _, v = line.partition("=")
        os.environ[k] = v

    s3 = boto3.client("s3", region_name=REGION)

    with tempfile.TemporaryDirectory() as tmp:
        # 1. Bajar el modelo original
        original_local = os.path.join(tmp, "original.tar.gz")
        src_bucket = original_uri.split("/")[2]
        src_key = "/".join(original_uri.split("/")[3:])
        print("Descargando", original_uri)
        s3.download_file(src_bucket, src_key, original_local)

        # 2. Extraer
        extract_dir = os.path.join(tmp, "extracted")
        os.makedirs(extract_dir)
        with tarfile.open(original_local, "r:gz") as t:
            t.extractall(extract_dir)
        print("Contenido original:", os.listdir(extract_dir))

        # 3. Agregar code/inference.py + requirements.txt
        code_dir = os.path.join(extract_dir, "code")
        os.makedirs(code_dir, exist_ok=True)
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        shutil.copy(
            os.path.join(repo_root, "src", "modelo_a", "inference.py"),
            os.path.join(code_dir, "inference.py"),
        )
        # requirements.txt minimo para el inference
        with open(os.path.join(code_dir, "requirements.txt"), "w") as f:
            f.write("Pillow\n")

        print("Contenido nuevo:", os.listdir(extract_dir), "+", os.listdir(code_dir))

        # 4. Empaquetar
        repacked_local = os.path.join(tmp, "repacked.tar.gz")
        with tarfile.open(repacked_local, "w:gz") as t:
            for name in os.listdir(extract_dir):
                t.add(os.path.join(extract_dir, name), arcname=name)

        # 5. Subir
        print("Subiendo a", f"s3://{BUCKET}/{REPACKED_KEY}")
        s3.upload_file(repacked_local, BUCKET, REPACKED_KEY)

    new_uri = f"s3://{BUCKET}/{REPACKED_KEY}"
    print("Listo:", new_uri)
    return new_uri


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ORIGINAL)
