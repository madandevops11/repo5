######## Create a file called ec2.tf with below contents ################

provider "aws" {
  region  = "us-east-1"
}

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] # Canonical
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  key_name      = "madankeypair01"

  tags = {
    Name = "HelloWorld"
  }
  subnet_id                     = "subnet-0674482a49f964aad"
  associate_public_ip_address = "true"
  vpc_security_group_ids        = ["sg-04660a97e8e5f1d47"]
  root_block_device {
        volume_size = 8
        volume_type = "gp2"

}
}







+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


commands:

# terraform init
# terraform plan
# terraform apply   ---> yes
