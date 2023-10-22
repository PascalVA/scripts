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
#           printf "%-34s " "FILE: $file"
#           printf "%-36s " "CREATE_DATE: $create_date"
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
#               echo "MOVED: $moved"
            fi
        else
#           printf "%-34s " "FILE: $file"
#           printf "%-36s " "CREATE_DATE: $create_date"
#           echo "ERROR: SKIPPED MISSING DATE"
            mkdir -p MISSING
            mv "$file" MISSING/
        fi
    fi
done

#filepath=$(readlink -f "$1")
#files=$(find "$filepath" -mindepth 1 -maxdepth 1 -type f)

#for file in $files; do
#    res=$(exiftool -b -DateTimeOriginal "$file" 2>/dev/null)
#    if [ "$res" ] && [ "$res" != "$EMPTY_DATE_FORMAT" ] && [ "$res" != "-" ]; then
#        exiftool '-FileName<DateTimeOriginal'   \
#           -d %Y/%m/%Y%m%d_%H%M%S%%-c.%%e \
#           -overwrite_original            \
#           -a "-ImageDescription=$imagedescripion" "$file" \
#           -v 2> /dev/null
#        exit 0
#    fi
#
#    dirname=$(dirname "$file")/missing_tag/
#    if [ ! -d "$dirname" ]; then
#        mkdir "$dirname"
#    fi
#    mv "$file" "$dirname"
#
#done
