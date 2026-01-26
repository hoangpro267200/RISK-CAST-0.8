output "bucket_names" {
  description = "All bucket names"
  value = {
    logs    = aws_s3_bucket.logs.id
    data    = aws_s3_bucket.data.id
    backups = aws_s3_bucket.backups.id
  }
}

output "logs_bucket" {
  description = "Logs bucket name"
  value       = aws_s3_bucket.logs.id
}

output "data_bucket" {
  description = "Data bucket name"
  value       = aws_s3_bucket.data.id
}

output "backups_bucket" {
  description = "Backups bucket name"
  value       = aws_s3_bucket.backups.id
}
