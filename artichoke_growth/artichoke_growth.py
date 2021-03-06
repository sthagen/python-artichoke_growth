#! /usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=expression-not-assigned,line-too-long
"""Visit folder tree of some binary repository management system and report statistics."""
import copy
import csv
import datetime as dti
import hashlib
import lzma
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

TS_FORMAT_HR = "%Y-%m-%d %H:%M:%S"
TS_FORMAT_DB = "%Y%m%dT%H%M%SZ"
GIGA = 2 << (30 - 1)
BUFFER_BYTES = 2 << 15

STORE_ROOT = "store"
STORE_PATH_ENTER = pathlib.Path(STORE_ROOT, "enter")
STORE_PATH_TOMBS = pathlib.Path(STORE_ROOT, "tombs")
STORE_PATH_PROXY = pathlib.Path(STORE_ROOT, "proxy")

XZ_FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": 7 | lzma.PRESET_EXTREME}]
XZ_EXT = ".xz"


def archive(stream, file_path):
    """Create .xz files for long term storage."""
    file_path = pathlib.Path(file_path)  # HACK A DID ACK
    if file_path.suffixes[-1] != XZ_EXT:
        file_path = file_path.with_suffix(file_path.suffix + XZ_EXT)
    with lzma.open(file_path, "w", check=lzma.CHECK_SHA256, filters=XZ_FILTERS) as f:
        for entry in stream:
            f.write(entry.encode(encoding=ENCODING, errors=ENCODING_ERRORS_POLICY))


def load(proxy_db_path):
    """Load the proxy data as dict."""
    file_path = pathlib.Path(proxy_db_path)  # HACK A DID ACK
    if file_path.suffixes[-1] == XZ_EXT:
        with lzma.open(file_path, mode='rt', encoding=ENCODING, errors=ENCODING_ERRORS_POLICY) as handle:
            return {row[0]: row[0:] for row in csv.reader(handle, delimiter=',', quotechar='|')}
    else:
        with open(proxy_db_path, newline='') as handle:
            return {row[0]: row[0:] for row in csv.reader(handle, delimiter=',', quotechar='|')}


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
        return timestamp.strftime(TS_FORMAT_HR)
    return dti.datetime.now().strftime(TS_FORMAT_HR)


def db_timestamp(timestamp=None):
    """Logging helper."""
    if timestamp:
        return timestamp.strftime(TS_FORMAT_DB)
    return dti.datetime.now().strftime(TS_FORMAT_DB)


def walk_hashed_files(base_path):
    """Visit the files in the folders below base path.
    Either:
    for data_folder in base_path.iterdir():
        for file_path in data_folder.iterdir():
            yield file_path
    or:
    for file_path in base_path.rglob('*/*'):
        yield file_path
    both return entries in different orders per platform.

    Implementer Note:
    -----------------
    This allocates a list (for sorting) - so be aware
    when operating on bucket stores with many entries ...
    """
    for file_path in sorted(base_path.rglob('*/*')):
        yield file_path


def elf_hash(some_bytes: bytes):
    """The ELF hash (Extremely Lossy Function - also used in ELF format).

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
    """x"""  # TODO(sthagen) round trip has become a mess - fix it
    size_bytes, c_time, m_time = f_stat.st_size, f_stat.st_ctime, f_stat.st_mtime
    return f"{','.join((storage_hash, str(size_bytes), str(c_time), str(m_time), fps, file_type))}\n"


def gen_out_stream(kind):
    """DRY"""
    for v in kind.values():
        yield f"{','.join(v)}\n"


def distribute_changes(enter, leave, keep, proxy, update):
    entered_bytes, ignored_bytes, updated_bytes, left_bytes = 0, 0, 0, 0
    for k, v in proxy.items():
        if k in update:
            ignored_bytes += int(v[1])
            keep[k] = copy.deepcopy(v)
        else:
            left_bytes += int(v[1])
            leave[k] = copy.deepcopy(v)
    updated_bytes += ignored_bytes
    for k, v in enter.items():
        entered_bytes += int(v[1])
        keep[k] = copy.deepcopy(v)
    updated_bytes += entered_bytes
    return entered_bytes, ignored_bytes, left_bytes, updated_bytes


def derive_proxy_paths(start_ts):
    added_db = pathlib.Path(STORE_PATH_ENTER, f"added-{db_timestamp(start_ts)}.csv")
    proxy_db = pathlib.Path(STORE_PATH_PROXY, f"proxy-{db_timestamp(start_ts)}.csv")
    gone_db = pathlib.Path(STORE_PATH_TOMBS, f"gone-{db_timestamp(start_ts)}.csv")
    pathlib.Path(STORE_PATH_ENTER).mkdir(parents=True, exist_ok=True)
    pathlib.Path(STORE_PATH_PROXY).mkdir(parents=True, exist_ok=True)
    pathlib.Path(STORE_PATH_TOMBS).mkdir(parents=True, exist_ok=True)
    return added_db, gone_db, proxy_db


def main(argv=None):
    """Drive the tree visitor."""
    argv = argv if argv else sys.argv[1:]
    if argv:
        print("ERROR no arguments expected.", file=sys.stderr)
        return 2

    brm_proxy_db_path = brm_proxy_db
    if brm_proxy_db == "AUTO":
        brm_proxy_db_path = tuple(reversed(sorted(STORE_PATH_PROXY.glob("proxy-*.csv.xz"))))[0]

    proxy = load(brm_proxy_db_path)
    previous = len(proxy)
    enter, update, leave = {}, set(), {}
    print(f"Read {previous} from {brm_proxy_db} artifacts below {brm_fs_root}", file=sys.stderr)

    algorithms = None
    if brm_hash_policy != BRM_HASH_POLICY_DEFAULT:
        algorithms = {
            BRM_HASH_POLICY_DEFAULT: hashlib.sha256,
            BRM_HASH_POLICY_LEGACY: hashlib.sha1,
        }
        print(f"Warning: Store seems to use ({BRM_HASH_POLICY_LEGACY}) - adding ({BRM_HASH_POLICY_DEFAULT})")

    start_ts = dti.datetime.now()

    print(f"Job visiting file store starts at {naive_timestamp(start_ts)}", file=sys.stderr)
    found_bytes, total = 0, 0
    for file_path in walk_hashed_files(pathlib.Path(brm_fs_root)):
        total += 1
        storage_hash = file_path.name
        if not file_path.is_file():
            continue
        if not possible_hash(storage_hash, brm_hash_policy):
            continue
        if storage_hash not in proxy:
            fingerprints = hashes(file_path, algorithms)
            fps = f'{",".join([f"{k}:{v}" for k, v in fingerprints.items()])}'
            f_stat = file_metrics(file_path)
            found_bytes += f_stat.st_size
            enter[storage_hash] = (storage_hash, str(f_stat.st_size), str(f_stat.st_ctime), str(f_stat.st_mtime), fps, mime_type(file_path))
        else:
            update.add(storage_hash)

    keep = {}
    entered_bytes, ignored_bytes, left_bytes, updated_bytes = distribute_changes(enter, leave, keep, proxy, update)

    added_db, gone_db, proxy_db = derive_proxy_paths(start_ts)

    entered, updated, left = len(enter), len(keep), len(leave)
    ignored = total-entered
    for db, kind in ((added_db, enter), (proxy_db, keep), (gone_db, leave)):
        archive(gen_out_stream(kind), db)

    print(f"Entered {entered} entries / {entered_bytes} bytes at {added_db} ", file=sys.stderr)
    print(f"Ignored {ignored} entries / {ignored_bytes} bytes for hashing", file=sys.stderr)
    print(f"Kept {updated} entries / {updated_bytes} bytes at {proxy_db}", file=sys.stderr)
    print(f"Removed {left} entries / {left_bytes} bytes at {gone_db}", file=sys.stderr)
    print(f"Total size in added files is {found_bytes/GIGA:.2f} Gigabytes ({found_bytes} bytes)", file=sys.stderr)
    print(f"Job visiting file store finished at {naive_timestamp()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
