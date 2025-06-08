#!/usr/bin/env python3

import logging
import sqlite3

from argparse import ArgumentParser
from ast import literal_eval
from base64 import b64encode, b64decode
from hashlib import md5
from json import dumps as json_dump
from os import environ as env
from os.path import isfile
from os.path import abspath, basename
from pathlib import Path
from rich.progress import track
from shutil import which
from subprocess import run
from sys import exit


class ExifToolMissing(Exception):
    def __init__(self, message="Exiftool is not installed on the system"):
        self.message = message
        super().__init__(self.message)


EXIFTOOL_CMD = which("exiftool")
if not EXIFTOOL_CMD:
    raise ExifToolMissing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IMAGE_DATA_ROWS = ["name", "exifdata_checksum", "imagedata_checksum", "exifdata_encoded", "path"]


VALID_SOFTWARE_TAG_VALUES = [
  "1.0300",
  "1202061",
  "4.2.1",
  "4.3.3",
  "5.0.1",
  "5.1",
  "8.1.2",
  "910291",
  "A536BXXS4AVJ1",
  "A536BXXS4BWA2",
  "A536BXXS5CWB6",
  "A536BXXS5CWD3",
  "A536BXXS7CWG2",
  "A536BXXS7CWH1",
  "A536BXXS7CWI1",
  "A536BXXS8DWL1",
  "A536BXXS8DWL5",
  "A536BXXS8DXA1",
  "A536BXXS8DXC1",
  "A536BXXS9DXD1",
  "A536BXXU2AVD7",
  "A536BXXU2AVF2",
  "A536BXXU2AVG1",
  "A536BXXU3AVGA",
  "A536BXXU4AVH9",
  "A536BXXU4BVJG",
  "A536BXXU4BVKB",
  "A536BXXU4BVL2",
  "A536BXXU4CWB1",
  "A536BXXU5CWD1",
  "A536BXXU6CWE9",
  "A536BXXU7CWGJ",
  "A536BXXU7DWK6",
  "DSLR-A230 v1.00",
  "I8190XXAMG4",
  "I8190XXANA2",
  "I8190XXANI4",
  "I9300XXBLH1",
  "I9300XXDLIH",
  "I9300XXELLA",
  "I9300XXEMC2",
  "I9300XXEME2",
  "I9300XXEMG4",
  "I9300XXEMH1",
  "I9300XXUGMK6",
  "I9300XXUGNA5",
  "I9300XXUGND5",
  "RNE-L21 8.0.0.332(C432)",
  "RNE-L21 8.0.0.334(C432)",
  "RNE-L21 8.0.0.336(C432)",
  "RNE-L21 8.0.0.337(C432)",
  "RNE-L21 8.0.0.338(C432)",
  "RNE-L21 8.0.0.339(C432)",
  "RNE-L21 8.0.0.340(C432)",
  "RNE-L21 8.0.0.341(C432)",
  "RNE-L21 8.0.0.342(C432)",
  "RNE-L21 8.0.0.343(C432)",
  "RNE-L21 8.0.0.344(C432)",
  "RNE-L21 8.0.0.345(C432)",
  "RNE-L21 8.0.0.346(C432)",
  "RNE-L21 8.0.0.354(C432)",
  "RNE-L21 8.0.0.360(C432)",
  "RNE-L21C432B100",
  "RNE-L21C432B120",
  "RNE-L21C432B130",
  "RNE-L21C432B133",
  "RNE-L21C432B134",
  "RNE-L21C432B135",
  "RNE-L21C432B137",
  "SNE-LX1 10.0.0.170(C432E10R1P1)",
  "SNE-LX1 10.0.0.185(C432E10R1P1)",
  "SNE-LX1 10.0.0.193(C432E10R1P1)",
  "SNE-LX1 10.0.0.203(C432E10R1P1)",
  "SNE-LX1 10.0.0.212(C432E10R1P1)",
  "SNE-LX1 10.0.0.232(C432E10R1P1)",
  "SNE-LX1 10.0.0.245(C432E10R1P1)",
  "SNE-LX1 10.0.0.258(C432E11R1P1)",
  "SNE-LX1 10.0.0.271(C432E11R1P1)",
  "SNE-LX1 10.0.0.272(C432E11R1P1)",
  "SNE-LX1 10.0.0.273(C432E11R1P1)",
  "SNE-LX1 10.0.0.274(C432E11R1P1)",
  "SNE-LX1 10.0.0.277(C432E11R1P1)",
  "SNE-LX1 10.0.0.278(C432E11R1P1)",
  "SNE-LX1 10.0.0.279(C432E11R1P1)",
  "SNE-LX1 10.0.0.286(C432E12R1P1)",
  "SNE-LX1 10.0.0.288(C432E12R1P1)",
  "SNE-LX1 10.0.0.290(C432E12R1P1)",
  "SNE-LX1 8.2.0.138(C432)",
  "SNE-LX1 9.0.1.164(SP53C432E6R1P1)",
  "SNE-LX1 9.0.1.173(SP53C432E6R1P1)",
  "SNE-LX1 9.1.0.215(C432E4R1P1)",
  "SNE-LX1 9.1.0.229(C432E4R1P1)",
  "SNE-LX1 9.1.0.245(C432E4R1P1)",
  "SNE-LX1 9.1.0.266(C432E4R1P1)",
  "SNE-LX1 9.1.0.280(C432E4R1P1)",
  "SNE-LX1 9.1.0.291(C432E4R1P1)",
  "V233-00-01",
  "XXLK6",
]

INVALID_SOFTWARE_TAG_VALUES = [
  "Adobe Photoshop CC (Windows)",
  "Adobe Photoshop CC 2014 (Windows)",
  "Adobe Photoshop CC 2015 (Macintosh)",
  "Adobe Photoshop CS3 Macintosh",
  "Adobe Photoshop CS3 Windows",
  "Adobe Photoshop CS5 Windows",
  "Adobe Photoshop CS6 (Macintosh)",
  "Adobe Photoshop Elements 12.0 Windows",
  "Adobe Photoshop Express 9.0 (Android)",
  "Adobe Photoshop Lightroom 5.0 (Windows)",
  "Adobe Photoshop Lightroom 5.5 (Macintosh)",
  "Adobe Photoshop Lightroom Classic 7.5 (Macintosh)",
  "Google",
  "Microsoft Windows Photo Viewer 6.1.7600.16385",
  "Picasa",
  "Shotwell 0.30.7",
  "Layout from Instagram",
  "kinzie_reteu-user 6.0 MPKS24.78-8-12 6 release-keys",
]


class ImageData(object):
    """
    Defines an image object. It contains all the attributes we want to query for deduplication
    """

    def __init__(self, path):
        self.name = basename(path)
        self.path = abspath(path)
        self.imagedata_checksum = None
        self.exifdata_checksum = None
        self.exifdata = {}
        self.calculate_imagedata_checksum()
        self.parse_exifdata()

    def parse_exifdata(self):
        """
        Creates a checksum of only the image exif data
        It excludes a bunch of field that are always different
        Such as creation, modification or access times
        """
        _cmd = [
            EXIFTOOL_CMD,
            self.path,
            "-x", "Directory",
            "-x", "FileName",
            "-x", "FilePermissions",
            "-x", "FileAccessDate",
            "-x", "FileModifyDate",
            "-x", "FileInodeChangeDate",
            "-x", "ExifToolVersion",
        ]

        result = run(_cmd, capture_output=True)

        # parse stdout to mapping
        _exifdata = {}
        for line in result.stdout.decode("cp850").split("\n"):
            if not line:
                continue
            separator_index = line.index(":")
            k = line[:separator_index].rstrip(" ")
            v = line[separator_index+2:].lstrip(" ")
            _exifdata.update({k: v})

        self.exifdata = dict(sorted(_exifdata.items()))
        self.exifdata_checksum = md5(str(self.exifdata).encode()).hexdigest()

    def calculate_imagedata_checksum(self):
        """
        Creates a checksum of the image data without including exif data
        """
        _cmd = [
            EXIFTOOL_CMD,
            self.path,
            "-all=",
            "-o", "-",
            "-b",
        ]

        result = run(_cmd, capture_output=True)

        self.imagedata_checksum = md5(result.stdout).hexdigest()


class ImageDataDB(object):
    """
    Implements database operations for image data
    """
    def __init__(self, sqlite_db_path):
        self.db = abspath(sqlite_db_path)
        self.connection = sqlite3.connect(self.db)
        self.cursor = self.connection.cursor()
        self.initialize_database()

    def initialize_database(self):
        logger.debug('Create image_table data if it does not exist')
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS "
            f"image_data({','.join(IMAGE_DATA_ROWS)})"
        )

        logger.debug(
            'Create index for "imagedata_checksum" column on the image_data table'
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS imagedata_checksum ON image_data(imagedata_checksum)"
        )

        logger.debug(
            'Create index for "exifdata_checksum" column on the image_data table'
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS exifdata_checksum ON image_data(exifdata_checksum)"
        )

        logger.debug(
           'Create compound index for the "imagedata_checksum" and "exifdata_checksum" columns on the image_data table'
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS checksums ON image_data(imagedata_checksum, exifdata_checksum)"
        )

    def insert(self, image_data):
        """
        insert a single image_data object as one row
        """
        self.cursor.execute(f"""
            INSERT INTO image_data VALUES
            (
                '{escape_query_string(image_data.name)}',
                '{image_data.exifdata_checksum}',
                '{image_data.imagedata_checksum}',
                '{b64encode(str(image_data.exifdata).encode()).decode()}',
                '{escape_query_string(image_data.path)}'
            )
        """)
        self.connection.commit()

    def remove_by_path(self, path):
        res = self.cursor.execute(f"DELETE FROM image_data WHERE path = '{escape_query_string(path)}'")
        self.connection.commit()

    def select_all(self):
        res = self.cursor.execute("SELECT * FROM image_data")
        return res.fetchall()

    def select_by_path(self, path):
        res = self.cursor.execute(f"""
            SELECT * FROM image_data WHERE path = '{escape_query_string(abspath(path))}'
        """)
        return res.fetchall()

    def path_exists(self, path):
        res = self.cursor.execute(f"SELECT * FROM image_data WHERE path = '{escape_query_string(abspath(path))}'")
        return (res.fetchone() is not None)

    def dump(self):
        return list(
            map(lambda r: dict(zip(IMAGE_DATA_ROWS, r)), self.select_all())
        )


def get_image_sets(db):
    """Returns two dictionaries of images sorted by imagedata_checksum (as the key)
       The first dictionary contains only images with duplicates while the second
       contains all images
    """
    rows = db.dump()

    all_sets = {}
    for row in rows:
        all_sets.setdefault(row['imagedata_checksum'], []).append(row)

    duplicate_sets = {k: v for k, v in all_sets.items() if len(v) > 1}

    return duplicate_sets, all_sets


def decode_exifdata(encoded_string):
    return literal_eval(b64decode(encoded_string).decode())


# TODO: needs improvement
def escape_query_string(string):
    return string.replace("'", "''")


def find_images(path):
    """
    Recursively find jpg and jpeg images on the specified path
    """
    # the question mark matches a single chacter, the p is not optional
    jpgs = list(Path(abspath(path)).rglob('**/*.jpg'))
    jpegs = list(Path(abspath(path)).rglob('**/*.jpeg'))
    return sorted(jpgs + jpegs)


def index_images(db, path, force_reindex):
    """
    When called all files at path will be indexed into the database
    """
    logger.info(f'Searching for files in "{path}"')
    files = find_images(path)

    logger.info(f'Staring file index on {len(files)} files')
    for f in track(files, description="Indexing files..."):
        # skip files we have already indexed
        if db.path_exists(f) and not force_reindex:
            logger.debug(f'Skipping file "{f}"')
            continue

        try:
            logger.debug(f'Parsing file "{f}"')
            image_data = ImageData(f)

            logger.debug(f'Inserting file "{f}"')
            db.insert(image_data)
        except Exception as e:
            logger.error(f'Error occurred while parsing file "{f}"')
            raise e


def find_videos(db, path):
    pass


def index_videos(db, path):
    pass


def index(db, args):
    index_images(db, args.path, args.force_reindex)


def dump(db, args):
    print(json_dump(db.dump()))


def images_by_tag(db, args):
    """Return list of image paths that have a matchin exiftag value"""
    matches = []

    _, images = get_image_sets(db)
    for k, v in images.items():
        for i in v:
            exifdata = decode_exifdata(i.get('exifdata_encoded', ''))
            if exifdata.get(args.tag, '') == args.value:
                matches.append(i['path'])

    print(json_dump(matches))


def unique_tag_values(db, args):
    """Returns a list of unique values for a tag"""
    _, images = get_image_sets(db)
    unique_values = set()
    for k, v in images.items():
        for i in v:
            try:
                exifdata = decode_exifdata(i.get('exifdata_encoded', ''))
                unique_values.add(exifdata.get(args.tag, ''))
            except BaseException as e:
                print(i['path'], e)

    print(json_dump(list(unique_values)))


def fix(db, args):
    """Fix exif data in duplicate sets"""
    dupes, _ = get_image_sets(db)
    for d in dupes:
        pass
        #
        # Software Tag
        #


def stats(db, args):
    """Print statistics on duplicates"""
    dupes, images = get_image_sets(db)
    print(f'Found {len(images.items())} sets of images of which {len(dupes.items())} have duplicates')


def clean(db, args):
    """Print statistics on duplicates"""
    for i in db.dump():
        if not isfile(i['path']):
            logger.info(f'Removing missing file at {i["path"]}')
            db.remove_by_path(i["path"])

def parse_args():
    parser = ArgumentParser(
        prog="imgtool",
        description="Tool to compare images in a directory and find duplicates while ignoring exif data"
    )
    parser.add_argument("-D", "--dbpath", type=str, default=f"{env["HOME"]}/imgtool.sqlite")
    parser.set_defaults(func=parser.print_usage)
    subparsers = parser.add_subparsers()

    parser_index = subparsers.add_parser("index", help="Index image files")
    parser_index.set_defaults(func=index)
    parser_index.add_argument("path", help="Path to search for images (recursively)")
    parser_index.add_argument(
        "-f", "--force-reindex", action="store_true", help="Force re-indexation of existing files"
    )

    parser_dump = subparsers.add_parser("dump", help="Dump all rows in the database")
    parser_dump.set_defaults(func=dump)

    parser_unique = subparsers.add_parser("unique-tag-values", help="List unique values for a specific tag")
    parser_unique.add_argument(
        "-t", "--tag", required=True, help="Exif tag you want to check"
    )
    parser_unique.set_defaults(func=unique_tag_values)

    parser_tagvalue = subparsers.add_parser("find-by-tag-value", help="List unique values for a specific tag")
    parser_tagvalue.add_argument(
        "-t", "--tag", required=True, help="Exif tag you want to search for"
    )
    parser_tagvalue.add_argument(
        "-v", "--value", required=True, help="Value of the tag you are searching for"
    )
    parser_tagvalue.set_defaults(func=images_by_tag)

    parser_fix = subparsers.add_parser("fix", help="Fix exifdata")
    parser_fix.set_defaults(func=fix)

    parser_stats = subparsers.add_parser("stats", help="Show duplicate stats")
    parser_stats.set_defaults(func=stats)

    parser_stats = subparsers.add_parser("clean", help="Clean up missing files from database")
    parser_stats.set_defaults(func=clean)

    args = parser.parse_args()

    if args.func == parser.print_usage:
        parser.print_usage()
        exit(1)

    return args


def main():
    logger.debug('Parsing command-line arguments')
    args = parse_args()

    logger.debug('Initializing database client"')
    db = ImageDataDB(args.dbpath)

    logger.debug('Calling subcommand function')
    args.func(db, args)


if __name__ == "__main__":
    main()
