#!/bin/bash

# recurisively look for image files in the working directory and create md5 hashes of the image data and imagemetadata (exif) seperately.
# Returns a CSV of IMG_DATA_CHECKSUM,IMG_METADATA_CHECKSUM,IMG_DATETIMEORIGINAL,IMG_CREATEDATE,IMG_FILESIZE,ABUSOLUTE_FILEPATH

# it will recursively search for JP(E)G files in the current directory
#
# Usage:
# ./imgdata_checksum.sh DIRECTORY

# For example:
# ./imgdata_checksum.sh /path/to/images/
#
# fff8946f8741facbc2873be25d69d03b|23b6a5c2713e1e62f00b4152fae33e01|2016:08:09 19:41:08|2002:12:08 12:00:00|1508093|/path/to/image/20160809_194108-1.jpg
# fff8946f8741facbc2873be25d69d03b|47435c8b9e685cf4943cfa07345112c3|2016:08:09 19:41:08|2002:12:08 12:00:00|1508056|/path/to/image/20160809_194108.jpg

#IFS=$'\n'
IMGDATA_LOGFILE_DEFAULT="${HOME}/imgchecksum.log"
IMGDATA_LOGFILE="${1:-$IMGDATA_LOGFILE_DEFAULT}"

function parse_file () {
    imgfile=$1
    if [ -e "$imgfile" ]; then
        img_filepath_absolute=$(readlink -e "$imgfile")

        # exclude files that have already been parsed
        if [[ `echo $parsed_files | grep -c "$img_filepath_absolute"` -gt 0 ]]; then
            echo "Skipping \"$imgfile\" (already done)" 1>&2
            continue
        fi

        img_data_checksum=$(exiftool "$img_filepath_absolute" -all= -o - -b | md5sum | awk '{ print $1}')
        img_metadata_checksum=$(exiftool "$img_filepath_absolute" -x Directory -x FileName -x FilePermissions -x FileAccessDate -x FileModifyDate -x FileInodeChangeDate | sort | md5sum | awk '{ print $1}')
        img_datetimeoriginal=$(exiftool -b -DateTimeOriginal "$img_filepath_absolute" 2> /dev/null)
        img_createdate=$(exiftool -b -CreateDate "$img_filepath_absolute" 2> /dev/null)
        img_filesize=$(exiftool -b -FileSize "$img_filepath_absolute" 2> /dev/null)
        #echo $img_data_checksum,$img_metadata_checksum,$img_filepath_absolute,$img_datetimeoriginal,$img_createdate,$img_filesize
        echo $img_data_checksum\|$img_metadata_checksum\|$img_datetimeoriginal\|$img_createdate\|$img_filesize\|$img_filepath_absolute
    else
        echo File \"$imgfile\" does not exist 1>&2
    fi
}

export -f parse_file

echo Using log file "$IMGDATA_LOGFILE" 1>&2

# If log file exists, parse it so we can skip files that have already been hashed
if [ -e "$IMGDATA_LOGFILE" ]; then
    parsed_files=$(cat "$IMGDATA_LOGFILE" | awk -F',' '{print $3}')
fi

echo "parsing files..." 1>&2
find . -type f -iname '*.jp*g' | parallel parse_file
# for imgfile in $(find . -type f -iname '*.jp*g' -printf "%p\n"); do
#     if [ -e "$imgfile" ]; then
#         img_filepath_absolute=$(readlink -e "$imgfile")
#
#         # exclude files that have already been parsed
#         if [[ `echo $parsed_files | grep -c "$img_filepath_absolute"` -gt 0 ]]; then
#             continue
#         fi
#
#         img_data_checksum=$(exiftool "$img_filepath_absolute" -all= -o - -b | md5sum | awk '{ print $1}')
#         img_metadata_checksum=$(exiftool "$img_filepath_absolute" -x Directory -x FileName -x FileAccessDate -x FileModifyDate -x FileInodeChangeDate | md5sum | awk '{ print $1}')
#         img_datetimeoriginal=$(exiftool -b -DateTimeOriginal "$img_filepath_absolute" 2> /dev/null)
#         img_createdate=$(exiftool -b -CreateDate "$img_filepath_absolute" 2> /dev/null)
#         img_filesize=$(exiftool -b -FileSize "$img_filepath_absolute" 2> /dev/null)
#         echo $img_data_checksum,$img_metadata_checksum,$img_filepath_absolute,$img_datetimeoriginal,$img_createdate,$img_filesize >> "$IMGDATA_LOGFILE"
#     else
#         echo File \"$imgfile\" does not exist 1>&2
#     fi
# done
