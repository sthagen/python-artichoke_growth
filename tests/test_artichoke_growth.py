# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring,unused-import,reimported
import pytest  # type: ignore

import artichoke_growth.artichoke_growth as ag


def test_by_name_ok_minimal():
    text = '0123456789abcdef'
    hash_length = len(text)
    assert ag.by_name(text, hash_length) is True


def test_by_name_nok_minimal():
    text = '0123456789abcdeg'
    hash_length = len(text)
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
