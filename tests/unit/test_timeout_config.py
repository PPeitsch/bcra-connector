"""Unit tests for timeout configuration."""

from typing import Dict, Tuple

import pytest

from bcra_connector.timeout_config import TimeoutConfig


class TestTimeoutConfig:
    """Test suite for TimeoutConfig class."""

    def test_default_values(self) -> None:
        """Test default timeout values."""
        config: TimeoutConfig = TimeoutConfig()
        assert config.connect == 3.05
        assert config.read == 27.0

    def test_custom_values(self) -> None:
        """Test custom timeout values."""
        config: TimeoutConfig = TimeoutConfig(connect=5.0, read=30.0)
        assert config.connect == 5.0
        assert config.read == 30.0

    def test_invalid_values(self) -> None:
        """Test invalid timeout values."""
        with pytest.raises(ValueError, match="connect timeout must be greater than 0"):
            TimeoutConfig(connect=0)

        with pytest.raises(ValueError, match="connect timeout must be greater than 0"):
            TimeoutConfig(connect=-1)

        with pytest.raises(ValueError, match="read timeout must be greater than 0"):
            TimeoutConfig(read=0)

        with pytest.raises(ValueError, match="read timeout must be greater than 0"):
            TimeoutConfig(read=-1)

    def test_as_tuple(self) -> None:
        """Test getting timeout configuration as tuple."""
        config: TimeoutConfig = TimeoutConfig(connect=5.0, read=30.0)
        timeout_tuple: Tuple[float, float] = config.as_tuple
        assert isinstance(timeout_tuple, tuple)
        assert len(timeout_tuple) == 2
        assert timeout_tuple == (5.0, 30.0)

    def test_from_total(self) -> None:
        """Test creating TimeoutConfig from total timeout value."""
        total_timeout: float = 10.0
        config: TimeoutConfig = TimeoutConfig.from_total(total_timeout)
        assert config.connect == 1.0  # 10% of total
        assert config.read == 9.0  # 90% of total
        assert isinstance(config, TimeoutConfig)

    def test_invalid_total_timeout(self) -> None:
        """Test invalid total timeout values."""
        with pytest.raises(ValueError, match="total timeout must be greater than 0"):
            TimeoutConfig.from_total(0)

        with pytest.raises(ValueError, match="total timeout must be greater than 0"):
            TimeoutConfig.from_total(-1)

    def test_timeout_config_immutability(self) -> None:
        """Test that TimeoutConfig instances are effectively immutable."""
        config: TimeoutConfig = TimeoutConfig()
        with pytest.raises(AttributeError):
            setattr(config, "connect", 10.0)
        with pytest.raises(AttributeError):
            setattr(config, "read", 60.0)

    def test_string_representation(self) -> None:
        """Test string representation of TimeoutConfig."""
        config: TimeoutConfig = TimeoutConfig(connect=2.0, read=20.0)
        expected_str: str = "TimeoutConfig(connect=2.00s, read=20.00s)"
        assert str(config) == expected_str

    def test_default_factory_method(self) -> None:
        """Test default() factory method."""
        config: TimeoutConfig = TimeoutConfig.default()
        assert isinstance(config, TimeoutConfig)
        assert config.connect == 3.05
        assert config.read == 27.0

    def test_timeout_config_equality(self) -> None:
        """Test equality comparison of TimeoutConfig instances."""
        config1: TimeoutConfig = TimeoutConfig(connect=5.0, read=30.0)
        config2: TimeoutConfig = TimeoutConfig(connect=5.0, read=30.0)
        config3: TimeoutConfig = TimeoutConfig(connect=3.0, read=30.0)

        assert config1 == config2
        assert config1 != config3
        assert config1 != "not a config object"

    def test_timeout_config_hash(self) -> None:
        """Test hash implementation for TimeoutConfig."""
        config1: TimeoutConfig = TimeoutConfig(connect=5.0, read=30.0)
        config2: TimeoutConfig = TimeoutConfig(connect=5.0, read=30.0)

        # Same configurations should have same hash
        assert hash(config1) == hash(config2)

        # Can be used as dictionary keys
        timeout_dict: Dict[TimeoutConfig, str] = {config1: "test"}
        assert timeout_dict[config2] == "test"

    def test_timeout_config_repr(self) -> None:
        """Test repr implementation for TimeoutConfig."""
        config: TimeoutConfig = TimeoutConfig(connect=5.0, read=30.0)
        expected_repr: str = "TimeoutConfig(connect=5.0, read=30.0)"
        assert repr(config) == expected_repr
