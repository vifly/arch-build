#!/bin/bash
set -e

init_path=$PWD
mkdir upload_packages
cp $local_path/*/*/*.tar.zst ./upload_packages/

if [ ! -f ~/.config/rclone/rclone.conf ]; then
    mkdir --parents ~/.config/rclone
    echo "[onedrive]" >> ~/.config/rclone/rclone.conf
    echo "type = onedrive" >> ~/.config/rclone/rclone.conf

    echo "client_id=$RCLONE_ONEDRIVE_CLIENT_ID" >> ~/.config/rclone/rclone.conf
    echo "client_secret=$RCLONE_ONEDRIVE_CLIENT_SECRET" >> ~/.config/rclone/rclone.conf
    echo "region=$RCLONE_ONEDRIVE_REGION" >> ~/.config/rclone/rclone.conf
    echo "drive_type=$RCLONE_ONEDRIVE_DRIVE_TYPE" >> ~/.config/rclone/rclone.conf
    echo "token=$RCLONE_ONEDRIVE_TOKEN" >> ~/.config/rclone/rclone.conf
    echo "drive_id=$RCLONE_ONEDRIVE_DRIVE_ID" >> ~/.config/rclone/rclone.conf
fi

if [ ! -z "$gpg_key" ]; then
    echo "$gpg_key" | gpg --import
fi

cd upload_packages || exit 1

repo-add "./${repo_name:?}.db.tar.gz" ./*.tar.zst
python3 $init_path/create-db-and-upload-action/sync.py
rm "./${repo_name:?}.db.tar.gz"
rm "./${repo_name:?}.files.tar.gz"

if [ ! -z "$gpg_key" ]; then
    packages=( "*.tar.zst" )
    for name in $packages
    do
        gpg --detach-sig --yes $name
    done
    repo-add --verify --sign "./${repo_name:?}.db.tar.gz" ./*.tar.zst
fi
rclone copy ./ "onedrive:${dest_path:?}" --copy-links
