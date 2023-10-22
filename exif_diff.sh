#!/usr/bin/env bash

#
# Simple script to diff two image files but ignoring some fields that will almost always be different
# Takes two positional arguments
#

if [ "$#" -ne "2" ]; then
  cat <<EOF
Usage:
  exif_diff.sh FILE1 FILE2
EOF
  exit 1
fi

diff <(exiftool "$1" -x Directory -x FileName -x FilePermissions -x FileAccessDate -x FileModifyDate -x FileInodeChangeDate | sort) \
     <(exiftool "$2" -x Directory -x FileName -x FilePermissions -x FileAccessDate -x FileModifyDate -x FileInodeChangeDate | sort)
