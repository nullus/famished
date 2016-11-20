import base64
from datetime import datetime
import json
import os
import requests
from textwrap import dedent
import time

import boto3
from fabric.api import abort, env, execute, task, warn

import masterless

#
# FIXME:
# Generic class to handle caching URL objects?
#   check modified time, save URL to UUID(URL) in cache
#   provide cached object
#

def iter_instance_type_on_demand_price(url):
    '''Scrape entire EC2 pricing JSON, it's big...'''

    resp = requests.get(url)

    if resp.status_code != 200:
        abort('Failed to retrieve EC2 offers')

    offers = resp.json()

    def match(product):
        return (
            product['productFamily'] == "Compute Instance" and
            product['attributes']['location'] == "Asia Pacific (Sydney)" and
            product['attributes']['operatingSystem'] == "Linux" and
            product['attributes']['usagetype'].startswith('APS2-BoxUsage:')
        )

    return (
        (sku_product[1]['attributes']['instanceType'], skutermprice_pricedimensions[1]['pricePerUnit']['USD'])

        for sku_product
        in offers['products'].iteritems()
        if match(sku_product[1])

        for skuterm_ondemand
        in offers['terms']['OnDemand'][sku_product[0]].iteritems()

        for skutermprice_pricedimensions
        in skuterm_ondemand[1]['priceDimensions'].iteritems()
    )

@task
def scrape_aws_pricing(url='https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/index.json', output='pricing.json'):
    resp = requests.get(url)

    if resp.status_code != 200:
        abort('Failed to retrieve pricing index')

    index = resp.json()

    try:
        # Don't proceed if we're already up to date
        if datetime.strptime(index['publicationDate'], "%Y-%m-%dT%H:%M:%SZ") <= datetime.utcfromtimestamp(os.stat(output).st_mtime):
            return
    except OSError:
        # Expecting file not found, but there could be others?
        pass

    with open(output, "wb") as pricing:
        json.dump(
            dict(iter_instance_type_on_demand_price(
                requests.compat.urljoin(resp.url, index['offers']['AmazonEC2']['currentVersionUrl'])
            )),
            pricing
        )

def get_spot_instance_id(spot_instance_request_id, wait=30, retry=6):
    ec2 = boto3.client('ec2')

    for attempt in xrange(0, retry):
        time.sleep(wait)

        response = ec2.describe_spot_instance_requests(SpotInstanceRequestIds=[spot_instance_request_id])

        if len(response["SpotInstanceRequests"]) != 1:
            warn("Incorrect number of spot instance requests: ({0} expected 1)".format(len(response["SpotInstanceRequests"])))

        spot_req = response["SpotInstanceRequests"][0]

        if spot_req["State"].lower() == "active" and spot_req["InstanceId"]:
            return spot_req["InstanceId"]

    ec2.cancel_spot_instance_requests(SpotInstanceRequestIds=[spot_instance_request_id])

    abort("Failed to launch spot instance")

def get_instance_public_ip(instance_id, wait=30, retry=6):
    ec2 = boto3.client('ec2')

    for attempt in xrange(0, retry):
        time.sleep(wait)

        response = ec2.describe_instances(InstanceIds=[instance_id])

        if len(response["Reservations"]) != 1:
            warn("Incorrect number of reservations: ({0} expected 1)".format(len(response["SpotInstanceRequests"])))

        res = response["Reservations"][0]["Instances"][0]

        if res["State"]["Name"].lower() == "running":
            return res["PublicIpAddress"]

    ec2.terminate_instances(InstanceIds=[instance_id])

    abort("Failed to get public IP address")

@task
def start_spot_instance(spot_price='0.03', image_id="ami-db704cb8", key_name="null@dylan-laptop 20160517", instance_type='c4.large'):
    ec2 = boto3.client('ec2')

    response = ec2.request_spot_instances(SpotPrice=spot_price, InstanceCount=1, Type='one-time', LaunchSpecification={
        "ImageId": image_id,
        # FIXME: Create our own key, persist some data, take advantage of idempotence
        "KeyName": key_name,
        "UserData": base64.encodestring(dedent("""
            #cloud-config
            repo_update: true
            repo_upgrade: all
            packages:
            - puppet
        """)),
        "InstanceType": instance_type,
        "SecurityGroupIds": ['sg-1f04ac7b', 'sg-dd2c3eb9'],
        "IamInstanceProfile": {
            "Arn": "arn:aws:iam::842521264722:instance-profile/DontStarveTogether"
        },
        })


    if len(response["SpotInstanceRequests"]) != 1:
        warn("Incorrect number of spot instance requests: ({0} expected 1)".format(len(response["SpotInstanceRequests"])))

    spot_req = response["SpotInstanceRequests"][0]

    if spot_req["State"].lower() in ['open', 'active']:
        instance_id = get_spot_instance_id(spot_instance_request_id=spot_req["SpotInstanceRequestId"])
    else: # Status doesn't look happy
        abort("Spot request failed: {0}".format(spot_req["Fault"]["Message"]))

    public_ip = get_instance_public_ip(instance_id=instance_id)

    route53 = boto3.client('route53')

    response = route53.change_resource_record_sets(HostedZoneId='/hostedzone/Z3V0Y7RWSVPOWL', ChangeBatch={
        "Changes": [{
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": env.host,
                "Type": "A",
                "TTL": 60,
                "ResourceRecords": [{
                    'Value': public_ip,
                    }],
                },
            }],
        })

    change_id = response['ChangeInfo']['Id']

    for attempt in xrange(0, 6):
        time.sleep(5)
        response = route53.get_change(Id=change_id)

        if response['ChangeInfo']['Status'].lower() == "insync":
            break

