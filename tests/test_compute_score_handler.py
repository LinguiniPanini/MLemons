"""Tests del handler compute_score. Mockea DynamoDB."""
import importlib.util
import json
import os
import sys
from unittest.mock import MagicMock

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-2")
os.environ.setdefault("DYNAMODB_TABLE", "test-mlemons-lotes")

# El handler hace from scoring_logic import ..., asi que necesitamos su dir en sys.path.
_COMPUTE_SCORE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "src", "lambda_code", "compute_score"
)
sys.path.insert(0, _COMPUTE_SCORE_DIR)

# Los dos handlers de Lambda se llaman handler.py. Los cargamos por path bajo
# un nombre unico para que no colisionen en sys.modules.
_HANDLER_PATH = os.path.join(_COMPUTE_SCORE_DIR, "handler.py")
_spec = importlib.util.spec_from_file_location("compute_score_handler", _HANDLER_PATH)
handler = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(handler)


def _mock_table(monkeypatch):
    fake_table = MagicMock()
    fake_dynamodb = MagicMock()
    fake_dynamodb.Table.return_value = fake_table
    monkeypatch.setattr(handler, "dynamodb", fake_dynamodb)
    return fake_dynamodb, fake_table


def test_handler_persiste_item_con_score_correcto(monkeypatch):
    _, fake_table = _mock_table(monkeypatch)

    event = {
        "lote_id": "lote-test-1",
        "predictions": [
            {"predicted_class": "good_quality"},
            {"predicted_class": "bad_quality"},
        ],
        "threshold": 75,
    }
    resp = handler.lambda_handler(event, context=None)

    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["lote_id"] == "lote-test-1"
    assert body["score"] == 50.0
    assert body["decision"] == "RECHAZADO"
    assert body["n_images"] == 2

    fake_table.put_item.assert_called_once()
    item = fake_table.put_item.call_args.kwargs["Item"]
    assert item["lote_id"] == "lote-test-1"
    assert item["score"] == "50.0"  # como string por restriccion DynamoDB con floats
    assert item["threshold"] == "75.0"
    assert item["decision"] == "RECHAZADO"
    assert item["n_images"] == 2
    assert item["distribucion"] == {"good_quality": 1, "bad_quality": 1}
    assert isinstance(item["timestamp"], int)


def test_handler_genera_lote_id_si_falta(monkeypatch):
    _, fake_table = _mock_table(monkeypatch)
    monkeypatch.setattr(handler.uuid, "uuid4", lambda: "11111111-2222-3333-4444-555555555555")

    event = {"predictions": [{"predicted_class": "good_quality"}]}
    resp = handler.lambda_handler(event, context=None)

    body = json.loads(resp["body"])
    assert body["lote_id"] == "11111111-2222-3333-4444-555555555555"
    item = fake_table.put_item.call_args.kwargs["Item"]
    assert item["lote_id"] == "11111111-2222-3333-4444-555555555555"


def test_handler_respeta_threshold_del_evento(monkeypatch):
    _, fake_table = _mock_table(monkeypatch)

    # 3 good + 1 bad -> score = 75. Con threshold 80 RECHAZADO.
    event = {
        "lote_id": "lote-thr",
        "predictions": [{"predicted_class": "good_quality"}] * 3
        + [{"predicted_class": "bad_quality"}],
        "threshold": 80,
    }
    resp = handler.lambda_handler(event, context=None)
    body = json.loads(resp["body"])
    assert body["score"] == 75.0
    assert body["decision"] == "RECHAZADO"

    item = fake_table.put_item.call_args.kwargs["Item"]
    assert item["threshold"] == "80.0"


def test_handler_threshold_default_75_si_falta(monkeypatch):
    _, fake_table = _mock_table(monkeypatch)

    # 3 good + 1 bad -> score 75. Default threshold 75 -> APROBADO (>=).
    event = {
        "lote_id": "lote-default",
        "predictions": [{"predicted_class": "good_quality"}] * 3
        + [{"predicted_class": "bad_quality"}],
    }
    resp = handler.lambda_handler(event, context=None)
    body = json.loads(resp["body"])
    assert body["decision"] == "APROBADO"
    item = fake_table.put_item.call_args.kwargs["Item"]
    assert item["threshold"] == "75.0"


def test_handler_lote_vacio_persiste_score_cero_y_rechazado(monkeypatch):
    _, fake_table = _mock_table(monkeypatch)

    event = {"lote_id": "vacio", "predictions": []}
    resp = handler.lambda_handler(event, context=None)
    body = json.loads(resp["body"])
    assert body["score"] == 0.0
    assert body["decision"] == "RECHAZADO"
    assert body["n_images"] == 0
    fake_table.put_item.assert_called_once()
