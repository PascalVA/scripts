#!/usr/bin/env python3

from os import remove
from os.path import isfile

LOGFILE = "./imgchecksum.log"


# def get_image_description(file):
#     p = subprocess.Popen(
#         ['exiftool', '-s', '-s', '-s', '-imagedescription', file],
#         stdout=subprocess.PIPE
#     )
#
#     while p.poll() is None:
#         sleep(0.2)
#
#     if not p.returncode:
#         output = p.communicate()
#         output_text = output[0].decode()
#         return output_text
#     else:
#         return False
#         print('An error has occured')


def parse_file(file):
    _hash_records_map = {}
    with open(file, 'r') as f:
        for line in f.readlines():
            r = line.rstrip().split('|')
            r = [0] + r  # prepend 'active' bool

            hash_key = _hash_records_map.setdefault(r[1], [])
            if isfile(r[6]):
                hash_key.append(r)
    return _hash_records_map


def extract_duplicate_records(records):
    _res = {}
    for k, v in records.items():
        if len(v) > 1:
            _res.update({k: v})
    return _res


def main():
    duplicates = extract_duplicate_records(parse_file(LOGFILE))
    print(len(duplicates))
    for _, v in duplicates.items():
        from pprint import pprint
        pprint(v)
        # if len(v) == 2:
        #     print(get_image_description(v[0][-1]), get_image_description(v[1][-1]))
        # found_indices = []
        # for i, r in enumerate(v):
        #     if "/path/to/images/" in r[-1]:
        #         remove(r[-1])

if __name__ == "__main__":
    main()
