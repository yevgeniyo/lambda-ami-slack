# Lambda AMI creator

## IAM

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "directorEc2",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeRegions",
                "ec2:DescribeInstances",
                "ec2:DescribeImages",
                "ec2:CreateImage",
                "ec2:DescribeSnapshots",
                "ec2:DeregisterImage",
                "ec2:DeleteSnapshot",
                "ec2:CreateSnapshot"
            ],
            "Resource": "*"
        }
    ]
}
```

## Prepearing .zip

- `pip install module-name -t .`
- `zip -r ../myDeploymentPackage.zip .`