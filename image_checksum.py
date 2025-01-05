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


EXIFTOOL_CMD=which("exiftool")
SQLITE_DB_PATH=f'{env["HOME"]}/image_checksum.sqlite'
TEST_IMAGE_PATH="/tank/shares/media/20231031_backup/"

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
        for line in result.stdout.decode().split("\n"):
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
        self.create_table()

    def create_table(self):
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS "
            "image_data(name, exifdata_checksum, imagedata_checksum, exifdata_encoded, path)"
        )

    def insert(self, image_data):
        """
        insert a single image_data object as one row
        """
        self.cursor.execute(f"""
            INSERT INTO image_data VALUES
            (
                '{image_data.name}',
                '{image_data.exifdata_checksum}',
                '{image_data.imagedata_checksum}',
                '{b64encode(str(image_data.exifdata).encode()).decode()}',
                '{image_data.path}'
            )
        """)
        self.connection.commit()

    def select_all(self):
        res = self.cursor.execute("SELECT * FROM image_data")
        return res.fetchall()


    def select_by_path(self, path):
        res = self.cursor.execute(f"""
            SELECT * FROM image_data WHERE path = '{abspath(path)}'
        """)
        return res.fetchall()

    def path_exists(self, path):
        res = self.cursor.execute(f"""
            SELECT * FROM image_data WHERE path = '{abspath(path)}'
        """)
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

        logger.debug(f'Parsing file "{f}"')
        image_data = ImageData(f)

        logger.debug(f'Inserting file "{f}"')
        db.insert(image_data)


def find_videos(db, path):
    pass


def index_videos(db, path):
    pass



def main():
    if not EXIFTOOL_CMD:
        raise ExifToolMissing

    logger.info(f'Initializing database client"')
    db = ImageDataDB(SQLITE_DB_PATH)

    # TODO: get image path from argparse
    index_images(db, TEST_IMAGE_PATH)

    #print(len(db.select_all()))

if __name__ == "__main__":
    main()
