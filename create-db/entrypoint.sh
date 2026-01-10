#!/bin/bash
set -e

init_path=$PWD
mkdir upload_packages
find $local_path -type f -name "*.tar.zst" -exec cp {} ./upload_packages/ \;

if [ ! -f ~/.config/rclone/rclone.conf ]; then
    mkdir --parents ~/.config/rclone
    echo "$RCLONE_CONFIG_CONTENT" >> ~/.config/rclone/rclone.conf
fi

if [ ! -z "$gpg_key" ]; then
    echo "$gpg_key" | gpg --import
fi

cd upload_packages || exit 1

python3 $init_path/create-db/create-db.py