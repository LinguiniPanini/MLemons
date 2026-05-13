"""Tests del scoring puro. No requiere AWS."""
import sys
import os

# El Lambda apila el scoring_logic.py en el directorio raiz del zip;
# para correr en local desde la raiz del repo, agregar el path manualmente.
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "src", "lambda_code", "compute_score")
)

from scoring_logic import score_lote, CLASS_WEIGHTS


def test_lote_todo_sano_da_score_100_aprobado():
    preds = [{"predicted_class": "good_quality"} for _ in range(5)]
    r = score_lote(preds)
    assert r["score"] == 100.0
    assert r["decision"] == "APROBADO"
    assert r["distribucion"] == {"good_quality": 5}
    assert r["n_images"] == 5


def test_lote_todo_defectuoso_da_score_0_rechazado():
    preds = [{"predicted_class": "bad_quality"} for _ in range(3)]
    r = score_lote(preds)
    assert r["score"] == 0.0
    assert r["decision"] == "RECHAZADO"


def test_mitad_y_mitad_da_score_50_rechazado_con_default():
    # default threshold = 75, asi que 50 RECHAZADO
    preds = [{"predicted_class": "good_quality"}] * 4 + [{"predicted_class": "bad_quality"}] * 4
    r = score_lote(preds)
    assert r["score"] == 50.0
    assert r["decision"] == "RECHAZADO"


def test_threshold_custom_baja_aprueba():
    preds = [{"predicted_class": "good_quality"}] * 4 + [{"predicted_class": "bad_quality"}] * 4
    r = score_lote(preds, threshold=40.0)
    assert r["decision"] == "APROBADO"


def test_clases_desconocidas_se_ignoran():
    preds = [
        {"predicted_class": "good_quality"},
        {"predicted_class": "empty_background"},  # se ignora
        {"predicted_class": "good_quality"},
    ]
    r = score_lote(preds)
    assert r["n_images"] == 2  # solo las 2 conocidas
    assert r["score"] == 100.0
    assert r["distribucion"] == {"good_quality": 2}


def test_lote_vacio_rechaza_sin_dividir_por_cero():
    r = score_lote([])
    assert r["score"] == 0.0
    assert r["decision"] == "RECHAZADO"
    assert r["n_images"] == 0


def test_lote_solo_background_rechaza():
    preds = [{"predicted_class": "empty_background"} for _ in range(3)]
    r = score_lote(preds)
    assert r["n_images"] == 0
    assert r["decision"] == "RECHAZADO"


def test_threshold_borde_aprueba_exacto():
    # 7 good, 1 bad: score = 7/8 * 100 = 87.5
    preds = [{"predicted_class": "good_quality"}] * 7 + [{"predicted_class": "bad_quality"}]
    r = score_lote(preds, threshold=87.5)
    assert r["score"] == 87.5
    assert r["decision"] == "APROBADO"


def test_pesos_de_clase_son_los_esperados():
    # invariante de diseno: D6 fija good=100, bad=0
    assert CLASS_WEIGHTS["good_quality"] == 100
    assert CLASS_WEIGHTS["bad_quality"] == 0
