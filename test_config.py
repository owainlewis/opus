"""Unit tests for config parsing and environment variable expansion"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.opus.models import expand_env_vars, OpusConfig


class TestExpandEnvVars:
    """Tests for environment variable expansion in config data"""

    def test_basic_env_var_expansion(self):
        """Test basic ${VAR_NAME} expansion"""
        os.environ["TEST_VAR"] = "test_value"
        try:
            result = expand_env_vars("${TEST_VAR}")
            assert result == "test_value"
        finally:
            del os.environ["TEST_VAR"]

    def test_env_var_with_default(self):
        """Test ${VAR_NAME:-default} expansion with default value"""
        # When var is not set, use default
        result = expand_env_vars("${NONEXISTENT_VAR:-default_value}")
        assert result == "default_value"

        # When var is set, use the value
        os.environ["EXISTING_VAR"] = "actual_value"
        try:
            result = expand_env_vars("${EXISTING_VAR:-default_value}")
            assert result == "actual_value"
        finally:
            del os.environ["EXISTING_VAR"]

    def test_missing_env_var_returns_original(self):
        """Test that missing env vars without defaults return original string"""
        result = expand_env_vars("${MISSING_VAR}")
        assert result == "${MISSING_VAR}"

    def test_env_var_in_string(self):
        """Test env var expansion within a larger string"""
        os.environ["TEST_VAR"] = "world"
        try:
            result = expand_env_vars("hello ${TEST_VAR}!")
            assert result == "hello world!"
        finally:
            del os.environ["TEST_VAR"]

    def test_multiple_env_vars_in_string(self):
        """Test multiple env var expansions in one string"""
        os.environ["VAR1"] = "foo"
        os.environ["VAR2"] = "bar"
        try:
            result = expand_env_vars("${VAR1} and ${VAR2}")
            assert result == "foo and bar"
        finally:
            del os.environ["VAR1"]
            del os.environ["VAR2"]

    def test_dict_expansion(self):
        """Test env var expansion in nested dictionaries"""
        os.environ["API_KEY"] = "secret123"
        os.environ["API_URL"] = "https://api.example.com"
        try:
            data = {
                "api_key": "${API_KEY}",
                "api_url": "${API_URL}",
                "timeout": 30,  # Non-string value
            }
            result = expand_env_vars(data)
            assert result == {
                "api_key": "secret123",
                "api_url": "https://api.example.com",
                "timeout": 30,
            }
        finally:
            del os.environ["API_KEY"]
            del os.environ["API_URL"]

    def test_list_expansion(self):
        """Test env var expansion in lists"""
        os.environ["ITEM1"] = "first"
        os.environ["ITEM2"] = "second"
        try:
            data = ["${ITEM1}", "${ITEM2}", "third"]
            result = expand_env_vars(data)
            assert result == ["first", "second", "third"]
        finally:
            del os.environ["ITEM1"]
            del os.environ["ITEM2"]

    def test_nested_structures(self):
        """Test env var expansion in deeply nested structures"""
        os.environ["DB_HOST"] = "localhost"
        os.environ["DB_PORT"] = "5432"
        try:
            data = {
                "database": {
                    "host": "${DB_HOST}",
                    "port": "${DB_PORT}",
                    "options": ["${DB_HOST}:${DB_PORT}"],
                }
            }
            result = expand_env_vars(data)
            assert result == {
                "database": {
                    "host": "localhost",
                    "port": "5432",
                    "options": ["localhost:5432"],
                }
            }
        finally:
            del os.environ["DB_HOST"]
            del os.environ["DB_PORT"]

    def test_non_string_types_unchanged(self):
        """Test that non-string types pass through unchanged"""
        assert expand_env_vars(42) == 42
        assert expand_env_vars(3.14) == 3.14
        assert expand_env_vars(True) is True
        assert expand_env_vars(None) is None


class TestOpusConfigLoading:
    """Tests for OpusConfig YAML loading with env var expansion"""

    def test_load_config_with_env_vars(self):
        """Test loading config file with environment variable expansion"""
        os.environ["TEST_API_KEY"] = "my_secret_key"
        os.environ["TEST_MODEL"] = "gpt-4"

        try:
            # Create temporary config file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f:
                config_data = {
                    "provider": "openai",
                    "model": "${TEST_MODEL}",
                    "openai_api_key": "${TEST_API_KEY}",
                    "max_iterations": 25,
                }
                yaml.dump(config_data, f)
                config_path = f.name

            # Load config
            config = OpusConfig.from_yaml(config_path)

            # Verify env vars were expanded
            assert config.model == "gpt-4"
            assert config.openai_api_key == "my_secret_key"
            assert config.provider == "openai"
            assert config.max_iterations == 25

        finally:
            del os.environ["TEST_API_KEY"]
            del os.environ["TEST_MODEL"]
            Path(config_path).unlink()

    def test_load_config_with_defaults(self):
        """Test loading config with default values for missing env vars"""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "provider": "openai",
                "model": "${MISSING_MODEL:-gpt-4-turbo}",
                "openai_api_key": "${MISSING_KEY:-default_key}",
            }
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            # Load config
            config = OpusConfig.from_yaml(config_path)

            # Verify defaults were used
            assert config.model == "gpt-4-turbo"
            assert config.openai_api_key == "default_key"

        finally:
            Path(config_path).unlink()

    def test_config_file_not_found(self):
        """Test that loading non-existent config raises FileNotFoundError"""
        with pytest.raises(FileNotFoundError) as exc_info:
            OpusConfig.from_yaml("/nonexistent/path/config.yaml")

        assert "Configuration file not found" in str(exc_info.value)

    def test_env_vars_in_tools_config(self):
        """Test env var expansion in tools configuration"""
        os.environ["TOOL_TIMEOUT"] = "60"

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f:
                config_data = {
                    "provider": "openai",
                    "model": "gpt-4",
                    "tools": {
                        "bash": {
                            "enabled": True,
                            "timeout": "${TOOL_TIMEOUT}",
                        }
                    },
                }
                yaml.dump(config_data, f)
                config_path = f.name

            # Load config
            config = OpusConfig.from_yaml(config_path)

            # Verify env var was expanded in tools config
            bash_config = config.get_tool_config("bash")
            assert bash_config["timeout"] == "60"

        finally:
            del os.environ["TOOL_TIMEOUT"]
            Path(config_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
