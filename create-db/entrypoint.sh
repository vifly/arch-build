#!/bin/bash
set -e

init_path=$PWD

echo "::group::Importing GPG key"
if [ ! -z "$gpg_key" ]; then
    echo "$gpg_key" | gpg --import
fi
echo "::endgroup::"

python3 $init_path/create-db/create_db.py