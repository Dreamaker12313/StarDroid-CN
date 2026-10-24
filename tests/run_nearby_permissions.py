#!/usr/bin/env python3
"""Compatibility entry point for the current Google-free permission suite."""
import pathlib,runpy
runpy.run_path(str(pathlib.Path(__file__).with_name('run_local_permissions.py')),run_name='__main__')
