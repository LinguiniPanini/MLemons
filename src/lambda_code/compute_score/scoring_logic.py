"""Logica pura de scoring de lotes. Sin dependencias AWS para poder testear."""

# Pesos por clase. Decision D6: clasificacion binaria.
CLASS_WEIGHTS = {
    "good_quality": 100,
    "bad_quality": 0,
}

DEFAULT_THRESHOLD = 75.0


def score_lote(predictions, threshold=DEFAULT_THRESHOLD):
    """Calcula el score de un lote dado una lista de predicciones.

    Args:
        predictions: list of dicts con al menos {"predicted_class": str}.
            Se ignoran predicciones de clases no conocidas (e.g. "empty_background").
        threshold: umbral para decidir APROBADO vs RECHAZADO.

    Returns:
        dict con score, decision, distribucion, n_images.
    """
    distribucion = {}
    score_acumulado = 0.0
    n_clasificados = 0

    for p in predictions:
        clase = p.get("predicted_class")
        if clase not in CLASS_WEIGHTS:
            # ignora clases fuera del scoring (e.g. background)
            continue
        distribucion[clase] = distribucion.get(clase, 0) + 1
        score_acumulado += CLASS_WEIGHTS[clase]
        n_clasificados += 1

    if n_clasificados == 0:
        # lote vacio o todas las imagenes fueron descartadas
        return {
            "score": 0.0,
            "decision": "RECHAZADO",
            "distribucion": distribucion,
            "n_images": 0,
        }

    score = score_acumulado / n_clasificados
    decision = "APROBADO" if score >= threshold else "RECHAZADO"

    return {
        "score": round(score, 2),
        "decision": decision,
        "distribucion": distribucion,
        "n_images": n_clasificados,
    }
