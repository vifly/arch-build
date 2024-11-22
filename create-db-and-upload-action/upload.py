import subprocess
import os

REPO_NAME = os.environ["repo_name"]
ROOT_PATH = os.environ["dest_path"]
CONFIG_NAME = os.environ.get("RCLONE_CONFIG_NAME", "")

if CONFIG_NAME == "":
    result = subprocess.run(["rclone", "listremotes"], capture_output=True)
    CONFIG_NAME = result.stdout.decode().split("\n")[0]
if not CONFIG_NAME.endswith(":"):
    CONFIG_NAME = CONFIG_NAME + ":"

if ROOT_PATH.startswith("/"):
    ROOT_PATH = ROOT_PATH[1:]

if __name__ == "__main__":
    r = subprocess.run(
        ["rclone", "copy", "./", f"{CONFIG_NAME}/{ROOT_PATH}", "--copy-links"],
        stderr=subprocess.PIPE,
    )
    if r.returncode != 0:
        print("Failed when copying to remote")
        print(r.stderr.decode())
        exit(0)
