"""Lambda handler para compute_score: recibe predicciones, calcula score, persiste a DynamoDB."""
import json
import os
import time
import uuid
import boto3

from scoring_logic import score_lote, DEFAULT_THRESHOLD

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "mlemons_lotes")


def lambda_handler(event, context):
    # event esperado:
    # {
    #   "lote_id": "...",
    #   "predictions": [{"image_s3_uri": "...", "predicted_class": "...", "confidence": float}, ...]
    # }
    lote_id = event.get("lote_id") or str(uuid.uuid4())
    predictions = event.get("predictions", [])
    threshold = float(event.get("threshold", DEFAULT_THRESHOLD))

    resultado = score_lote(predictions, threshold=threshold)

    item = {
        "lote_id": lote_id,
        "timestamp": int(time.time()),
        "score": str(resultado["score"]),  # DynamoDB no acepta float, usar Decimal o str
        "decision": resultado["decision"],
        "distribucion": resultado["distribucion"],
        "n_images": resultado["n_images"],
        "threshold": str(threshold),
    }

    table = dynamodb.Table(TABLE_NAME)
    table.put_item(Item=item)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "lote_id": lote_id,
                "score": resultado["score"],
                "decision": resultado["decision"],
                "distribucion": resultado["distribucion"],
                "n_images": resultado["n_images"],
            }
        ),
    }
