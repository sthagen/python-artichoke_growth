#! /usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=expression-not-assigned,line-too-long
"""Visit folder tree of some binary repository management system and report statistics."""
import datetime as dti
import os
import pathlib
import sys
import time

import magic  # type: ignore

DEBUG_VAR = "AG_DEBUG"
DEBUG = os.getenv(DEBUG_VAR)

ENCODING = "utf-8"
ENCODING_ERRORS_POLICY = "ignore"

BRM_FS_ROOT = "BRM_FS_ROOT"
brm_fs_root = os.getenv(BRM_FS_ROOT, "")
if not brm_fs_root:
    raise RuntimeError(
        f"Please set {BRM_FS_ROOT} to the root of the file system storage like /opt/brm/data/filestore/"
    )

TS_FORMAT = "%Y-%m-%d %H:%M:%S"
FILE_TS_FORMAT = "%Y%m%dT%H%M%S"
A_TS = dti.datetime.now()
TS_THIS_YEAR = A_TS.strftime("%Y")
TS_THIS_MONTH = A_TS.strftime("%Y-%m")
TS_M_NOW = TS_THIS_MONTH[-2:]
A_TIME = time.mktime(A_TS.timetuple())
M_TIME = A_TIME


def possible_sha1(text):
    """Fast and shallow sha1 rep validity probe."""
    sha1_rep_length, base = 40, 16
    if len(text) != sha1_rep_length:
        return False
    try:
        _ = int(text, base)
    except ValueError:
        return False
    return True


def naive_timestamp(timestamp=None):
    """Logging helper."""
    if timestamp:
        return timestamp.strftime(TS_FORMAT)
    return dti.datetime.now().strftime(TS_FORMAT)


def main(argv=None):
    """Drive the tree visitor."""
    peek_buffer_bytes = 2 << 10
    argv = argv if argv else sys.argv[1:]
    if argv:
        print("ERROR no arguments expected.")
        return 2

    print(
        f"Job visiting binary repository manager file store root ({brm_fs_root}) starts at {naive_timestamp()}"
    )
    base_path = pathlib.Path(brm_fs_root)
    print(f"#Recursing into {base_path} ...")
    print("#1. level ==> prefix ...")
    prefixes = base_path.iterdir()
    DEBUG and print(f"    got: {prefixes}")
    print("#2. level ==> leaf --> prefix ...")
    prefix_leafs = [leaf for prefix in prefixes for leaf in prefix.iterdir()]
    DEBUG and print(f"    got: {prefix_leafs}")

    print(
        f"#Visiting {len(prefix_leafs)} data folders for files matching their sha1 checksum ..."
    )
    file_paths = []
    for data_folder in prefix_leafs:
        for file_path in data_folder.iterdir():
            file_paths.append(file_path)

    print(f"#Processing the {len(file_paths)} files matching their sha1 checksum ...")
    for file_path in file_paths:
        DEBUG and print("=" * 80)
        DEBUG and print(f"Processing {file_path} ...")
        if file_path.is_file() and possible_sha1(file_path.name):
            print(f"- {file_path} is file and possible sha1 hash", end="")
            size_bytes = file_path.stat().st_size
            print(f", size={size_bytes} bytes", end="")
            mime_type = magic.from_buffer(
                open("testdata/test.pdf").read(peek_buffer_bytes), mime=True
            )
            print(f", mime_type='{mime_type}'")

    print(f"Job finished at {naive_timestamp()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

