#!/usr/bin/env python3

"""\
A script to fix the imagedescription exif tag that I broke on a number of files
This script expects a file containing image checksums of duplacate files in
a specific format and is not safe to be used for any other purpose

requirements:
  - exiftool must be installed on the machine running this script
"""

import argparse
import subprocess

from os.path import isfile
from time import sleep


def update_image_description(file, description):
    p = subprocess.Popen(
        ['exiftool', '-imagedescription=' + description, file],
        stdout=subprocess.PIPE
    )

    while p.poll() is None:
        sleep(0.2)

    if not p.returncode == 0:
        output = p.communicate()
        output_text = output[0].decode()
        return output_text
    else:
        return False
        print('An error has occured')


def get_image_description(file):
    p = subprocess.Popen(
        ['exiftool', '-s', '-s', '-s', '-imagedescription', file],
        stdout=subprocess.PIPE
    )

    while p.poll() is None:
        sleep(0.2)

    if not p.returncode:
        output = p.communicate()
        output_text = output[0].decode()
        return output_text
    else:
        return False
        print('An error has occured')


def main():

    parser = argparse.ArgumentParser(
        prog='exif description fixer',
        description='Fixes broken imagedescription exif tags of near-duplicate files',
        epilog='This program expects a checksum file containing images and their checksums in a very specific format'
    )
    parser.add_argument('checksum_file', help="Absolute path to the checksum file containing near-duplicate hashes")
    args = parser.parse_args()

    # Sort file records by imagedata hash
    _hash_records_map = {}
    with open(args.checksum_file, 'r') as f:
        for line in f.readlines():
            r = line.rstrip().split('|')

            hash_key = _hash_records_map.setdefault(r[0], [])
            if isfile(r[5]):
                hash_key.append(r[5])

    matches = {}
    for k, v in _hash_records_map.items():
        if len(v) == 2:
            matches[k] = v

            desc0 = get_image_description(v[0]).rstrip()
            desc1 = get_image_description(v[1]).rstrip()

            if desc0 is False or desc1 is False:
                continue

            # Fix broken imagedescription 'Image' tags
            if desc0 == 'Image':
                update_image_description(v[0], desc1)
            elif desc1 == 'Image':
                update_image_description(v[1], desc0)

            # update empty imagedescription tags
            if desc0 == '' and desc1 != '':
                update_image_description(v[0], desc1)
            elif desc1 == '' and desc0 != '':
                update_image_description(v[1], desc0)


if __name__ == '__main__':
    main()
