# dynamodb.tf

resource "aws_dynamodb_table" "lotes" {
  name         = "mlemons_lotes"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "lote_id"

  attribute {
    name = "lote_id"
    type = "S"
  }
}

output "dynamodb_lotes_arn" {
  value = aws_dynamodb_table.lotes.arn
}
