# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring,unused-import,reimported
import os
import pathlib
import pytest  # type: ignore

prefix_store_data_root = pathlib.Path('tests', 'fixtures', 'prefix_store')
prefix_data_sha1 = pathlib.Path(prefix_store_data_root, 'sha1')
prefix_data_sha256 = pathlib.Path(prefix_store_data_root, 'sha256')
os.environ["BRM_FS_ROOT"] = str(prefix_data_sha1)
prefix_data_proxy = pathlib.Path(prefix_store_data_root, 'proxy', 'brm_proxy_db.csv')
os.environ["BRM_PROXY_DB"] = str(prefix_data_proxy)
import artichoke_growth.artichoke_growth as ag


# prefix_store_catalog_root = pathlib.Path('tests', 'fixtures', 'catalog')
# prefix_catalog_sha1 = pathlib.Path(prefix_store_catalog_root, 'sha1')
# prefix_catalog_sha256 = pathlib.Path(prefix_store_catalog_root, 'sha256')


def test_by_name_ok_minimal():
    text = '0123456789abcdef'
    hash_length = len(text)
    assert ag.by_name(text, hash_length) is True


def test_by_name_nok_domain_minimal():
    text = '0123456789abcdeg'
    hash_length = len(text)
    assert ag.by_name(text, hash_length) is False


def test_by_name_nok_length_minimal():
    text = '0123456789abcde'
    hash_length = len(text) + 1
    assert ag.by_name(text, hash_length) is False


def test_possible_hash_ok_default():
    text = "0123456789abcdef" * 4
    assert ag.possible_hash(text) is True


def test_possible_hash_ok_sha1():
    text = "0123456789" * 4
    hash_policy = 'sha1'
    assert ag.possible_hash(text, hash_policy) is True


def test_possible_hash_ok_sha256():
    text = "abcdef0123456789" * 4
    hash_policy = 'sha256'
    assert ag.possible_hash(text, hash_policy) is True


def test_walk_hashed_files_ok_sha1():
    data = ag.walk_hashed_files(prefix_data_sha1)
    expectation = f'{prefix_data_sha1}{pathlib.Path("/2a/2a3c26457a1df3f5035099ff6ac4e154d3dfe695")}'
    assert str(next(data)) == expectation


def test_walk_hashed_files_ok_sha256():
    data = ag.walk_hashed_files(prefix_data_sha256)
    expectation = f'{prefix_data_sha256}{pathlib.Path("/1a/1a7cc77e88cc15b4cbbdc8543a34a445fb386c41b1fb57bae94548dda19972f8")}'
    assert str(next(data)) == expectation


def test_file_metrics_ok_sha1():
    data = ag.walk_hashed_files(prefix_data_sha1)
    a_file_path = next(data)
    x_stat = ag.file_metrics(a_file_path)
    assert x_stat.st_size == 323
    f_stat = a_file_path.stat()
    assert f_stat.st_size == x_stat.st_size
    assert f_stat.st_ctime == x_stat.st_ctime
    assert f_stat.st_mtime == x_stat.st_mtime


def test_file_metrics_ok_sha256():
    data = ag.walk_hashed_files(prefix_data_sha256)
    a_file_path = next(data)
    x_stat = ag.file_metrics(a_file_path)
    assert x_stat.st_size == 11
    f_stat = a_file_path.stat()
    assert f_stat.st_size == x_stat.st_size
    assert f_stat.st_ctime == x_stat.st_ctime
    assert f_stat.st_mtime == x_stat.st_mtime


def test_mime_type_ok_sha1():
    data = ag.walk_hashed_files(prefix_data_sha1)
    a_file_path = next(data)
    expectation = 'application/zip; charset=binary'
    assert ag.mime_type(a_file_path) == expectation


def test_mime_type_ok_sha256():
    data = ag.walk_hashed_files(prefix_data_sha256)
    a_file_path = next(data)
    expectation = 'text/x-shellscript; charset=us-ascii'
    assert ag.mime_type(a_file_path) == expectation


def test_mime_type_nok_no_file():
    a_file_path = pathlib.Path('does', 'not', 'exist')
    expectation = 'artichoke/growth'
    assert ag.mime_type(a_file_path) == expectation


def test_elf_hash():
    assert ag.elf_hash(b'msbuild.exe') == 0x53D525
