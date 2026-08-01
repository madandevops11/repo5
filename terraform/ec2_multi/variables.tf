variable "configuration" {
  description = "EC2 configuration"

  type = list(object({
    application_name       = string
    instance_type          = string
    no_of_instances        = number
    subnet_id              = string
    vpc_security_group_ids = list(string)
  }))
}
