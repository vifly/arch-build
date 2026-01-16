#!/bin/bash
set -e

if [[ -d ${HOME}/.gnupg ]]; then
    rm -rf ${HOME}/.gnupg
fi

echo "::group::Importing GPG key"
if [ ! -z "$gpg_key" ]; then
    echo "$gpg_key" | gpg --import
fi
echo "::endgroup::"

init_path=$PWD
python3 $init_path/sync-db/sync_database.py