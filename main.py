import os
import json
import boto3
import requests
import datetime

date = datetime.datetime.now()
slack_webhook_url = os.environ['SLACK_WEBHOOK_URL']
slack_channel_name = os.environ['SLACK_CHANNEL_NAME']
retention = os.environ['RETENTION']


def get_account_id():
    id = boto3.client('sts').get_caller_identity().get('Account')
    return id

def get_all_regions():
    client = boto3.client("ec2")
    regions = [region['RegionName'] for region in client.describe_regions()['Regions']]
    return regions

def send_alert_slack(message):
    try:
        r = requests.post(slack_webhook_url, json=message)
        r.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        raise Exception(errh)
    except requests.exceptions.ConnectionError as errc:
        raise Exception(errc)
    except requests.exceptions.Timeout as errt:
        raise Exception(errt)
    except requests.exceptions.RequestException as err:
        raise Exception(err)

def registrer_message(region, channel_name, records, account_id):
    names = ""
    ids = ""
    for record in records:
        ids = ids + f"{record['Id']} \n"
        names = names + f"{record['Name']} \n"
    body = {
	"username": "AWS AMI backups",
	"channel": channel_name,
	"icon_emoji": ":backup:",
    "attachments": [
        {
			"text": "*AMI images were created successfuly*",
			"color": "49C39E",
			"fields": [{
        	  "title": "Region",
        	  "value": region,
        	  "short": "True"
			},
			{
        	  "title": "Account",
        	  "value": account_id,
        	  "short": "False"
			},
            {
        	  "title": "Name",
        	  "value": names,
        	  "short": "False"
			},
            {
        	  "title": "ID",
        	  "value": ids,
        	  "short": "False"
			}		   
			]
        }
    ]
    }
    return send_alert_slack(body)


def deregistrer_message(region, channel_name, records, account_id, retention):
    ids = ""
    creation_date = ""
    for record in records:
        ids = ids + f"{record['ID']} \n"
        creation_date = creation_date + f"{record['CreationDate']} \n"
    body = {
	"username": "AWS AMI backups",
	"channel": channel_name,
	"icon_emoji": ":deregister:",
    "attachments": [
        {
			"text": f"*Deregistering images older than {retention} days*",
			"color": "EBB424",
			"fields": [{
        	  "title": "Region",
        	  "value": region,
        	  "short": "True"
			},
			{
        	  "title": "Account",
        	  "value": account_id,
        	  "short": "False"
			},
            {
        	  "title": "ID",
        	  "value": ids,
        	  "short": "False"
			},
            {
        	  "title": "ID",
        	  "value": creation_date,
        	  "short": "False"
			}			   
			]
        }
    ]
    }
    return send_alert_slack(body)

def finding_ec2_with_needed_tag(region, tag_name):
    client = boto3.client('ec2',region)
    reservations = client.describe_instances( Filters=[
            { 
            'Name': 'tag-key', 
            'Values': [tag_name,]
            },
            { 
            'Name': 'tag-value', 
            'Values': ['true', 'True']
            },  
            ]).get('Reservations')
    instances = sum([[i for i in instance['Instances']]for instance in reservations], [])
    output = []
    for instance in instances:
        for tag in instance['Tags']:
            if tag['Key'] == 'Name':
                output.append({'Name':tag['Value'],'Id':instance['InstanceId']})
    return output


def creating_ami(region, instance_id):
    client = boto3.client('ec2',region)            
    try:
        name= f"Backup for {instance_id} {date.strftime('%Y-%m-%d')}"
        description= f"AMI for {instance_id} created by lambda"
        image = client.create_image(Description = description,
                                    DryRun = False, 
                                    InstanceId = instance_id, 
                                    Name = name, 
                                    NoReboot = True)
        if image['ImageId'].startswith("ami"):
            return image['ImageId']
        print(image['ImageId'])
    except Exception as ex:
        print(ex)

def deregister_image(image_id, region):
    ec2 = boto3.client('ec2',region)
    SnapDesc= f"*{image_id}*"
    myAccount = boto3.client('sts').get_caller_identity()['Account']
    snapshots = ec2.describe_snapshots(Filters=[{'Name': 'description','Values': [SnapDesc,]},],MaxResults=10000, OwnerIds=[myAccount])['Snapshots']
    print(f"Deregistering image {image_id}")
    ec2.deregister_image(DryRun=False,ImageId=image_id,)
    for snapshot in snapshots:
        if snapshot['Description'].find(image_id) > 0:
            ec2.delete_snapshot(SnapshotId=snapshot['SnapshotId'])
            print(f"Deleting snapshot {snapshot['SnapshotId']}")
    
    

def finding_images_which_need_deregister(region, retention):
    output = []
    register_date = datetime.datetime.utcnow().date() - datetime.timedelta(days=retention)
    ec2 = boto3.client('ec2',region)
    ami_name = "Backup for *"
    images = ec2.describe_images(Filters=[
            {
                'Name': 'name',
                'Values': [ami_name,]
            }
            ])['Images']
    for image in images:
        if str(register_date) >= image['CreationDate'][:10]:
            output.append({'ID':image['ImageId'],'CreationDate':image['CreationDate'][:10]})
            deregister_image(image['ImageId'], region)
    print(output)
    return output



def lambda_handler(event, context):
    account_id = get_account_id()
    regions = get_all_regions()
    for region in regions:
        instances = finding_ec2_with_needed_tag(region, 'backup')
        amies = []
        for instance in instances:
            ami = creating_ami(region, instance['Id'])
            if ami != None:
                amies.append(ami)    
            print(amies)
        # print(instances)
        if len(amies) >0:
            registrer_message(region, slack_channel_name, instances, account_id)
        # Deregistration process
        deregistered = finding_images_which_need_deregister(region, retention)
        if len(deregistered) > 0:
            deregistrer_message(region, slack_channel_name, deregistered, account_id, retention)