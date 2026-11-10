"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws

vpc = aws.ec2.Vpc(
  "learning-vpc",
  cidr_block="10.0.0.0/16",  # VPC IP address range
  enable_dns_support=True,  # Enables dns resolution
  enable_dns_hostnames=True,  # Enables dns hostnames for instances with public IPs
  tags={                      # Identifies 
    "Name":"learning-vpc",
    "Environment":"learning"
  }
)

public_subnet = aws.ec2.Subnet(
  "public-subnet",
  vpc_id=vpc.id,
  cidr_block="10.0.1.0/24",
  map_public_ip_on_launch=True,
  tags={
    "Name": "learning-public-subnet",
    "Tier": "public"
  }
)

internet_gateway = aws.ec2.InternetGateway(
    "learning-igw",
    vpc_id=vpc.id,
    tags={
      "Name":"learning-igw",
    }
)

public_route_table = aws.ec2.RouteTable(
   "public-route-table",
    vpc_id=vpc.id,
    routes=[
      {
        "cidr_block": "0.0.0.0/0",
        "gateway_id": internet_gateway.id
      }
    ],
    tags={
        "Name": "learning-public-route-table"
    }
)

route_table_association = aws.ec2.RouteTableAssociation(
    "public-subnet-association",
    subnet_id=public_subnet.id,
    route_table_id=public_route_table.id
)

# Create an AWS resource (S3 Bucket)
# bucket = aws.s3.Bucket('my-vpc-bucket')

# Export the name of the bucket
#pulumi.export('vpc_bucket', bucket.id)
pulumi.export("vpc_id", vpc.id)
pulumi.export("public_subnet_id", public_subnet.id)
pulumi.export("internet_gateway_id", internet_gateway.id)
pulumi.export("public_route_table", public_route_table.id)
