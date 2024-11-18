#!/bin/bash
set -e

init_path=$PWD
mkdir upload_packages
find $local_path -type f -name "*.tar.zst" -exec cp {} ./upload_packages/ \;

echo "$RCLONE_CONFIG_NAME"

if [ ! -f ~/.config/rclone/rclone.conf ]; then
    mkdir --parents ~/.config/rclone
    echo "$RCLONE_CONFIG" >> ~/.config/rclone/rclone.conf
    cat "~/.config/rclone/rclone.conf"
fi

if [ ! -z "$gpg_key" ]; then
    echo "$gpg_key" | gpg --import
fi

cd upload_packages || exit 1

repo-add "./${repo_name:?}.db.tar.gz" ./*.tar.zst

echo "repo-add complete"

python3 $init_path/create-db-and-upload-action/sync.py 

echo "sync complete"

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
rclone copy ./ "${RCLONE_CONFIG_NAME}:${dest_path:?}" --copy-links
