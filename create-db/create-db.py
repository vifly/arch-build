#!/usr/bin/python3

import subprocess
import tarfile
import shutil
import os
from typing import NamedTuple
import pathlib
import pyalpm

REPO_NAME = os.environ["repo_name"]

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
    local_packages: list["PkgInfo"], remote_packages: list["PkgInfo"]
) -> list["PkgInfo"]:
    """Get old packages
    Args:
        local_packages (list["PkgInfo"]): A list contains all local packages info.
        remote_packages (list["PkgInfo"]): A list contains all remote packages info.

    Returns:
        list["PkgInfo"]: A list contains all old packages info.
    """
    old_packages = []
    for l in local_packages:
        for r in remote_packages:
            if l.pkgname == r.pkgname:
                res = pyalpm.vercmp(l.version, r.version)
                if res > 0:
                    old_packages.append(r)

    return old_packages


def copy_missing_packages(
    local_packages: list["PkgInfo"],
    old_packages: list["PkgInfo"],
):
    """Copy missing packages from the remote repository.
    Args:
        local_packages (list["PkgInfo"]): A list contains all local packages info.
        remote_packages (list["PkgInfo"]): A list contains all remote packages info.
        old_packages (list["PkgInfo"]): A list contains all old packages info.

    Returns:
        None
    """
    local_files = [i.filename for i in local_packages]
    old_files = [i.filename for i in old_packages]
    print("Local files:", local_files)
    print("Old files:", old_files)
    for pkg in TMP_DIR.joinpath("old").glob("./*.tar.zst"):
        if pkg.name in local_files:
            continue
        if pkg.name in old_files:
            continue
        print("Copying missing package:", pkg.name)
        pkg.copy_into("./")
        TMP_DIR.joinpath("old").joinpath(pkg.name + ".sig").copy_into("./")


def main():
    """The main function."""
    print("::group::Creating temporary directory", flush=True)
    TMP_DIR.mkdir(exist_ok=True)
    for pkg in pathlib.Path().glob("./*.tar.zst"):
        subprocess.run(
            ["repo-add", str(TMP_DIR / "local_tmp.db.tar.gz"), str(pkg)],
            stderr=subprocess.STDOUT,
            check=True,
        )
    print("::endgroup::")

    remote_packages = None
    if not TMP_DIR.joinpath(f"old/{REPO_NAME}.db.tar.gz").exists():
        print("Remote database file is not exist!")
        print(
            "If you are running this script for the first time, you can ignore this error."
        )
        remote_packages = []
    else:
        remote_packages = get_pkg_infos(str(TMP_DIR / "old" / f"{REPO_NAME}.db.tar.gz"))
    local_packages = get_pkg_infos(str(TMP_DIR / "local_tmp.db.tar.gz"))

    old_packages = get_old_packages(local_packages, remote_packages)

    print("::group::Getting missing packages", flush=True)
    copy_missing_packages(local_packages, old_packages)
    print("::endgroup::")

    print("::group::Signing packages", flush=True)
    for pkg in local_packages:
        subprocess.run(
            ["gpg", "--detach-sig", "--yes", str(pkg.filename)],
            stderr=subprocess.STDOUT,
            check=False,
        )
    print("::endgroup::")

    print("::group::Adding packages to repo", flush=True)
    for pkg in pathlib.Path().glob("./*.tar.zst"):
        subprocess.run(
            ["repo-add", "--verify", "--sign", f"{REPO_NAME}.db.tar.gz", str(pkg)],
            stderr=subprocess.STDOUT,
            check=True,
        )
    print("::endgroup::")


if __name__ == "__main__":
    main()
