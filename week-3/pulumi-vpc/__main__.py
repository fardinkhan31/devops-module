"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws
import json
import base64

# IAM role for EC2
ec2_assume_role_policy = json.dumps({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
          "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
})

ec2_role = aws.iam.Role(
  "learning-ec2-role",
  description="IAM role for Pulumi learning EC2 instance",
  assume_role_policy=ec2_assume_role_policy,
  tags={
    "Name": "learning-ec2-role",
    "Environment": "learning"
  }
)

ec2_ssm_policy = aws.iam.RolePolicyAttachment(
  "ec2-ssm-policy-attachment",
  role=ec2_role.name,
  policy_arn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
)

ec2_instance_profile = aws.iam.InstanceProfile(
  "learning-ec2-instance-profile",
  role=ec2_role.name,
  tags={
    "Name": "learning-ec2-instance-profile",
    "Environment": "learning"
  }
)


# ec2 setup
amazon_linux_ami = aws.ec2.get_ami(
  most_recent=True,
  owners=["amazon"],
  filters=[
    {
      "name": "name",
      "values": ["al2023-ami-2023.*-x86_64"]
    },
    {
      "name": "architecture",
      "values": ["x86_64"]
    },
    {
      "name": "root-device-type",
      "values": ["ebs"]
    },
    {
      "name": "virtualization-type",
      "values": ["hvm"]
    }
  ]
)



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


subnet_configs = [
  {
    "name": "public-subnet-b",
    "cidr": "10.0.2.0/24",
    "az": "ap-southeast-2b",
    "tier": "public"
  },
  {
    "name": "private-subnet-a",
    "cidr": "10.0.11.0/24",
    "az": "ap-southeast-2a",
    "tier": "private"
  },
  {
    "name": "private-subnet-b",
    "cidr": "10.0.12.0/24",
    "az": "ap-southeast-2b",
    "tier": "private"
  }
]


created_subnets = {}

for config in subnet_configs:

  subnet = aws.ec2.Subnet(
            config["name"],
            vpc_id=vpc.id,
            cidr_block=config["cidr"],
            availability_zone=config["az"],
            map_public_ip_on_launch=(config["tier"] == "public"),
            tags={
                "Name": config["name"],
                "Tier": config["tier"],
                "Environment": "learning"
            }
  )

  created_subnets[config["name"]] = subnet

public_subnet_b = created_subnets["public-subnet-b"]
private_subnet_a = created_subnets["private-subnet-a"]
private_subnet_b = created_subnets["private-subnet-b"]


nat_eip = aws.ec2.Eip(
    "nat-eip",
    domain="vpc",
    tags={
        "Name": "learning-nat-eip"
    }
)

nat_gateway = aws.ec2.NatGateway(
    "learning-nat-gateway",
    allocation_id=nat_eip.id,
    subnet_id=public_subnet.id,
    tags={
      "Name":"learning-nat-gateway"
    },
    opts=pulumi.ResourceOptions(
        depends_on=[
          internet_gateway,
          route_table_association
        ]
    )
)

private_route_table = aws.ec2.RouteTable(
    "private-route-table",
    vpc_id=vpc.id,
    routes=[
      {
        "cidr_block":"0.0.0.0/0",
        "nat_gateway_id": nat_gateway.id
      }
    ],
    tags={
      "Name": "learning-private-route-table"
    }
)

public_subnet_b_association = aws.ec2.RouteTableAssociation(
    "public-subnet-b-association",
    subnet_id=public_subnet_b.id,
    route_table_id=public_route_table.id
)

private_subnet_a_association = aws.ec2.RouteTableAssociation(
    "private-subnet-a-association",
    subnet_id=private_subnet_a.id,
    route_table_id=private_route_table.id
)

private_subnet_b_association = aws.ec2.RouteTableAssociation(
    "private-subnet-b-association",
    subnet_id=private_subnet_b.id,
    route_table_id=private_route_table.id
)

web_security_group = aws.ec2.SecurityGroup(
    "web-security-group",
    name="learning-web-sg",
    description="Security group for learning web server",
    vpc_id=vpc.id,
    tags={
      "Name": "learning-web-sg",
      "Environment": "learning"
    }
)

http_ingress = aws.vpc.SecurityGroupIngressRule(
    "allow-http",
    security_group_id=web_security_group.id,
    cidr_ipv4="0.0.0.0/0",
    from_port=80,
    to_port=80,
    ip_protocol="tcp",
    description="Allow HTTP traffic"
)

allow_all_egress = aws.vpc.SecurityGroupEgressRule(
    "allow-all-egress",
    security_group_id=web_security_group.id,
    cidr_ipv4="0.0.0.0/0",
    ip_protocol="-1",
    description="Allow all outbound IPv4 traffic"
)


web_server = aws.ec2.Instance(
  "learning-web-server",

  ami=amazon_linux_ami.id,

  instance_type="t3.micro",

  iam_instance_profile=ec2_instance_profile.name,

  subnet_id=public_subnet.id,
  vpc_security_group_ids=[
    web_security_group.id
  ],
  associate_public_ip_address=True,

  metadata_options={
    "http_endpoint": "enabled",
    "http_tokens": "required"
  },

  user_data="""#!/bin/bash

  set -eux

  dnf install -y nginx

  systemctl enable --now nginx

  cat > /usr/share/nginx/html/index.html <<'EOF'
  <h1>Hello from Pulumi!</h1>
  <p>This EC2 instance was deployed using Pulumi and Python.</p>
  EOF

  systemctl enable --now amazon-ssm-agent || true
  """,

  root_block_device={
    "volume_size": 8,
    "volume_type": "gp3",
    "encrypted": True,
    "delete_on_termination": True
  },

  tags={
    "Name": "learning-web-server",
    "Environment": "learning"
  },

  opts=pulumi.ResourceOptions(
    depends_on=[ec2_ssm_policy]
  )
)


# EBS volume data
data_volume = aws.ebs.Volume(
  "learning-data-volume",
  availability_zone=web_server.availability_zone,
  size=5,
  type="gp3",
  encrypted=True,
  tags={
    "Name": "learning-data-volume",
    "Environment": "learning"
  }
)

data_volume_attachment = aws.ec2.VolumeAttachment(
  "learning-data-attachment",
  device_name="/dev/sdf",
  volume_id=data_volume.id,
  instance_id=web_server.id
)

# Create an AWS resource (S3 Bucket)
bucket = aws.s3.Bucket(
  'my-vpc-bucket',
  tags={
      "Name": "learning-assets",
      "Environment": "learning"
  }
)

assets_versioning = aws.s3.BucketVersioning(
  "assets-versioning",
  bucket=bucket.id,
  versioning_configuration={
    "status": "Enabled"
  }
)

assets_encryption = aws.s3.BucketServerSideEncryptionConfiguration(
  "assets-encryption",
  bucket=bucket.id,
  rules=[
      {
        "apply_server_side_encryption_by_default": {
          "sse_algorithm": "AES256"
        }
      }
  ]
)

assets_public_access = aws.s3.BucketPublicAccessBlock(
  "assets-public-access",
  bucket=bucket.id,
  block_public_acls=True,
  block_public_policy=True,
  ignore_public_acls=True,
  restrict_public_buckets=True
)

assets_lifecycle = aws.s3.BucketLifecycleConfiguration(
  "assets-lifecycle",
  bucket=bucket.id,
  rules=[
    {
      "id": "cleanup-incomplete-uploads",
      "status": "Enabled",
      "filter": {
        "prefix": "tmp/"
      },
      "abort_incomplete_multipart_upload": {
        "days_after_initiation": 7
      }
    }
  ]
)

# alb security group
alb_sg = aws.ec2.SecurityGroup(
  "learning-alb-sg",
  description="Allow public HTTP traffic to ALB",
  vpc_id=vpc.id,
  tags={"Name": "learning-alb-sg"}
)

alb_http = aws.vpc.SecurityGroupIngressRule(
  "alb-allow-http",
  security_group_id=alb_sg.id,
  cidr_ipv4="0.0.0.0/0",
  from_port=80,
  to_port=80,
  ip_protocol="tcp"
)

alb_egress = aws.vpc.SecurityGroupEgressRule(
  "alb-egress",
  security_group_id=alb_sg.id,
  cidr_ipv4="0.0.0.0/0",
  ip_protocol="-1"
)

# Application security group
app_sg = aws.ec2.SecurityGroup(
  "learning-asg-sg",
  description="Allow HTTP only from ALB",
  vpc_id=vpc.id,
  tags={"Name": "learning-asg-sg"}
)

app_http = aws.vpc.SecurityGroupIngressRule(
  "app-allow-alb-http",
  security_group_id=app_sg.id,
  referenced_security_group_id=alb_sg.id,
  from_port=80,
  to_port=80,
  ip_protocol="tcp"
)

app_egress = aws.vpc.SecurityGroupEgressRule(
  "app-egress",
  security_group_id=app_sg.id,
  cidr_ipv4="0.0.0.0/0",
  ip_protocol="-1"
)

# Target group
web_target_group = aws.lb.TargetGroup(
  "learning-web-target-group",
  name="learning-web-tg",
  port=80,
  protocol="HTTP",
  target_type="instance",
  vpc_id=vpc.id,
  health_check={
    "enabled": True,
    "path": "/",
    "protocol": "HTTP",
    "matcher": "200",
    "interval": 30,
    "healthy_threshold": 2,
    "unhealthy_threshold": 3
  },
  tags={"Name": "learning-web-target-group"}
)

# Application Load Balancer
web_alb = aws.lb.LoadBalancer(
  "learning-web-alb",
  internal=False,
  load_balancer_type="application",
  security_groups=[alb_sg.id],
  subnets=[
    public_subnet.id,
    public_subnet_b.id
  ],
  tags={
    "Name": "learning-web-alb",
    "Environment": "learning"
  }
)

# HTTP Listener
web_listener = aws.lb.Listener(
  "learning-http-listener",
  load_balancer_arn=web_alb.arn,
  port=80,
  protocol="HTTP",
  default_actions=[
    {
      "type": "forward",
      "target_group_arn": web_target_group.arn
    }
  ]
)

# Auto Scaling user data
asg_user_data = """
#!/bin/bash

set -eux

dnf install -y nginx

cat > /usr/share/nginx/html/index.html <<'EOF'
<h1>Hello from Auto Scaling!</h1>
<p>Instance launched using Pulumi Python.</p>
EOF

systemctl enable --now nginx
systemctl enable --now amazon-ssm-agent || true
"""

# Launch Template
web_launch_template = aws.ec2.LaunchTemplate(
  "learning-web-launch-template",
  name_prefix="learning-web-lt-",
  image_id=amazon_linux_ami.id,
  instance_type="t3.micro",

  iam_instance_profile={
    "name": ec2_instance_profile.name
  },

  vpc_security_group_ids=[app_sg.id],

  user_data = base64.b64encode(
    asg_user_data.encode("utf-8")
  ).decode("ascii"),

  tags={
    "Name": "learning-web-launch-template"
  },

  tag_specifications=[
    {
      "resource_type": "instance",
      "tags": {
          "Name": "learning-asg-instance",
          "Environment": "learning"
      }
    }
  ]
)

# Auto Scaling Group
web_asg = aws.autoscaling.Group(
  "learning-web-asg",

  min_size=1,
  desired_capacity=1,
  max_size=2,
  vpc_zone_identifiers=[
    private_subnet_a.id,
    private_subnet_b.id
  ],

  target_group_arns=[ web_target_group.arn ],

  launch_template={
    "id": web_launch_template.id,
    "version": "$Latest",
  },

  health_check_type="ELB",
  health_check_grace_period=180,
  default_instance_warmup=180,

  wait_for_capacity_timeout="10m",

  tags=[
    {
      "key": "Environment",
      "value": "learning",
      "propagate_at_launch": True
    }
  ]
)


# Target Tracking Scaling Policy
web_scaling_policy = aws.autoscaling.Policy(
  "learning-cpu-scaling-policy",

  autoscaling_group_name=web_asg.name,

  policy_type="TargetTrackingScaling",

  target_tracking_configuration={
    "predefined_metric_specification": {
      "predefined_metric_type": "ASGAverageCPUUtilization"
    },
    "target_value": 60.0
  }
)

# ALB and ASG outputs
pulumi.export("alb_dns_name", web_alb.dns_name)
pulumi.export("alb_url", web_alb.dns_name.apply(lambda dns: f"http://{dns}"))

pulumi.export("target_group_arn", web_target_group.arn)
pulumi.export("autoscaling_group_name", web_asg.name)
pulumi.export("launch_template_id", web_launch_template.id)

# RDS PostgreSQL
db_config = pulumi.Config()
db_username = db_config.require("dbUsername")
db_password = db_config.require_secret("dbPassword")

# database security group
db_sg = aws.ec2.SecurityGroup(
  "learning-db-sg",
  description="Allow postgres from application EC2",
  vpc_id=vpc.id,
  tags={
    "Name": "learning-db-sg"
  }
)

# allow postgres only from our EC2 security group
db_ingress = aws.vpc.SecurityGroupIngressRule(
  "allow-postgres-from-ec2",
  security_group_id=db_sg.id,
  referenced_security_group_id=web_security_group.id,
  from_port=5432,
  to_port=5432,
  ip_protocol="tcp"
)

# private db subnet group
db_subnet_group = aws.rds.SubnetGroup(
  "learning-db-subnet-group",
  subnet_ids=[
    private_subnet_a.id,
    private_subnet_b.id
  ],
  tags={
    "Name": "learning-db-subnets"
  }
)

database = aws.rds.Instance(
  "learning-postgres",
  engine="postgres",
  instance_class="db.t3.micro",
  allocated_storage=20,
  db_name="learningdb",
  username=db_username,
  password=db_password,
  db_subnet_group_name=db_subnet_group.name,
  vpc_security_group_ids=[db_sg.id],
  publicly_accessible=False,
  storage_encrypted=True,
  backup_retention_period=0,
  deletion_protection=False,
  skip_final_snapshot=True,
  tags={
    "Name": "learning-postgres",
    "Environment": "learning"
  }
)


# Export the name of the bucket
#pulumi.export('vpc_bucket', bucket.id)
pulumi.export("vpc_id", vpc.id)
pulumi.export("public_subnet_id", public_subnet.id)
pulumi.export("internet_gateway_id", internet_gateway.id)
pulumi.export("public_route_table", public_route_table.id)


pulumi.export("public_subnet_b_id", public_subnet_b.id)

pulumi.export("private_subnet_a_id", private_subnet_a.id)
pulumi.export("private_subnet_b_id", private_subnet_b.id)

pulumi.export("nat_gateway_id", nat_gateway.id)
pulumi.export("nat_eip", nat_eip.public_ip)

pulumi.export("private_route_table_id", private_route_table.id)

pulumi.export("web_security_group_id", web_security_group.id)
pulumi.export("web_security_group_arn", web_security_group.arn)

pulumi.export("ec2_role_name", ec2_role.name)
pulumi.export("ec2_role_arn", ec2_role.arn)
pulumi.export("ec2_instance_profile_name", ec2_instance_profile.name)

# EC2 OUTPUTS
pulumi.export("web_server_id", web_server.id)

pulumi.export("web_server_public_ip", web_server.public_ip)

pulumi.export("web_server_private_ip", web_server.private_ip)

pulumi.export("web_server_public_dns", web_server.public_dns)

pulumi.export("web_server_ami", amazon_linux_ami.id)

pulumi.export("data_volume_id", data_volume.id)


# s3 exports
pulumi.export("assets_bucket_name", bucket.id)
pulumi.export("assets_bucket_arn", bucket.arn)

# RDS exports
pulumi.export("db_endpoint", database.endpoint)
pulumi.export("db_address", database.address)
pulumi.export("db_port", database.port)