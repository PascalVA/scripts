#!/usr/bin/env python3

import logging
import subprocess
import sqlite3

from argparse import ArgumentParser
from base64 import b64encode, b64decode
from hashlib import md5
from os import environ as env
from os.path import abspath, basename
from pathlib import Path
from rich.progress import track
from shutil import which
from subprocess import PIPE, run
from json import dumps as jsondump


EXIFTOOL_CMD=which("exiftool")
IMAGE_DATA_ROWS = ["name", "exifdata_checksum", "imagedata_checksum", "exifdata_encoded", "path"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExifToolMissing(Exception):
    def __init__(self, message="Exiftool is not installed on the system"):
        self.message = message
        super().__init__(self.message)


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
        logger.debug(f'Create image_table data if it does not exist')
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS "
            f"image_data({','.join(IMAGE_DATA_ROWS)})"
        )

        logger.debug(f'Create index for "imagedata_checksum" column on the image_data table')
        self.cursor.execute("CREATE INDEX IF NOT EXISTS imagedata_checksum ON image_data(imagedata_checksum)")

        logger.debug(f'Create index for "exifdata_checksum" column on the image_data table')
        self.cursor.execute("CREATE INDEX IF NOT EXISTS exifdata_checksum ON image_data(exifdata_checksum)")

        logger.debug(f'Create compound index for the "imagedata_checksum" and "exifdata_checksum" columns on the image_data table')
        self.cursor.execute("CREATE INDEX IF NOT EXISTS checksums ON image_data(imagedata_checksum, exifdata_checksum)")

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
        return (res.fetchone() != None)


def find_images(path):
    """
    Recursively find jpg and jpeg images on the specified path
    """
    # the question mark matches a single chacter, the p is not optional
    jpgs = list(Path(abspath(path)).rglob('**/*.jpg'))
    jpegs = list(Path(abspath(path)).rglob('**/*.jpeg'))
    return sorted(jpgs + jpegs)


def index_images(db, path):
    """
    When called all files at path will be indexed into the database
    """
    logger.info(f'Searching for files in "{path}"')
    files = find_images(path)

    logger.info(f'Staring file index on {len(files)} files')
    for f in track(files, description="Indexing files..."):
        if db.path_exists(f):
            continue

        try:
            logger.debug(f'Parsing file "{f}"')
            image_data = ImageData(f)

            logger.debug(f'Inserting file "{f}"')
            db.insert(image_data)
        except Exception as e:
            loger.error(f'Error occurred while parsing file "{f}"')
            raise(e)


def find_videos(db, path):
    pass


def index_videos(db, path):
    pass


def parse_args():
    parser = ArgumentParser(
        prog="imgtool",
        description="Tool to compare images in a directory and find duplicates while ignoring exif data"
    )
    parser.add_argument("-D", "--dbpath", type=str, default=env["HOME"]+"/imgtool.sqlite")
    subparsers = parser.add_subparsers()

    parser_index = subparsers.add_parser("index", help="Index image files ")
    parser_index.add_argument("path", help="Path to search for images (recursively)")
    parser_index.set_defaults(func=index)

    parser_count = subparsers.add_parser("count", help="Prints the number of rows found in the database")
    parser_count.set_defaults(func=count)

    parser_dump = subparsers.add_parser("dump", help="Dump all rows in the database")
    parser_dump.set_defaults(func=dump)

    args = parser.parse_args()
    args.func(args)


def index(args):
    logger.info(f'Initializing database client"')
    db = ImageDataDB(args.dbpath)

    index_images(db, args.path)


def count(args):
    logger.info(f'Initializing database client"')
    db = ImageDataDB(args.dbpath)

    print(len(db.select_all()))


def dump(args):
    logger.info(f'Initializing database client"')
    db = ImageDataDB(args.dbpath)

    # convert row results to JSON
    records = list(
        map(lambda r: dict(zip(IMAGE_DATA_ROWS, r)), db.select_all())
    )
    print(jsondump(records))


# TODO: needs improvement
def escape_query_string(string):
    return string.replace("'", "''")


def main():

    if not EXIFTOOL_CMD:
        raise ExifToolMissing

    args = parse_args()


if __name__ == "__main__":
    main()
