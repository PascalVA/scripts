#!/bin/bash
#
# required packages:
#   - qrencode
#   - feh
# usage:
#   wifiqr.sh SSID PASSWORD [TYPE] [HIDDEN]

SSID=$1
PASSWORD=$2
TYPE=${3:-WPA}
HIDDEN=${4:-false}

echo "WIFI:S:${SSID};T:${TYPE};P:${PASSWORD};H:${HIDDEN};;" | qrencode -s 5 -o - | feh -F -