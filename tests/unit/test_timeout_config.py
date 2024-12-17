"""Unit tests for timeout configuration."""

import pytest

from bcra_connector.timeout_config import TimeoutConfig


class TestTimeoutConfig:
    """Test suite for TimeoutConfig class."""

    def test_default_values(self):
        """Test default timeout values."""
        config = TimeoutConfig()
        assert config.connect == 3.05
        assert config.read == 27.0

    def test_custom_values(self):
        """Test custom timeout values."""
        config = TimeoutConfig(connect=5.0, read=30.0)
        assert config.connect == 5.0
        assert config.read == 30.0

    def test_invalid_values(self):
        """Test invalid timeout values."""
        with pytest.raises(ValueError, match="connect timeout must be greater than 0"):
            TimeoutConfig(connect=0)

        with pytest.raises(ValueError, match="connect timeout must be greater than 0"):
            TimeoutConfig(connect=-1)

        with pytest.raises(ValueError, match="read timeout must be greater than 0"):
            TimeoutConfig(read=0)

        with pytest.raises(ValueError, match="read timeout must be greater than 0"):
            TimeoutConfig(read=-1)

    def test_as_tuple(self):
        """Test getting timeout configuration as tuple."""
        config = TimeoutConfig(connect=5.0, read=30.0)
        timeout_tuple = config.as_tuple
        assert isinstance(timeout_tuple, tuple)
        assert len(timeout_tuple) == 2
        assert timeout_tuple == (5.0, 30.0)

    def test_from_total(self):
        """Test creating TimeoutConfig from total timeout value."""
        total_timeout = 10.0
        config = TimeoutConfig.from_total(total_timeout)
        assert config.connect == 1.0  # 10% of total
        assert config.read == 9.0    # 90% of total
        assert isinstance(config, TimeoutConfig)

    def test_invalid_total_timeout(self):
        """Test invalid total timeout values."""
        with pytest.raises(ValueError, match="total timeout must be greater than 0"):
            TimeoutConfig.from_total(0)

        with pytest.raises(ValueError, match="total timeout must be greater than 0"):
            TimeoutConfig.from_total(-1)

    def test_timeout_config_immutability(self):
        """Test that TimeoutConfig instances are effectively immutable."""
        config = TimeoutConfig()
        with pytest.raises(AttributeError):
            config.connect = 10.0
        with pytest.raises(AttributeError):
            config.read = 60.0

    def test_string_representation(self):
        """Test string representation of TimeoutConfig."""
        config = TimeoutConfig(connect=2.0, read=20.0)
        expected_str = "TimeoutConfig(connect=2.00s, read=20.00s)"
        assert str(config) == expected_str

    def test_default_factory_method(self):
        """Test default() factory method."""
        config = TimeoutConfig.default()
        assert isinstance(config, TimeoutConfig)
        assert config.connect == 3.05
        assert config.read == 27.0

    def test_timeout_config_equality(self):
        """Test equality comparison of TimeoutConfig instances."""
        config1 = TimeoutConfig(connect=5.0, read=30.0)
        config2 = TimeoutConfig(connect=5.0, read=30.0)
        config3 = TimeoutConfig(connect=3.0, read=30.0)

        assert config1 == config2
        assert config1 != config3
        assert config1 != "not a config object"

    def test_timeout_config_hash(self):
        """Test hash implementation for TimeoutConfig."""
        config1 = TimeoutConfig(connect=5.0, read=30.0)
        config2 = TimeoutConfig(connect=5.0, read=30.0)

        # Same configurations should have same hash
        assert hash(config1) == hash(config2)

        # Can be used as dictionary keys
        timeout_dict = {config1: "test"}
        assert timeout_dict[config2] == "test"

    def test_timeout_config_repr(self):
        """Test repr implementation for TimeoutConfig."""
        config = TimeoutConfig(connect=5.0, read=30.0)
        expected_repr = "TimeoutConfig(connect=5.0, read=30.0)"
        assert repr(config) == expected_repr
