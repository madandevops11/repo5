configuration = [

  {
    application_name       = "webserver"
    instance_type          = "t2.micro"
    no_of_instances        = 2
    subnet_id              = "subnet-0985e63b150f91073"
    vpc_security_group_ids = ["sg-055cadb052dde1533"]
  },

  {
    application_name       = "appserver"
    instance_type          = "t2.small"
    no_of_instances        = 1
    subnet_id              = "subnet-0985e63b150f91073"
    vpc_security_group_ids = ["sg-055cadb052dde1533"]
  }

]
