"""Invoca el endpoint con una imagen del test set local y muestra el resultado."""
import json
import os
import subprocess
import sys
import boto3


def main(image_path):
    creds = subprocess.check_output(
        ["aws", "configure", "export-credentials", "--format", "env-no-export"]
    ).decode()
    for line in creds.strip().split("\n"):
        k, _, v = line.partition("=")
        os.environ[k] = v

    runtime = boto3.client("sagemaker-runtime", region_name="us-east-2")

    with open(image_path, "rb") as f:
        payload = f.read()

    resp = runtime.invoke_endpoint(
        EndpointName="mlemons-modelo-a-endpoint",
        ContentType="application/x-image",
        Body=payload,
    )
    body = json.loads(resp["Body"].read())
    print("Imagen :", image_path)
    print("Resp   :", json.dumps(body, indent=2))


if __name__ == "__main__":
    img = sys.argv[1] if len(sys.argv) > 1 else "data/lemons/good_quality/good_quality_0.jpg"
    main(img)
