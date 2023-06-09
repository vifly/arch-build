#!/usr/bin/python3

import os
from glob import glob


names = glob("./*.tar.zst")
for name in names:
    new_name = name.removesuffix(".tar.zst")
    new_name = new_name.replace("-colon-", ":")
    os.rename(name, new_name + ".tar.zst")
