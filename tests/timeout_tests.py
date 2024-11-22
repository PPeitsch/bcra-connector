"""Unit tests for request timeout configuration."""

import unittest

from bcra_connector.timeout_config import TimeoutConfig


class TestTimeoutConfig(unittest.TestCase):
    """Test suite for the TimeoutConfig class."""

    def test_default_values(self):
        """Test default timeout values."""
        config = TimeoutConfig()
        self.assertEqual(config.connect, 3.05)
        self.assertEqual(config.read, 27.0)

    def test_custom_values(self):
        """Test custom timeout values."""
        config = TimeoutConfig(connect=5.0, read=30.0)
        self.assertEqual(config.connect, 5.0)
        self.assertEqual(config.read, 30.0)

    def test_invalid_values(self):
        """Test invalid timeout values."""
        with self.assertRaises(ValueError):
            TimeoutConfig(connect=0)
        with self.assertRaises(ValueError):
            TimeoutConfig(connect=-1)
        with self.assertRaises(ValueError):
            TimeoutConfig(read=0)
        with self.assertRaises(ValueError):
            TimeoutConfig(read=-1)

    def test_from_total(self):
        """Test creating TimeoutConfig from total timeout."""
        config = TimeoutConfig.from_total(10.0)
        self.assertEqual(config.connect, 1.0)  # 10% of total
        self.assertEqual(config.read, 9.0)  # 90% of total

    def test_invalid_total(self):
        """Test invalid total timeout values."""
        with self.assertRaises(ValueError):
            TimeoutConfig.from_total(0)
        with self.assertRaises(ValueError):
            TimeoutConfig.from_total(-1)

    def test_as_tuple(self):
        """Test getting timeout as tuple."""
        config = TimeoutConfig(connect=2.0, read=20.0)
        self.assertEqual(config.as_tuple, (2.0, 20.0))

    def test_default_factory(self):
        """Test default timeout factory method."""
        config = TimeoutConfig.default()
        self.assertEqual(config.connect, 3.05)
        self.assertEqual(config.read, 27.0)

    def test_string_representation(self):
        """Test string representation of TimeoutConfig."""
        config = TimeoutConfig(connect=2.0, read=20.0)
        self.assertEqual(str(config), "TimeoutConfig(connect=2.00s, read=20.00s)")
