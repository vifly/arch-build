#!/bin/bash
set -e

init_path=$PWD
mkdir -p /tmp/repo/
mkdir upload_packages
find $package_path -type f -name "*.tar.zst" -exec cp {} ./upload_packages/ \;
if [[ -d "/tmp/repo/old" ]]; then
    rm -rf /tmp/repo/old
fi
cp -r $repo_path  /tmp/repo/old

echo "::group::Importing GPG key"
if [ ! -z "$gpg_key" ]; then
    echo "$gpg_key" | gpg --import
fi
echo "::endgroup::"

pushd upload_packages || exit 1

python3 $init_path/create-db/create-db.py

popd

if [[ -d "$output_path" ]]; then
    rm -rf $output_path/*
else
    mkdir -p $output_path
fi

cp -r upload_packages/* $output_path/

echo "::group::Cleaning up"
rm -rf /tmp/repo
rm -rf upload_packages
echo "::endgroup::"