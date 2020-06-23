# AMI backup creator

This project created for automating process of EC2 AMI`s creation.

## Topology

![Screen Shot 2020-06-23 at 15 57 39](https://user-images.githubusercontent.com/14246521/85406380-65f5f480-b56a-11ea-80a9-dd1df79f31ea.png)

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

- `pip install requests -t .`
- `zip -r ../myDeploymentPackage.zip .`


## Environment Variables

- `*RETENTION*`            -  number of days
- `*SLACK_CHANNEL_NAME*`   -  name of slack channel where you want to get notifications
- `*SLACK_WEBHOOK_URL*`    -  slack web hook URL

## Slack output

<img width="425" alt="Screen Shot 2020-06-23 at 16 03 06" src="https://user-images.githubusercontent.com/14246521/85408382-1e249c80-b56d-11ea-802f-4fee69f912cd.png">