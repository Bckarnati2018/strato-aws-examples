# Sample tfvars file 
# Stratoscale Symphony credentials

symphony_ip = "10.16.145.132"
access_key = "f3f9d244941a4ce68d7b6d5033301f62"
secret_key = "5d8d17948b554129b1d86f1eadef7ca5"

# Number of web servers (Load balancer will automatically manage target groups)
web_number = "2"

# Use Public Xenial cloud image ami
# Recommend use of Xenial's latest cloud image
# located here: https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-disk1.img
web_ami = "ami-de1c420e825b4a998e2ce913362f4e77"
web_instance_type = "t2.medium"
public_keypair_path = "<path to public key pair>"

#Database Information (wordpress containe will use wordpress database by default)

db_user = "admin"
db_password = "Stratoscale!Orchestration!"




