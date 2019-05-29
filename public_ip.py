#!/usr/bin/env python3
#
# Returns the current public ip address of this machine by using an external provider
# It randomly selects a provider to get your current public ip address
# Currently used ip providers: 
#   - httpbin.org
#   - ipfy.org
#   - wtfismyip.com

from __future__ import print_function
import requests
from random import shuffle
from re import search

SIMPLE_IP_REGEX = '\\b(?:\\d{1,3}\\.){3}\\d{1,3}\\b'


def ip_json(url, json_key):
    return requests.get(url).json().get(json_key, None)


def search_ip(ip_str):
    ip = search(SIMPLE_IP_REGEX, ip_str)
    if ip:
       return ip.group()
    return None


def ip_httpbin_org():
    return search_ip(ip_json('https://httpbin.org/ip', 'origin'))


def ip_ipfy_org():
    return search_ip(ip_json('https://api.ipify.org/?format=json', 'ip'))


def ip_wtfismyip_com():
    return search_ip(ip_json('https://ipv4.wtfismyip.com/json', 'YourFuckingIPAddress'))


def get_ip():
    """Get the ip address from a random provider
       Try them all sequentially until one succeeds
    """
    ip = None
    providers = [
        {'name': 'httpbin.org', 'func': ip_httpbin_org},
        {'name': 'ipfy.org', 'func': ip_ipfy_org},
        {'name': 'wtfismyip.com', 'func': ip_wtfismyip_com}
    ]
    shuffle(providers)

    for provider in providers:
        try:
            ip = provider["func"]()
        except:
            continue
        break
    if ip:
        return ip
    return None

if __name__ == "__main__":
    print(get_ip())
