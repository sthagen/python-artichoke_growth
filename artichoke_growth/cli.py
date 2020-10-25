#! /usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
""""Visit folder tree of some binary repository management system and report statistics."""
import os
import sys

import artichoke_growth.artichoke_growth as ag


# pylint: disable=expression-not-assigned
def main(argv=None):
    """Process the files separately per folder."""
    argv = sys.argv[1:] if argv is None else argv
    ag.main(argv)