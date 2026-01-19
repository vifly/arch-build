#!/bin/bash
set -e

init_path=$PWD
mkdir upload_packages
find $local_path -type f -name "*.tar.zst" -exec cp {} ./upload_packages/ \;
find $local_path -type f -name "*.tar.gz" -exec cp {} ./upload_packages/ \;
find $local_path -type f -name "*.sig" -exec cp {} ./upload_packages/ \;
find $local_path -type f -name "*.db" -exec cp {} ./upload_packages/ \;
find $local_path -type f -name "*.files" -exec cp {} ./upload_packages/ \;

echo "$RCLONE_CONFIG_NAME"

if [ ! -f ~/.config/rclone/rclone.conf ]; then
    mkdir --parents ~/.config/rclone
    echo "$RCLONE_CONFIG_CONTENT" >>~/.config/rclone/rclone.conf
fi

cd upload_packages

echo "::group::Uploading to remote"

CONFIG_NAME="${RCLONE_CONFIG_NAME:-}"

if [ -z "$CONFIG_NAME" ]; then
    CONFIG_NAME=$(rclone listremotes | head -n 1)
fi

if [[ "$CONFIG_NAME" != *":" ]]; then
    CONFIG_NAME="${CONFIG_NAME}:"
fi

if [[ "$dest_path" == /* ]]; then
    dest_path="${dest_path:1}"
fi

# Sync using rclone
rclone sync ./ "${CONFIG_NAME}/${dest_path}" 

echo "::endgroup::"
