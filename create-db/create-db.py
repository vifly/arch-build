#!/usr/bin/python3

import subprocess
import tarfile
import shutil
import os
from typing import NamedTuple
import pathlib
import pyalpm

REPO_NAME = os.environ["repo_name"]
ROOT_PATH = os.environ["dest_path"]
CONFIG_NAME = os.environ.get("RCLONE_CONFIG_NAME", "")

if CONFIG_NAME == "":
    result = subprocess.run(["rclone", "listremotes"], capture_output=True, check=False)
    CONFIG_NAME = result.stdout.decode().split("\n")[0]
if not CONFIG_NAME.endswith(":"):
    CONFIG_NAME = CONFIG_NAME + ":"

if ROOT_PATH.startswith("/"):
    ROOT_PATH = ROOT_PATH[1:]

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


def rclone_download(name: str, dest_path: str = "./"):
    """Download file <name> from remote and save it to <dest_path>

    Args:
        name (str): the name of the files to download.
                    Fill empty string to download the whole directory.
        dest_path (str): the path to save the file.

    Exceptions:
        RuntimeError: If rclone fails, raise a RuntimeError containing the stderr of rclone.
    """
    r = subprocess.run(
        [
            "rclone",
            "copy",
            f"{CONFIG_NAME}/{ROOT_PATH}/{name}",
            dest_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode())


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


def remove_old_files(
    local_packages: list["PkgInfo"],
    remote_packages: list["PkgInfo"],
    old_packages: list["PkgInfo"],
):
    """Remove old files from the local repository.
    Args:
        local_packages (list["PkgInfo"]): A list contains all local packages info.
        remote_packages (list["PkgInfo"]): A list contains all remote packages info.
        old_packages (list["PkgInfo"]): A list contains all old packages info.

    Returns:
        None
    """
    local_files = [i.filename for i in local_packages]
    remote_files = [i.filename for i in remote_packages]
    old_files = [i.filename for i in old_packages]
    for r in remote_files:
        if r in local_files or ".db" in r or ".files" in r or r in old_files:
            print("Removing file:", r)
            pathlib.Path(r).unlink()


def main():
    """The main function."""
    print("::group::Creating temporary directory", flush=True)
    TMP_DIR.mkdir(exist_ok=True)
    for pkg in pathlib.Path().glob("./*.tar.zst"):
        r = subprocess.run(
            ["repo-add", str(TMP_DIR / "local_tmp.db.tar.gz"), str(pkg)],
            stderr=subprocess.STDOUT,
            check=False,
        )
        pkg.copy(TMP_DIR / pkg.name)
    print("::endgroup::")
    r = subprocess.run(
        ["rclone", "size", f"{CONFIG_NAME}/{ROOT_PATH}/{REPO_NAME}.db.tar.gz"],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        check=False,
    )
    remote_packages = None
    if r.returncode != 0 or "Total size: 0" in r.stdout.decode():
        print("Remote database file is not exist!")
        print(
            "If you are running this script for the first time, you can ignore this error."
        )
        print(r.stderr.decode())
        remote_packages = []
    else:
        rclone_download(f"{REPO_NAME}.db.tar.gz", str(TMP_DIR))
        remote_packages = get_pkg_infos(str(TMP_DIR / f"{REPO_NAME}.db.tar.gz"))
    local_packages = get_pkg_infos(str(TMP_DIR / "local_tmp.db.tar.gz"))

    old_packages = get_old_packages(local_packages, remote_packages)

    print("::group::Download missing files", flush=True)
    r = subprocess.run(
        [
            "rclone",
            "copy",
            f"{CONFIG_NAME}/{ROOT_PATH}/",
            "./",
            "--include",
            "*.tar.zst",
        ],
        stderr=subprocess.STDOUT,
        check=True,
    )
    print("::endgroup::")

    print("::group::Removing unused files", flush=True)
    remove_old_files(local_packages, remote_packages, old_packages)
    print("::endgroup::")

    print("::group::Adding new packages", flush=True)
    for pkg in TMP_DIR.glob("./*.tar.zst"):
        pkg.copy(pkg.name)

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
