output "instance_public_ips" {
  value = {
    for k, v in aws_instance.ec2 :
    k => v.public_ip
  }
}

output "instance_private_ips" {
  value = {
    for k, v in aws_instance.ec2 :
    k => v.private_ip
  }
}
