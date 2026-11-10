"""An AWS Python Pulumi program"""

import pulumi
from pulumi_aws import s3

config = pulumi.Config()

# returns value or throw error if value not found
env = config.require("environment")

# returns value or None if not found
# env = config.get("environment")

print(env)

# Create an AWS resource (S3 Bucket)
bucket = s3.Bucket(
    'my-bucket', 
     tags={
            "environments": env
     }
)

hello = s3.BucketObject(
  "hello",
  bucket=bucket.id,
  key="hello.txt",
  content="Hello, Pulumi! Contents updated.",
)

# Export the name of the bucket
pulumi.export('bucket_name', bucket.id)

bucket_uri = bucket.id.apply(
  lambda name: f"s3://{name}"
)

pulumi.export("bucket_uri", bucket_uri)

pulumi.export("object_key", hello.key)
