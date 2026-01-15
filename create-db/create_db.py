#!/usr/bin/python3

import subprocess
import os
import pathlib
import shutil

REPO_NAME = os.environ["repo_name"]
OUTPUT_PATH = pathlib.Path(os.environ.get("output_path", "./repo"))
PACKAGE_PATH = pathlib.Path(os.environ.get("package_path", "./packages"))


def main():
    """The main function."""

    if OUTPUT_PATH.exists():
        shutil.rmtree(OUTPUT_PATH)
    OUTPUT_PATH.mkdir(exist_ok=True)

    print("::group::Creating Output directory", flush=True)
    OUTPUT_PATH.mkdir(exist_ok=True)
    print("::endgroup::")

    print("::group::Copying packages to output directory", flush=True)
    for pkg in PACKAGE_PATH.glob("./*.tar.zst"):
        pkg.copy_into(OUTPUT_PATH)
    print("::endgroup::")

    print("::group::Signing packages", flush=True)
    for pkg in OUTPUT_PATH.glob("./*.tar.zst"):
        subprocess.run(
            ["gpg", "--detach-sig", "--yes", str(pkg)],
            stderr=subprocess.STDOUT,
            check=False,
        )
    print("::endgroup::")

    print("::group::Adding packages to repo", flush=True)
    for pkg in OUTPUT_PATH.glob("./*.tar.zst"):
        subprocess.run(
            ["repo-add", str(OUTPUT_PATH / f"{REPO_NAME}.db.tar.gz"), str(pkg)],
            stderr=subprocess.STDOUT,
            check=True,
        )
    print("::endgroup::")


if __name__ == "__main__":
    main()
