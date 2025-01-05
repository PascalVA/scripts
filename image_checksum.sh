#!/bin/bash

# this script recurisively looks for image files (.jp(e)g) in the working directory.
# it creates md5 hashes of the image data and imagemetadata (exif) seperately.
# This is useful to detect duplicate images that might have differences in metadata
# because you may, for some reason, have ruined the exif data on some of them.
#
# returns a pipe-separated list of rows following the following data structure:
# IMG_DATA_CHECKSUM,IMG_METADATA_CHECKSUM,IMG_DATETIMEORIGINAL,IMG_CREATEDATE,IMG_FILESIZE,ABUSOLUTE_FILEPATH
#
# Usage:
# ./imgdata_checksum.sh

# For example:
# ./imgdata_checksum.sh
#
# fff8946f8741facbc2873be25d69d03b|23b6a5c2713e1e62f00b4152fae33e01|2016:08:09 19:41:08|2002:12:08 12:00:00|1508093|/path/to/image/20160809_194108-1.jpg
# fff8946f8741facbc2873be25d69d03b|47435c8b9e685cf4943cfa07345112c3|2016:08:09 19:41:08|2002:12:08 12:00:00|1508056|/path/to/image/20160809_194108.jpg
# ...

IMGDATA_LOGFILE_DEFAULT="${HOME}/image_checksum.log"
IMGDATA_LOGFILE="${1:-$IMGDATA_LOGFILE_DEFAULT}"

# this function handles creating the checksums and echoing
# the result to a file safely using a semaphore
# this function is ran in parallel below
function parse_file () {
    imglog="$1"
    imgfile="$2"

    if [ -e "$imgfile" ]; then
        # set absolute filepath
        img_filepath_absolute=$(readlink -e "$imgfile")

        # exclude files that have already been parsed
        if [[ `echo $parsed_files | grep -c "$img_filepath_absolute"` -gt 0 ]]; then
            echo "Skipping \"$imgfile\" (already done)" 1>&2
            continue
        fi

        # process image data
        img_data_checksum=$(exiftool "$img_filepath_absolute" -all= -o - -b | md5sum | awk '{ print $1}')
        img_metadata_checksum=$(exiftool "$img_filepath_absolute" -x Directory -x FileName -x FilePermissions -x FileAccessDate -x FileModifyDate -x FileInodeChangeDate | sort | md5sum | awk '{ print $1}')
        img_datetimeoriginal=$(exiftool -b -DateTimeOriginal "$img_filepath_absolute" 2> /dev/null)
        img_createdate=$(exiftool -b -CreateDate "$img_filepath_absolute" 2> /dev/null)
        img_filesize=$(exiftool -b -FileSize "$img_filepath_absolute" 2> /dev/null)

        # use semaphore with max 1 worker when echoing to logfile and prevent race conditions
        sem --fg --id echolock -j1 -u "echo $img_data_checksum\|$img_metadata_checksum\|$img_datetimeoriginal\|$img_createdate\|$img_filesize\|$img_filepath_absolute | tee -a \"$imglog\""
    else
        echo "File \"$imgfile\" does not exist" 1>&2
    fi
}

export -f parse_file

echo "Using log file \"$IMGDATA_LOGFILE\"" 1>&2

# Create log file 
if [ ! -f "$IMGDATA_LOGFILE" ]; then
    touch "$IMGDATA_LOGFILE"
fi

# If log file exists, parse it so we can skip files that have already been hashed
if [ -e "$IMGDATA_LOGFILE" ]; then
    parsed_files=$(cat "$IMGDATA_LOGFILE" | awk -F',' '{print $NF}')
fi

echo "parsing files..." 1>&2

# runs each output line in parallel to speedup creating checksums of all images
find . -type f -iname '*.jp*g' | parallel parse_file "$IMGDATA_LOGFILE"
