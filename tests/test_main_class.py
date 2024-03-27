# -*- coding: utf-8 -*-
"""
  test_main_class.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 27.03.2024, 13:24:53
  
  Purpose: Tests for main classes.
"""

from unittest import TestCase
from uke_pit2.main import SpiderApp, UkeApp


class TestSpiderApp(TestCase):
    """SpiderApp class test unit."""

    def setUp(self) -> None:
        """Set up tests."""
        self.obj = SpiderApp()

    def test_01_create_object(self) -> None:
        """Test nr 01."""
        self.assertIsInstance(self.obj, SpiderApp)

    def test_02_get_version(self) -> None:
        """Test nr 02."""
        self.assertTrue(hasattr(self.obj, "version"))
        self.assertIsInstance(self.obj.version, str)
        self.assertTrue(len(self.obj.version) > 0, "version string is not set")


class TestUkeApp(TestCase):
    """UkeApp class test unit."""

    def setUp(self) -> None:
        """Set up tests."""
        self.obj = UkeApp()

    def test_01_create_object(self) -> None:
        """Test nr 01."""
        self.assertIsInstance(self.obj, UkeApp)

    def test_02_get_version(self) -> None:
        """Test nr 02."""
        self.assertTrue(hasattr(self.obj, "version"))
        self.assertIsInstance(self.obj.version, str)
        self.assertTrue(len(self.obj.version) > 0, "version string is not set")


# #[EOF]#######################################################################
