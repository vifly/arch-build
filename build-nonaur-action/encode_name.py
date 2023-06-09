#!/usr/bin/python3

import os
from glob import glob
from base64 import urlsafe_b64encode, urlsafe_b64decode


names = glob("./*.tar.zst")
for name in names:
    new_name = name.removesuffix(".tar.zst")
    new_name = new_name.replace(":", "-colon-")
    os.rename(name, new_name + ".tar.zst")
