#!/bin/bash
#
# Updates the kvm.pascalvanacker.com record on digitalocean using doctl
# Requires doctl to be installed and auth to have been instantiated

# Make sure we have the correct number of args
if [[ "$#" != "2" ]]; then
    cat <<EOF
Usage:
  $0 DOMAIN HOST
EOF
    exit 1
fi
DOMAIN=$1
HOST=$2

# Get a list of DNS records for the domain
RECORDS=$(doctl compute domain records list $DOMAIN -o json)

# Compare the current IP with the DNS record
REGISTERED_IP=$(echo $RECORDS | jq -r --arg host "$HOST" '.[] | select(.name==$host)'.data)
CURRENT_IP=$(public_ip.sh)

if [[ ! -z $REGISTERED_IP ]]; then
    if [[ $REGISTERED_IP == $CURRENT_IP ]]; then
        logger DNS record already up to date
	exit 0
    fi
fi

# Delete the existing record if it exists
RECORD_ID=$(echo $RECORDS | jq -r --arg host "$HOST" '.[] | select(.name == "$host")'.id)
if [[ ! -z $RECORD_ID ]]; then
    doctl compute domain records delete -f $DOMAIN $RECORD_ID
fi

# Update the dns record with the new ip
doctl compute domain records create $DOMAIN \
    --record-type A                         \
    --record-name kvm                       \
    --record-data $CURRENT_IP               \
    --record-ttl 60

logger Updated DNS record to new IP $CURRENT_IP
