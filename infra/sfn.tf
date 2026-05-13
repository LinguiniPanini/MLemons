# sfn.tf
#
# Step Functions state machine: pipeline simple de inferencia.
#   1. InvokeModeloA  -> Lambda que llama al endpoint y produce predicciones
#   2. ComputeScore   -> Lambda que calcula score y persiste en DynamoDB

resource "aws_sfn_state_machine" "pipeline" {
  name     = "${local.project}-pipeline"
  role_arn = aws_iam_role.step_functions_role.arn

  definition = jsonencode({
    Comment = "MLemons inference pipeline simple (Modelo A)"
    StartAt = "InvokeModeloA"
    States = {
      InvokeModeloA = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.invoke_modelo_a.arn
          "Payload.$"  = "$"
        }
        OutputPath = "$.Payload"
        Retry = [{
          ErrorEquals     = ["States.ALL"]
          IntervalSeconds = 2
          MaxAttempts     = 2
          BackoffRate     = 2.0
        }]
        Next = "ComputeScore"
      }
      ComputeScore = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.compute_score.arn
          "Payload.$"  = "$"
        }
        OutputPath = "$.Payload"
        End        = true
      }
    }
  })
}

output "state_machine_arn" {
  value = aws_sfn_state_machine.pipeline.arn
}
