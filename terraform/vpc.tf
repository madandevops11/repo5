provider "aws" {
  region  = "us-east-1"
}
# Terraform Training VPC
resource "aws_vpc" "terraformtraining" {
  cidr_block            = "10.0.0.0/16"
  instance_tenancy      = "default"
  enable_dns_support   = "true"
  enable_dns_hostnames = "true"
  tags = {
        Name = "terraformtraining"
  }
}

# Terraform Training Subnets
resource "aws_subnet" "terraformtraining-public-1" {
  vpc_id                = aws_vpc.terraformtraining.id
  cidr_block            = "10.0.1.0/24"
  map_public_ip_on_launch = "true"
  availability_zone     = "us-east-1a"

  tags = {
        Name = "terraformtraining-public-1"
  }
}

resource "aws_subnet" "terraformtraining-public-2" {
  vpc_id                = aws_vpc.terraformtraining.id
  cidr_block            = "10.0.2.0/24"
  map_public_ip_on_launch = "true"
  availability_zone     = "us-east-1b"

  tags = {
        Name = "terraformtraining-public-2"
  }
}

resource "aws_subnet" "terraformtraining-private-1" {
  vpc_id                = aws_vpc.terraformtraining.id
  cidr_block            = "10.0.3.0/24"
  map_public_ip_on_launch = "false"
  availability_zone     = "us-east-1a"

  tags = {
        Name = "terraformtraining-private-1"
  }
}

resource "aws_subnet" "terraformtraining-private-2" {
  vpc_id                = aws_vpc.terraformtraining.id
  cidr_block            = "10.0.4.0/24"
  map_public_ip_on_launch = "false"
  availability_zone     = "us-east-1b"

  tags = {
        Name = "terraformtraining-private-2"
  }
}

# Terraform Training GW
resource "aws_internet_gateway" "terraformtraining-gw" {
  vpc_id = aws_vpc.terraformtraining.id

  tags = {
        Name = "terraformtraining-gw"
  }
}

# Terraform Training RT
resource "aws_route_table" "terraformtraining-public" {
  vpc_id = aws_vpc.terraformtraining.id
  route {
        cidr_block = "0.0.0.0/0"
        gateway_id = aws_internet_gateway.terraformtraining-gw.id
  }

  tags = {
        Name = "terraformtraining-public-1"
  }
}

# Terraform Training RTA
resource "aws_route_table_association" "terraformtraining-public-1-a" {
  subnet_id     = aws_subnet.terraformtraining-public-1.id
  route_table_id = aws_route_table.terraformtraining-public.id
}

resource "aws_route_table_association" "terraformtraining-public-2-a" {
  subnet_id     = aws_subnet.terraformtraining-public-2.id
  route_table_id = aws_route_table.terraformtraining-public.id
}

# TF-UPGRADE-TODO: Block type was not recognized, so this block and its contents were not automatically upgraded.
# Terraform Training NG
#NAT Gateway configuration

resource "aws_eip" "terraformtraining-nat" {
  domain ="vpc"
}

resource "aws_nat_gateway" "terraformtraining-nat-gw" {
  allocation_id = aws_eip.terraformtraining-nat.id
  subnet_id     = aws_subnet.terraformtraining-public-1.id
  depends_on    = [aws_internet_gateway.terraformtraining-gw]
}

# Terraform Training VPC for NAT
resource "aws_route_table" "terraformtraining-private" {
  vpc_id = aws_vpc.terraformtraining.id
  route {
        cidr_block      = "0.0.0.0/0"
        nat_gateway_id = aws_nat_gateway.terraformtraining-nat-gw.id
  }

  tags = {
        Name = "terraformtraining-private-1"
  }
}

# Terraform Training private routes
resource "aws_route_table_association" "terraformtraining-private-1-a" {
  subnet_id     = aws_subnet.terraformtraining-private-1.id
  route_table_id = aws_route_table.terraformtraining-private.id
}

resource "aws_route_table_association" "terraformtraining-private-2-a" {
  subnet_id     = aws_subnet.terraformtraining-private-2.id
  route_table_id = aws_route_table.terraformtraining-private.id
}
