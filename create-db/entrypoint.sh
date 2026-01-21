#!/bin/bash
set -e

init_path=$PWD

echo "::group::Importing GPG key"
if [ ! -z "$gpg_key" ]; then
    if [[ -d ${HOME}/.gnupg ]]; then
        rm -rf ${HOME}/.gnupg
    fi
    echo "$gpg_key" | gpg --import
fi
echo "::endgroup::"

echo "::group::Creating Output directory"
if [ -d "$output_path" ]; then
    rm -rf "$output_path"
fi
mkdir -p "$output_path"
echo "::endgroup::"

echo "::group::Copying packages to output directory"
find "$package_path" -name "*.tar.zst" -exec cp {} "$output_path" \;
find "$package_path" -name "*.tar.zst.sig" -exec cp {} "$output_path" \;
echo "::endgroup::"

echo "::group::Signing packages"
for pkg in "$output_path"/*.tar.zst; do
    # Only sign if signature does not already exist
    if [ ! -f "${pkg}.sig" ]; then
        gpg --detach-sig --yes "$pkg"
    fi
done
echo "::endgroup::"

echo "::group::Adding packages to repo"
for pkg in "$output_path"/*.tar.zst; do
    repo-add --verify --sign "$output_path/$repo_name.db.tar.gz" "$pkg"
done
echo "::endgroup::"
