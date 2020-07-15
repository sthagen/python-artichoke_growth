#! /usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
"""Visit folder tree of some binary repository management system and report statistics."""
import datetime as dti
import os
import pathlib
import sys
import time
from typing import Any, Dict, Generator, List, Union

DEBUG_VAR = "AG_DEBUG"
DEBUG = os.getenv(DEBUG_VAR)

ENCODING = "utf-8"
ENCODING_ERRORS_POLICY = "ignore"

BRM_FS_ROOT = "BRM_FS_ROOT"
brm_fs_root = os.getenv(BRM_FS_ROOT, "")
if not brm_fs_root:
    raise RuntimeError(
        f"Please set {BRM_FS_ROOT} to the root of the file system storage like /opt/brm/data/filestore/")

TS_FORMAT = "%Y-%m-%d %H:%M:%S"
FILE_TS_FORMAT = "%Y%m%dT%H%M%S"
A_TS = dti.datetime.now()
TS_THIS_YEAR = A_TS.strftime("%Y")
TS_THIS_MONTH = A_TS.strftime("%Y-%m")
TS_M_NOW = TS_THIS_MONTH[-2:]
A_TIME = time.mktime(A_TS.timetuple())
M_TIME = A_TIME


def naive_timestamp(timestamp=None):
    """Logging helper."""
    if timestamp:
        return timestamp.strftime(TS_FORMAT)
    return dti.datetime.now().strftime(TS_FORMAT)


def main(argv=None):
    """Drive the tree visitor."""
    argv = argv if argv else sys.argv[1:]
    if argv:
        print("ERROR no arguments expected.")
        return 2

    print(f"Job visiting binary repository manager file store root ({brm_fs_root}) starts at {naive_timestamp()}")
    base_path = pathlib.Path(brm_fs_root)
    print(f"#Recursing into {base_path} ...")
    print(f"#1. level ==> prefix ...")
    prefixes = [prefix for prefix in base_path.iterdir()]
    DEBUG and print(f"    got: {prefixes}")

    print(f"#Visiting {len(prefixes)} data folders for files matching their sha1 checksum ...")
    file_paths = []
    for data_folder in prefixes:
        for file_path in data_folder.iterdir():
            file_paths.append(file_path)

    print(f"#Processing the {len(file_paths)} files matching their sha1 checksum ...")
    for file_path in file_paths:
        DEBUG and print("=" * 80)
        DEBUG and print(f"Processing {file_path} ...")

    print(f"Job finished at {naive_timestamp()}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
