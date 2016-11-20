# DST dedicated

## Requirements

API call to create/destroy server HTTPS?
  letsencrypt + s3front (cloudfront)
  or Amazon internal service?
Build dedicated server from scratch (Amazon Linux AMI)
Persist world data on destroy
Load world data on create

## Questions

Can offline mode work with public IP?

## HowTo

Probably best not to query the AWS price list too frequently, the EC2 offers JSON is ~70MB. Save the on-demand pricing JSON:

    curl -O https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/index.json

