#! /usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=expression-not-assigned,line-too-long
"""Visit folder tree of some binary repository management system and report statistics."""
import datetime as dti
import hashlib
import os
import pathlib
import subprocess
import sys

DEBUG_VAR = "AG_DEBUG"
DEBUG = os.getenv(DEBUG_VAR)

ENCODING = "utf-8"
ENCODING_ERRORS_POLICY = "ignore"

BRM_HASH_POLICY_DEFAULT = "sha256"
BRM_HASH_POLICY_LEGACY = "sha1"
BRM_HASH_POLICIES_KNOWN = (BRM_HASH_POLICY_DEFAULT, BRM_HASH_POLICY_LEGACY)

BRM_FS_ROOT = "BRM_FS_ROOT"
brm_fs_root = os.getenv(BRM_FS_ROOT, "")
if not brm_fs_root:
    raise RuntimeError(
        f"Please set {BRM_FS_ROOT} to the root of the file system storage like /opt/brm/data/filestore/"
    )

BRM_HASH_POLICY = "BRM_HASH_POLICY"
brm_hash_policy = os.getenv(BRM_HASH_POLICY, BRM_HASH_POLICY_DEFAULT)
if brm_hash_policy not in BRM_HASH_POLICIES_KNOWN:
    raise RuntimeError(
        f"Please set {BRM_HASH_POLICY} to a known hash policy in ({', '.join(BRM_HASH_POLICIES_KNOWN)})"
    )

TS_FORMAT = "%Y-%m-%d %H:%M:%S"
GIGA = 2 << (30 - 1)
BUFFER_BYTES = 2 << 15


def by_name(text, hash_length):
    """Fast and shallow hash rep validity probe."""
    hash_rep_length, base = hash_length, 16
    if len(text) != hash_rep_length:
        return False
    try:
        _ = int(text, base)
    except ValueError:
        return False
    return True


def possible_hash(text, hash_policy=BRM_HASH_POLICY_DEFAULT):
    """Fast and shallow hash rep validity probe."""
    probe = {
        BRM_HASH_POLICY_DEFAULT: 64,
        "sha1": 40,
    }
    return by_name(text, probe[hash_policy])


def naive_timestamp(timestamp=None):
    """Logging helper."""
    if timestamp:
        return timestamp.strftime(TS_FORMAT)
    return dti.datetime.now().strftime(TS_FORMAT)


def walk_hashed_files(base_path):
    """Visit the files in the folders below base path."""
    for data_folder in base_path.iterdir():
        for file_path in data_folder.iterdir():
            yield file_path


def hashes(path_string, algorithms=None):
    """Yield hashes per algorithms of path."""
    if algorithms is None:
        algorithms = {BRM_HASH_POLICY_DEFAULT: hashlib.sha256}
    for key in algorithms:
        if key not in BRM_HASH_POLICIES_KNOWN:
            raise ValueError("hashes received unexpected algorithm key.")

    path = pathlib.Path(path_string)
    if not path.is_file():
        raise IOError("path is no file.")

    accumulator = {k: f() for k, f in algorithms.items()}
    with open(path, "rb") as in_file:
        for byte_block in iter(lambda in_f=in_file: in_f.read(BUFFER_BYTES), b""):
            for k in algorithms:
                accumulator[k].update(byte_block)

    return {k: f.hexdigest() for k, f in accumulator.items()}


def file_metrics(file_path):
    """Retrieve the size in bytes, as well as the create and last modified times for file path."""
    f_stat = file_path.stat()
    return f_stat.st_size, f_stat.st_ctime, f_stat.st_mtime


def mime_type(file_path):
    """Either yield mime type from find command without file name in result or artichoke/growth"""
    find_type = ["file", "--mime", file_path]
    try:
        output = subprocess.check_output(find_type, stderr=subprocess.STDOUT).decode()
        if not output.strip().endswith('(No such file or directory)'):
            return output.strip().split(":", 1)[1].strip()
    except subprocess.CalledProcessError:
        pass  # for now
    return 'artichoke/growth'


def main(argv=None):
    """Drive the tree visitor."""
    argv = argv if argv else sys.argv[1:]
    if argv:
        print("ERROR no arguments expected.", file=sys.stderr)
        return 2

    print(f"Job visiting file store starts at {naive_timestamp()}", file=sys.stderr)
    found, found_bytes, total = 0, 0, 0
    for file_path in walk_hashed_files(pathlib.Path(brm_fs_root)):
        total += 1
        DEBUG and print("=" * 80, file=sys.stderr)
        DEBUG and print(f"Processing {file_path} ...", file=sys.stderr)
        if file_path.is_file() and possible_hash(file_path.name, brm_hash_policy):
            found += 1
            print(f"{file_path.name}", end="")
            size_bytes, c_time, m_time = file_metrics(file_path)
            found_bytes += size_bytes
            print(f",{size_bytes},{c_time},{m_time}", end="")
            file_type = mime_type(file_path)
            print(f",'{file_type}'")
    print(f"Found {found} and ignored {total-found} artifacts below {brm_fs_root}", file=sys.stderr)
    print(f"Total size in files is {found_bytes/GIGA:.2f} Gigabytes ({found_bytes} bytes)", file=sys.stderr)
    print(f"Job visiting file store finished at {naive_timestamp()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
