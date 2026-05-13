# lambda.tf
#
# Pattern slide 03: data.archive_file + aws_lambda_function. source_code_hash
# usa output_base64sha256 para que Terraform detecte cambios en el codigo.

# -----------------------------
# invoke_modelo_a
# -----------------------------

data "archive_file" "invoke_modelo_a" {
  type        = "zip"
  source_dir  = "${path.module}/../src/lambda_code/invoke_modelo_a"
  output_path = "${path.module}/build/invoke_modelo_a.zip"
}

resource "aws_lambda_function" "invoke_modelo_a" {
  function_name    = "${local.project}-invoke-modelo-a"
  role             = aws_iam_role.lambda_role.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 60
  memory_size      = 512
  filename         = data.archive_file.invoke_modelo_a.output_path
  source_code_hash = data.archive_file.invoke_modelo_a.output_base64sha256

  environment {
    variables = {
      ENDPOINT_NAME = "${local.project}-modelo-a-endpoint"
    }
  }
}

# -----------------------------
# compute_score
# -----------------------------

data "archive_file" "compute_score" {
  type        = "zip"
  source_dir  = "${path.module}/../src/lambda_code/compute_score"
  output_path = "${path.module}/build/compute_score.zip"
}

resource "aws_lambda_function" "compute_score" {
  function_name    = "${local.project}-compute-score"
  role             = aws_iam_role.lambda_role.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 256
  filename         = data.archive_file.compute_score.output_path
  source_code_hash = data.archive_file.compute_score.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.lotes.name
    }
  }
}

output "lambda_invoke_modelo_a_arn" {
  value = aws_lambda_function.invoke_modelo_a.arn
}

output "lambda_compute_score_arn" {
  value = aws_lambda_function.compute_score.arn
}
