# Makefile — MLemons
# Recipes para desarrollo, testing y despliegue.

.PHONY: help install lint format test clean apply destroy endpoint-up endpoint-down

help:
	@echo "Recipes disponibles:"
	@echo "  make install       Instalar dependencias Python"
	@echo "  make lint          Correr pylint + black --check"
	@echo "  make format        Formatear con black"
	@echo "  make test          Correr pytest con coverage"
	@echo "  make apply         terraform apply (toda la infra)"
	@echo "  make destroy       terraform destroy (toda la infra)"
	@echo "  make endpoint-up   Crear endpoint SageMaker Modelo B"
	@echo "  make endpoint-down Apagar endpoint SageMaker Modelo B"
	@echo "  make clean         Limpiar artefactos (__pycache__, .pytest_cache)"

install:
	pip install -r requirements.txt

lint:
	pylint src/ tests/
	black --check src/ tests/

format:
	black src/ tests/

test:
	pytest tests/ --cov=src --cov-report=term-missing

apply:
	cd infra && terraform init && terraform apply

destroy:
	cd infra && terraform destroy

endpoint-up:
	aws sagemaker create-endpoint --endpoint-name mlemons-modelo-b-endpoint --endpoint-config-name mlemons-modelo-b-config

endpoint-down:
	aws sagemaker delete-endpoint --endpoint-name mlemons-modelo-b-endpoint || true
	aws sagemaker delete-endpoint-config --endpoint-config-name mlemons-modelo-b-config || true

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov
