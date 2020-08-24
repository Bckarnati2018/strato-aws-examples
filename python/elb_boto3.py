import boto3
import botocore
import sys
import random


def main():
    # CHeck with Roei

    # Replace following parameters with your IP and credentials
    CLUSTER_IP = '10.16.146.15'
    AWS_ACCESS = '5456a41265ba4b04bf28f9a550e8b98a'
    AWS_SECRET = 'a63277bc152946a49186cf675df2c3ac'

    # Example parameters
    VPC_CIDR = '172.20.0.0/16'
    SUBNET_CIDR = '172.20.10.0/24'
    PORT_INTERNAL = 9090
    PORT_EXTERNAL = 80
    TARGETS_COUNT = 2
    IMAGE_ID = '<Targets Image ID>'
    INSTANCE_TYPE = '<Targets Instance Type>'

    """
    This script shows and example of Boto3 ELB v2 integration with Stratoscale Symphony.

    The scenario:
         1. Create VPC
         2. Create Internet-Gateway
         3. Attach Internet-Gateway
         4. Create Subnet
         5. Create Route-Table
         6. Create Route
         7. Associate Route-Table to Subnet
         8. Create Targets Security-Group
         9. Run target instances
         10. List load-balancers
         11. Create Load-Balancer Security-Groups
         12. Create load-balancer
         13. Create target-group
         14. Register instances to target-group
         15. Create Listener
    
    This example was tested on versions:
    - botocore 1.7.35
    - boto3 1.4.7
    """

    # The following will be used to differentiate entity names in this example
    run_index = '%03x' % random.randrange(2**12)

    print ("Disabling warning for Insecure connection")
    botocore.vendored.requests.packages.urllib3.disable_warnings(
        botocore.vendored.requests.packages.urllib3.exceptions.InsecureRequestWarning)

    # creating a EC2 client connection to Symphony AWS Compatible region
    ec2_client = boto3.client(service_name="ec2", region_name="symphony",
                              endpoint_url="https://%s/api/v2/ec2/" % CLUSTER_IP,
                              verify=False,
                              aws_access_key_id = AWS_ACCESS,
                              aws_secret_access_key=AWS_SECRET)

    # creating a ELB client connection to Symphony AWS Compatible region
    elb_client = boto3.client(service_name="elbv2", region_name="symphony",
                              endpoint_url="https://%s/api/v2/aws/elb" % CLUSTER_IP,
                              verify=False,
                              aws_access_key_id = AWS_ACCESS,
                              aws_secret_access_key=AWS_SECRET)

    # Create VPC
    create_vpc_response = ec2_client.create_vpc(CidrBlock=VPC_CIDR)

    # check create vpc returned successfully
    if create_vpc_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        vpcId = create_vpc_response['Vpc']['VpcId']
        print("Created VPC with ID %s" % vpcId)
    else:
        print("Create VPC failed")

    #Create Internet Gateway
    create_igw_response = ec2_client.create_internet_gateway()

    # check create internet-gateway returned successfully
    if create_igw_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        igwId = create_igw_response['InternetGateway']['InternetGatewayId']
        print("Created InternetGateway with ID %s" % igwId)
    else:
        print("Create InternetGateway failed")

    #Attach Internet Gateway to VPC
    attach_igw_response = ec2_client.attach_internet_gateway(InternetGatewayId=igwId,
                                                             VpcId=vpcId)

    # check attach internet-gateway returned successfully
    if attach_igw_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print("Attached InternetGateway with ID %s to VPC %s" % (igwId, vpcId))
    else:
        print("Create InternetGateway failed")

    #Create Subnet
    create_subnet_response = ec2_client.create_subnet(CidrBlock=SUBNET_CIDR, VpcId=vpcId)

    # check create subnet returned successfully
    if create_subnet_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        subnetId = create_subnet_response['Subnet']['SubnetId']
        print("Created Subnet with ID %s" % subnetId)
    else:
        print("Create Subnet failed")

    #Create route table in the VPC
    create_rtb_response = ec2_client.create_route_table(VpcId=vpcId)

    # check create route-tables returned successfully
    if create_rtb_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        rtbId = create_rtb_response['RouteTable']['RouteTableId']
        print("Created Route Table ID %s in VPC %s" % (rtbId, vpcId))
    else:
        print("Create route-tables failed")

    #Add routing rule to route table
    create_route_response = ec2_client.create_route(DestinationCidrBlock='0.0.0.0/0',
                                                    GatewayId=igwId,
                                                    RouteTableId=rtbId)

    # check create route returned successfully
    if create_route_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print("Created routing rule VPC with ID %s" % vpcId)
    else:
        print("Create routing rule failed")

    #Associate route table to subnet
    associate_rtb_response = ec2_client.associate_route_table(RouteTableId=rtbId,
                                                              SubnetId=subnetId)

    # check create route returned successfully
    if associate_rtb_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print("Associated route table %s to subnet %s" % (rtbId, subnetId))
    else:
        print("Associated route table failed")

    #Create Security-Group
    create_sg_response = ec2_client.create_security_group(GroupName='my_ELB_SG_%s' % run_index,
                                                          Description='Allow traffic for ELB',
                                                          VpcId=vpcId)

    # check create security-group returned successfully
    if create_sg_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        sgId = create_sg_response['GroupId']
        print("Created security-group with ID %s" % sgId)
    else:
        print("Create security-group failed")

    #Allow Security-Group Rules - ICMP and TCP
    allow_ingress_response = ec2_client.authorize_security_group_ingress(GroupId=sgId,
                                                                         IpPermissions=[
                                                                             {"IpProtocol": "icmp", "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
                                                                             {"IpProtocol": "tcp", "FromPort": PORT_INTERNAL, "ToPort": PORT_INTERNAL, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}
                                                                         ])

    # check allow ingress traffic returned successfully
    if allow_ingress_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print("Allow security group ingress for ICMP and TCP")
    else:
        print("Allow security group ingress failed")

    #Run instances
    print ("Starting to run target instances")
    run_instances_response = ec2_client.run_instances(ImageId=IMAGE_ID, InstanceType=INSTANCE_TYPE,
                                                      MaxCount=TARGETS_COUNT, MinCount=TARGETS_COUNT,
                                                      SecurityGroupIds=[sgId], SubnetId=subnetId)

    # check run instances returned successfully
    if run_instances_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        targetIds = [instance['InstanceId'] for instance in run_instances_response['Instances']]
        print ("Created instances: " + ' '.join(p for p in targetIds))
    else:
        print("Create instances failed")

    def my_list_lbs():
        # list lbs
        lbs_list_response = elb_client.describe_load_balancers()

        # check lbs list returned successfully
        if lbs_list_response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print ("LBs list: " + ' '.join(p for p in [lb['LoadBalancerName']
                                           for lb in lbs_list_response['LoadBalancers']]))
        else:
            print ("List lbs failed")

    my_list_lbs()

    # Create Security-group for Load Balancer
    create_lb_sg_response = ec2_client.create_security_group(GroupName='internet-load-balancer_%s' % run_index,
                                                             Description='Security Group for Internet-facing LB',
                                                             VpcId=vpcId)

    # check create security-group returned successfully
    if create_lb_sg_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        lbSgId = create_lb_sg_response['GroupId']
        print("Created LB security-group with ID %s" % lbSgId)
    else:
        print("Create LB security-group failed")

    # Allow Security-Group Ingress Rules
    # TCP - external port from all sources
    # ICMP - all
    allow_ingress_response = ec2_client.authorize_security_group_ingress(GroupId=lbSgId,
                                                                         IpPermissions=[
                                                                             {"IpProtocol": "icmp", "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
                                                                             {"IpProtocol": "tcp", "FromPort": PORT_EXTERNAL,
                                                                              "ToPort": PORT_EXTERNAL, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}
                                                                         ])

    # check allow ingress traffic returned successfully
    if allow_ingress_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print("Allow security group ingress for ICMP and TCP")
    else:
        print("Allow security group ingress failed")

    # Allow Security-Group Egress Rules
    # TCP - internal port to targets group
    allow_egress_response = ec2_client.authorize_security_group_egress(GroupId=lbSgId,
                                                                       IpPermissions=[
                                                                           {"IpProtocol": "tcp",
                                                                            "FromPort": PORT_INTERNAL,
                                                                            "ToPort": PORT_INTERNAL,
                                                                            "UserIdGroupPairs": [{'GroupId': sgId}]}
                                                                       ])

    # check allow egress traffic returned successfully
    if allow_egress_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print("Allow security group egress for ICMP and TCP")
    else:
        print("Allow security group egress failed")

    # create load-balancer
    create_lb_response = elb_client.create_load_balancer(Name='my_lb_%s' % run_index,
                                                         Subnets=[subnetId],
                                                         SecurityGroups=[lbSgId],
                                                         Scheme='internet-facing')

    # check create lb returned successfully
    if create_lb_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        lbId = create_lb_response['LoadBalancers'][0]['LoadBalancerArn']
        print "Successfully created load balancer %s" % lbId
    else:
        print ("Create load balancer failed")

    my_list_lbs()

    # create target-group
    create_tg_response = elb_client.create_target_group(Name='my_lb_tg_%s' % run_index,
                                                        Protocol='TCP',
                                                        Port=PORT_INTERNAL,
                                                        VpcId=vpcId)

    # check create target-group returned successfully
    if create_tg_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        tgId = create_tg_response['TargetGroups'][0]['TargetGroupArn']
        print "Successfully created target group %s" % tgId
    else:
        print ("Create target group failed")

    # Register targets
    targets_list = [dict(Id=target_id, Port=PORT_INTERNAL) for target_id in targetIds]
    reg_targets_response = elb_client.register_targets(TargetGroupArn=tgId, Targets=targets_list)

    # check register group returned successfully
    if reg_targets_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print "Successfully registered targets"
    else:
        print ("Register targets failed")

    # create Listener
    create_listener_response = elb_client.create_listener(LoadBalancerArn=lbId,
                                                          Protocol='TCP', Port=PORT_EXTERNAL,
                                                          DefaultActions=[{'Type': 'forward',
                                                                           'TargetGroupArn': tgId}])

    # check create listener returned successfully
    if create_listener_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print "Successfully created listener %s" % tgId
    else:
        print ("Create listener failed")

if __name__ == '__main__':
    sys.exit(main())
