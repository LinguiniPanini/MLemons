# cloudwatch.tf
#
# Alarmas basicas para detectar problemas en el pipeline.
# Se podrian conectar a SNS para email, pero aqui solo dejamos las metricas.

resource "aws_cloudwatch_metric_alarm" "lambda_invoke_errors" {
  alarm_name          = "${local.project}-invoke-modelo-a-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Lambda invoke_modelo_a registro errores"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.invoke_modelo_a.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_compute_score_errors" {
  alarm_name          = "${local.project}-compute-score-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Lambda compute_score registro errores"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.compute_score.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "sfn_execution_failures" {
  alarm_name          = "${local.project}-sfn-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ExecutionsFailed"
  namespace           = "AWS/States"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Step Functions execution fallo"
  treat_missing_data  = "notBreaching"

  dimensions = {
    StateMachineArn = aws_sfn_state_machine.pipeline.arn
  }
}
