terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

data "aws_ami" "ubuntu" {
  most_recent = true

  owners = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

locals {
  instances = flatten([
    for srv in var.configuration : [
      for i in range(srv.no_of_instances) : {
        instance_name   = "${srv.application_name}-${i + 1}"
        instance_type   = srv.instance_type
        subnet_id       = srv.subnet_id
        security_groups = srv.vpc_security_group_ids
      }
    ]
  ])
}

resource "aws_instance" "ec2" {

  for_each = {
    for instance in local.instances :
    instance.instance_name => instance
  }

  ami                    = data.aws_ami.ubuntu.id
  instance_type          = each.value.instance_type
  subnet_id              = each.value.subnet_id
  vpc_security_group_ids = each.value.security_groups
  key_name = "test01"

  tags = {
    Name = each.value.instance_name
  }
}
