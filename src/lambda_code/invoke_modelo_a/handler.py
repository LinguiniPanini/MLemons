"""Lambda handler para invoke_modelo_a: descarga imagenes de S3, las pasa al endpoint, regresa predicciones."""
import io
import json
import os
from urllib.parse import urlparse
import boto3

s3 = boto3.client("s3")
runtime = boto3.client("sagemaker-runtime")

ENDPOINT_NAME = os.environ.get("ENDPOINT_NAME", "mlemons-modelo-a-endpoint")
CLASS_NAMES = ["good_quality", "bad_quality"]  # alineado con LemonDataset


def parse_s3_uri(uri):
    parsed = urlparse(uri)
    return parsed.netloc, parsed.path.lstrip("/")


def predict_one(image_uri):
    bucket, key = parse_s3_uri(image_uri)
    obj = s3.get_object(Bucket=bucket, Key=key)
    payload = obj["Body"].read()

    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/x-image",
        Body=payload,
    )
    body = json.loads(response["Body"].read())
    # esperado del modelo: {"class": int, "confidence": float} o lista de probs
    # mantenemos compat con ambos formatos
    if isinstance(body, list):
        # raw logits o probs: argmax
        idx = max(range(len(body)), key=lambda i: body[i])
        return {
            "image_s3_uri": image_uri,
            "predicted_class": CLASS_NAMES[idx],
            "confidence": float(body[idx]),
        }
    return {
        "image_s3_uri": image_uri,
        "predicted_class": CLASS_NAMES[int(body["class"])],
        "confidence": float(body.get("confidence", 0.0)),
    }


def lambda_handler(event, context):
    # event esperado:
    # {
    #   "lote_id": "...",
    #   "images": ["s3://bucket/key.jpg", ...]
    # }
    lote_id = event["lote_id"]
    images = event.get("images", [])

    predictions = [predict_one(uri) for uri in images]

    return {
        "lote_id": lote_id,
        "predictions": predictions,
    }
