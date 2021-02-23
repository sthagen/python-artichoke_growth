#! /usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=expression-not-assigned,line-too-long
"""Visit folder tree of some binary repository management system and report statistics."""
import copy
import csv
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

BRM_PROXY_DB = "BRM_PROXY_DB"
brm_proxy_db = os.getenv(BRM_PROXY_DB, "")
if not brm_proxy_db:
    raise RuntimeError(
        f"Please set {BRM_PROXY_DB} as the path to the file system proxy like some/path/brm_proxy_db.csv"
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


def load(proxy_db_path):
    """Load the proxy data as dict."""
    with open(proxy_db_path, newline='') as handle:
        return {row[0]: row[1:] for row in csv.reader(handle, delimiter=',', quotechar='|')}


def elf_hash(some_bytes: bytes):
    """The ELF hash.

    unsigned long ElfHash(const unsigned char *s) {
        unsigned long h = 0, high;
        while (*s) {
            h = (h << 4) + *s++;
            if (high = h & 0xF0000000)
                h ^= high >> 24;
            h &= ~high;
        }
        return h;
    }
    """
    h = 0
    for s in some_bytes:
        h = (h << 4) + s
        high = h & 0xF0000000
        if high:
            h ^= (high >> 24)
        h &= ~high
    return h


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
    """Retrieve the file stats."""
    return file_path.stat()


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


def serialize(storage_hash, f_stat, fps, file_type):
    """x"""
    size_bytes, c_time, m_time = f_stat.st_size, f_stat.st_ctime, f_stat.st_mtime
    return f"{','.join((storage_hash, str(size_bytes), str(c_time), str(m_time), fps, file_type))}\n"


def main(argv=None):
    """Drive the tree visitor."""
    argv = argv if argv else sys.argv[1:]
    if argv:
        print("ERROR no arguments expected.", file=sys.stderr)
        return 2

    proxy = load(brm_proxy_db)
    keep = copy.deepcopy(proxy)

    algorithms = None
    if brm_hash_policy != BRM_HASH_POLICY_DEFAULT:
        algorithms = {
            BRM_HASH_POLICY_DEFAULT: hashlib.sha256,
            BRM_HASH_POLICY_LEGACY: hashlib.sha1,
        }
        print(f"Warning: Store seems to use ({BRM_HASH_POLICY_LEGACY}) - adding ({BRM_HASH_POLICY_DEFAULT})")

    print(f"Job visiting file store starts at {naive_timestamp()}", file=sys.stderr)
    found, found_bytes, total = 0, 0, 0
    with open("added.csv", "wt") as csv_handle:
        for file_path in walk_hashed_files(pathlib.Path(brm_fs_root)):
            total += 1
            DEBUG and print("=" * 80, file=sys.stderr)
            DEBUG and print(f"Processing {file_path} ...", file=sys.stderr)
            storage_hash = file_path.name
            if file_path.is_file() and storage_hash not in proxy and possible_hash(storage_hash, brm_hash_policy):
                found += 1
                fingerprints = hashes(file_path, algorithms)
                fps = f'{",".join([f"{k}:{v}" for k, v in fingerprints.items()])}'
                f_stat = file_metrics(file_path)
                found_bytes += f_stat.st_size
                entry = (storage_hash, f_stat, fps, mime_type(file_path))
                csv_handle.write(serialize(*entry))
                keep[storage_hash] = (storage_hash, f_stat, fps, mime_type(file_path))
            if storage_hash in proxy:
                del proxy[storage_hash]  # After processing proxy holds gone entries (tombstones)

    gone = len(proxy)
    with open("gone.csv", "wt") as csv_handle:
        for k, v in proxy.items():
            csv_handle.write(serialize(k, *v))

    kept = len(keep)
    with open("proxy.csv", "wt") as csv_handle:
        for k, v in keep.items():
            csv_handle.write(serialize(k, *v))

    print(f"Found {found} and ignored {total-found} artifacts below {brm_fs_root}", file=sys.stderr)
    print(f"Identified {gone} tombstones below {brm_fs_root}", file=sys.stderr)
    print(f"Updated Proxy has {kept} entries below {brm_fs_root}", file=sys.stderr)
    print(f"Total size in files is {found_bytes/GIGA:.2f} Gigabytes ({found_bytes} bytes)", file=sys.stderr)
    print(f"Job visiting file store finished at {naive_timestamp()}", file=sys.stderr)
    return 0



if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
