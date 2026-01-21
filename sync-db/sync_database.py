#!/usr/bin/python3

import tarfile
import shutil
import os
from typing import NamedTuple
import pathlib
import sys
import pyalpm

REPO_NAME = os.environ["repo_name"]

SRC_PATH = pathlib.Path(os.environ.get("src_repo_path", "./src_repo"))
DEST_PATH = pathlib.Path(os.environ.get("dest_repo_path", "./dest_repo"))
OUTPUT_PATH = pathlib.Path(os.environ.get("output_path", "./new_packages"))
TMP_DIR = pathlib.Path("/tmp/repo")


class PkgInfo(NamedTuple):
    """The package info.

    Members:
        filename (str): The package file name.
        pkgname (str): The package name.
        version (str): The package version.
    """

    filename: str
    pkgname: str
    version: str


def get_pkg_infos(file_path: str) -> list["PkgInfo"]:
    """Get packages info from "*.db.tar.gz".

    Args:
        file_path (str): DB file path.

    Returns:
        list["PkgInfo"]: A list contains all packages info.
    """
    with tarfile.open(file_path) as f:
        f.extractall(str(TMP_DIR / "extractdb"))

    pkg_infos = []
    pkgs = TMP_DIR.glob("extractdb/*/desc")
    for pkg_desc in pkgs:
        with pkg_desc.open("r") as f:
            lines = f.readlines()
        lines = [i.strip() for i in lines]
        filename = ""
        pkgname = ""
        version = ""
        for index, line in enumerate(lines):
            if "%FILENAME%" in line:
                filename = lines[index + 1]
            if "%NAME%" in line:
                pkgname = lines[index + 1]
            if "%VERSION%" in line:
                version = lines[index + 1]
        if pkgname != "" and version != "" and filename != "":
            pkg_infos.append(
                PkgInfo(filename=filename, pkgname=pkgname, version=version)
            )

    shutil.rmtree(str(TMP_DIR / "extractdb"))

    return pkg_infos


def get_old_packages(
    local_packages: list["PkgInfo"], dest_packages: list["PkgInfo"]
) -> list["PkgInfo"]:
    """Get old packages
    Args:
        local_packages (list["PkgInfo"]): A list contains all local packages info.
        dest_packages (list["PkgInfo"]): A list contains all destination packages info.

    Returns:
        list["PkgInfo"]: A list contains all old packages info.
    """
    old_packages = []
    for l in local_packages:
        for r in dest_packages:
            if l.pkgname == r.pkgname:
                res = pyalpm.vercmp(l.version, r.version)
                if res >= 0:
                    # also replace old package with new one if version is same
                    old_packages.append(r)

    return old_packages


def copy_missing_packages(
    local_packages: list["PkgInfo"],
    old_packages: list["PkgInfo"],
):
    """Copy missing packages from the remote repository.
    Args:
        local_packages (list["PkgInfo"]): A list contains all local packages info.
        old_packages (list["PkgInfo"]): A list contains all old packages info.

    Returns:
        None
    """
    local_files = [i.filename for i in local_packages]
    old_files = [i.filename for i in old_packages]
    print("Local files:", local_files)
    print("Old files:", old_files)
    for pkg in DEST_PATH.glob("*.tar.zst"):
        if pkg.name in old_files:
            continue
        print("Copying missing package:", pkg.name)
        pkg.copy_into(OUTPUT_PATH)
        DEST_PATH.joinpath(pkg.name + ".sig").copy_into(OUTPUT_PATH)

def copy_new_packages(
    src_packages: list["PkgInfo"],
    old_packages: list["PkgInfo"],
    dest_packages: list["PkgInfo"],
):
    """Copy new packages from the source repository.
    Args:
        src_packages (list["PkgInfo"]): A list contains all packages info in src repo.
        old_packages (list["PkgInfo"]): A list contains all old packages info.
        dest_packages (list["PkgInfo"]): A list contains all packages info in dest repo.
    """
    old_files = [i.pkgname for i in old_packages]
    dest_files = [i.pkgname for i in dest_packages]
    new_files = [
        i.filename
        for i in src_packages
        if i.pkgname in old_files or i.pkgname not in dest_files
    ]

    for pkg in new_files:
        print("Copying new package:", pkg)
        SRC_PATH.joinpath(pkg).copy_into(OUTPUT_PATH)
        SRC_PATH.joinpath(pkg + ".sig").copy_into(OUTPUT_PATH)


def main():
    """The main function."""
    if OUTPUT_PATH.exists():
        shutil.rmtree(OUTPUT_PATH)
    OUTPUT_PATH.mkdir(exist_ok=True)
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)

    TMP_DIR.mkdir(exist_ok=True)

    dest_packages = None
    if not DEST_PATH.joinpath(f"{REPO_NAME}.db.tar.gz").exists():
        print("Destination database file is not exist!")
        print(
            "If you are running this script for the first time, you can ignore this error."
        )
        dest_packages = []
    else:
        dest_packages = get_pkg_infos(str(DEST_PATH / f"{REPO_NAME}.db.tar.gz"))
    local_packages = get_pkg_infos(str(SRC_PATH / f"{REPO_NAME}.db.tar.gz"))

    old_packages = get_old_packages(local_packages, dest_packages)

    print("::group::Copying missing packages")
    copy_missing_packages(local_packages, old_packages)
    print("::endgroup::")

    print("::group::Copying new packages")
    copy_new_packages(local_packages, old_packages, dest_packages)
    print("::endgroup::")

if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print("File not found:", e.filename)
        print("::endgroup::")
        sys.exit(1)
    except Exception as e:
        print("An unexpected error occurred:", str(e))
        print("::endgroup::")
        sys.exit(1)
    else:
        print("Repository synchronization completed successfully.")
    finally:
        shutil.rmtree(str(TMP_DIR), ignore_errors=True)
