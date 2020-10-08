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
