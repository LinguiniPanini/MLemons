# sagemaker.tf
#
# Endpoint para inferencia del Modelo A.
#
# Pre-requisito: el Model Package debe estar registrado y aprobado en el
# Model Package Group "mlemons-modelo-a-group" (lo hace notebook 03).
#
# La variable model_package_arn se pasa con -var o terraform.tfvars; no se
# crea hasta que el training termine.

variable "model_package_arn" {
  description = "ARN del Model Package aprobado (output del notebook 03)"
  type        = string
  default     = ""
}

# Solo crear el endpoint cuando el ARN este definido
locals {
  endpoint_enabled = var.model_package_arn != ""
}

resource "aws_sagemaker_model" "modelo_a" {
  count              = local.endpoint_enabled ? 1 : 0
  name               = "${local.project}-modelo-a"
  execution_role_arn = aws_iam_role.sagemaker_role.arn

  primary_container {
    model_package_name = var.model_package_arn
  }
}

resource "aws_sagemaker_endpoint_configuration" "modelo_a" {
  count = local.endpoint_enabled ? 1 : 0
  name  = "${local.project}-modelo-a-config"

  production_variants {
    variant_name           = "AllTraffic"
    model_name             = aws_sagemaker_model.modelo_a[0].name
    initial_instance_count = 1
    instance_type          = "ml.t2.medium"
    initial_variant_weight = 1
  }
}

resource "aws_sagemaker_endpoint" "modelo_a" {
  count                = local.endpoint_enabled ? 1 : 0
  name                 = "${local.project}-modelo-a-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.modelo_a[0].name
}

output "endpoint_name" {
  value = local.endpoint_enabled ? aws_sagemaker_endpoint.modelo_a[0].name : "no-endpoint"
}
