"""Tests del handler invoke_modelo_a. Mockea S3 y SageMaker runtime."""
import importlib.util
import io
import json
import os
from unittest.mock import MagicMock

# region default para evitar NoRegionError al construir los clients en el import
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-2")
os.environ.setdefault("ENDPOINT_NAME", "test-endpoint")

# Los dos handlers de Lambda se llaman handler.py. Para que no colisionen en
# sys.modules, los cargamos directo del path con importlib bajo un nombre unico.
_HANDLER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "lambda_code", "invoke_modelo_a", "handler.py"
)
_spec = importlib.util.spec_from_file_location("invoke_modelo_a_handler", _HANDLER_PATH)
handler = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(handler)


def _fake_s3_response(body_bytes):
    resp = {"Body": MagicMock()}
    resp["Body"].read.return_value = body_bytes
    return resp


def _fake_runtime_response(body_dict_or_list):
    payload = json.dumps(body_dict_or_list).encode()
    return {"Body": io.BytesIO(payload)}


def test_parse_s3_uri_separa_bucket_y_key():
    bucket, key = handler.parse_s3_uri("s3://mlemons-raw/inference/lote123/img.jpg")
    assert bucket == "mlemons-raw"
    assert key == "inference/lote123/img.jpg"


def test_predict_one_con_dict_response_mapea_clase(monkeypatch):
    fake_s3 = MagicMock()
    fake_s3.get_object.return_value = _fake_s3_response(b"fake-image-bytes")
    fake_runtime = MagicMock()
    fake_runtime.invoke_endpoint.return_value = _fake_runtime_response(
        {"class": 1, "class_name": "bad_quality", "confidence": 0.92}
    )
    monkeypatch.setattr(handler, "s3", fake_s3)
    monkeypatch.setattr(handler, "runtime", fake_runtime)

    pred = handler.predict_one("s3://bucket/key.jpg")

    assert pred["image_s3_uri"] == "s3://bucket/key.jpg"
    assert pred["predicted_class"] == "bad_quality"
    assert pred["confidence"] == 0.92
    fake_s3.get_object.assert_called_once_with(Bucket="bucket", Key="key.jpg")
    args = fake_runtime.invoke_endpoint.call_args.kwargs
    assert args["EndpointName"] == "test-endpoint"
    assert args["ContentType"] == "application/x-image"
    assert args["Body"] == b"fake-image-bytes"


def test_predict_one_con_lista_de_probs_usa_argmax(monkeypatch):
    fake_s3 = MagicMock()
    fake_s3.get_object.return_value = _fake_s3_response(b"img")
    fake_runtime = MagicMock()
    # probs: indice 0 (good) gana
    fake_runtime.invoke_endpoint.return_value = _fake_runtime_response([0.8, 0.2])
    monkeypatch.setattr(handler, "s3", fake_s3)
    monkeypatch.setattr(handler, "runtime", fake_runtime)

    pred = handler.predict_one("s3://b/k.jpg")

    assert pred["predicted_class"] == "good_quality"
    assert pred["confidence"] == 0.8


def test_lambda_handler_devuelve_predicciones_en_orden(monkeypatch):
    fake_s3 = MagicMock()
    fake_s3.get_object.return_value = _fake_s3_response(b"img")
    fake_runtime = MagicMock()
    fake_runtime.invoke_endpoint.side_effect = [
        _fake_runtime_response({"class": 0, "confidence": 0.9}),
        _fake_runtime_response({"class": 1, "confidence": 0.7}),
        _fake_runtime_response({"class": 0, "confidence": 0.95}),
    ]
    monkeypatch.setattr(handler, "s3", fake_s3)
    monkeypatch.setattr(handler, "runtime", fake_runtime)

    event = {
        "lote_id": "lote-abc",
        "images": [
            "s3://b/img1.jpg",
            "s3://b/img2.jpg",
            "s3://b/img3.jpg",
        ],
    }
    result = handler.lambda_handler(event, context=None)

    assert result["lote_id"] == "lote-abc"
    assert len(result["predictions"]) == 3
    clases = [p["predicted_class"] for p in result["predictions"]]
    assert clases == ["good_quality", "bad_quality", "good_quality"]
    assert fake_runtime.invoke_endpoint.call_count == 3


def test_lambda_handler_sin_images_devuelve_predicciones_vacias(monkeypatch):
    fake_s3 = MagicMock()
    fake_runtime = MagicMock()
    monkeypatch.setattr(handler, "s3", fake_s3)
    monkeypatch.setattr(handler, "runtime", fake_runtime)

    result = handler.lambda_handler({"lote_id": "vacio"}, context=None)

    assert result == {"lote_id": "vacio", "predictions": []}
    fake_s3.get_object.assert_not_called()
    fake_runtime.invoke_endpoint.assert_not_called()
