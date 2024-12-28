#!/bin/bash
IFS=''
#set -xe

# This script sorts pictures in a YEAR/MONTH/FILE directory
# structure. The filename of the file will have the timestamp
# and a trailing ordinal number for a suffix if there are any duplicates

EMPTY_DATE_FORMAT="0000:00:00 00:00:00"

for file in $@; do
    if [ -f "$file" ]; then

        file_type=$(exiftool -b -FileTypeExtension "$file")

        if [ "$file_type" == "JPG" ]; then
            create_date=$(exiftool -b -DateTimeOriginal "$file" 2>/dev/null)
        else
            create_date=$(exiftool -b -TrackCreateDate "$file" 2>/dev/null)
        fi
        if [ "$create_date" ] && [ "$create_date" != "$EMPTY_DATE_FORMAT" ] && [ "$create_date" != "-" ]; then
            if [ "$file_type" == "JPG" ]; then
                output=$(exiftool -v '-FileName<DateTimeOriginal' -d %Y/%m/%Y%m%d_%H%M%S%%-c.%%e -overwrite_original "$file" 2>/dev/null)
            else
                output=$(exiftool -v '-FileName<TrackCreateDate' -d %Y/%m/%Y%m%d_%H%M%S%%-c.%%e -overwrite_original "$file" 2>/dev/null)
            fi

            moved_line=$(echo $output | grep -- '-->')
            if [ -z moved_line ]; then
                echo -e "\n  ERROR:$output\n"
            else
                moved=$(echo $moved_line | sed "s/[^']*\('[^']*'\\s-->\\s'[^']*'\).*/\\1/g")
            fi
        else
            mkdir -p MISSING
            mv "$file" MISSING/
        fi
    fi
done
