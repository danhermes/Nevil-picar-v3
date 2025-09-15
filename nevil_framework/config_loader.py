"""
Nevil v3.0 Configuration Loader

Loads and validates YAML configuration files with environment variable expansion.
"""

import yaml
import os
import re
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ValidationError:
    """Configuration validation error details"""
    file_path: str
    error_type: str
    message: str
    line_number: int = None


class ConfigLoader:
    """
    Loads and validates Nevil v3.0 configuration files.

    Features:
    - YAML syntax validation
    - Environment variable expansion (${VAR} and ${VAR:-default})
    - Schema validation for .nodes and .messages files
    - Comprehensive error reporting
    """

    def __init__(self, root_path: str = "."):
        self.root_path = root_path
        self.validation_errors = []

    def load_nodes_config(self) -> Dict[str, Any]:
        """Load and validate root .nodes configuration file"""
        config_path = os.path.join(self.root_path, ".nodes")

        if not os.path.exists(config_path):
            # Return default configuration if no .nodes file exists
            print(f"[ConfigLoader] No .nodes file found at {config_path}, using defaults")
            return self._get_default_nodes_config()

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}

            print(f"[ConfigLoader] Loaded .nodes config from {config_path}")

            # Expand environment variables
            config = self._expand_environment_variables(config)

            # Basic validation
            self._validate_nodes_config(config, config_path)

            return config

        except yaml.YAMLError as e:
            error_msg = f"Invalid YAML in {config_path}: {e}"
            print(f"[ConfigLoader] ERROR: {error_msg}")
            self.validation_errors.append(ValidationError(config_path, "YAML_ERROR", error_msg))
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Error loading {config_path}: {e}"
            print(f"[ConfigLoader] ERROR: {error_msg}")
            raise ValueError(error_msg)

    def load_node_messages_config(self, node_name: str) -> Dict[str, Any]:
        """Load and validate individual node .messages configuration file"""
        config_path = os.path.join(self.root_path, "nodes", node_name, ".messages")

        if not os.path.exists(config_path):
            print(f"[ConfigLoader] No .messages file found for node '{node_name}' at {config_path}")
            return {}

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}

            print(f"[ConfigLoader] Loaded .messages config for '{node_name}' from {config_path}")

            # Basic validation
            self._validate_messages_config(config, config_path)

            return config

        except yaml.YAMLError as e:
            error_msg = f"Invalid YAML in {config_path}: {e}"
            print(f"[ConfigLoader] ERROR: {error_msg}")
            self.validation_errors.append(ValidationError(config_path, "YAML_ERROR", error_msg))
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Error loading {config_path}: {e}"
            print(f"[ConfigLoader] ERROR: {error_msg}")
            raise ValueError(error_msg)

    def discover_nodes(self) -> List[str]:
        """Discover all node directories that contain .messages files"""
        nodes_dir = os.path.join(self.root_path, "nodes")
        discovered_nodes = []

        if not os.path.exists(nodes_dir):
            print(f"[ConfigLoader] Nodes directory not found: {nodes_dir}")
            return discovered_nodes

        try:
            for item in os.listdir(nodes_dir):
                node_path = os.path.join(nodes_dir, item)
                if os.path.isdir(node_path):
                    messages_file = os.path.join(node_path, ".messages")
                    if os.path.exists(messages_file):
                        discovered_nodes.append(item)
                        print(f"[ConfigLoader] Discovered node: {item}")

        except Exception as e:
            print(f"[ConfigLoader] Error discovering nodes: {e}")

        return discovered_nodes

    def _get_default_nodes_config(self) -> Dict[str, Any]:
        """Return default .nodes configuration"""
        return {
            "version": "3.0",
            "description": "Nevil v3.0 default configuration",
            "system": {
                "framework_version": "3.0.0",
                "log_level": "INFO",
                "health_check_interval": 5.0,
                "shutdown_timeout": 10.0,
                "startup_delay": 2.0
            },
            "environment": {
                "NEVIL_VERSION": "3.0",
                "LOG_LEVEL": "INFO"
            },
            "launch": {
                "startup_order": [],
                "parallel_launch": False,
                "wait_for_healthy": True,
                "ready_timeout": 30.0
            }
        }

    def _validate_nodes_config(self, config: Dict[str, Any], file_path: str):
        """Basic validation for .nodes configuration"""
        try:
            # Check required fields
            if "version" not in config:
                self.validation_errors.append(
                    ValidationError(file_path, "MISSING_FIELD", "Missing required field: version")
                )

            # Validate version format
            version = config.get("version", "")
            if not re.match(r'^\d+\.\d+$', str(version)):
                self.validation_errors.append(
                    ValidationError(file_path, "INVALID_VERSION", f"Invalid version format: {version}")
                )

            print(f"[ConfigLoader] Validated .nodes config: {len(self.validation_errors)} errors")

        except Exception as e:
            self.validation_errors.append(
                ValidationError(file_path, "VALIDATION_ERROR", f"Validation error: {e}")
            )

    def _validate_messages_config(self, config: Dict[str, Any], file_path: str):
        """Basic validation for .messages configuration"""
        try:
            # Check that publishes and subscribes are lists if they exist
            publishes = config.get("publishes", [])
            if not isinstance(publishes, list):
                self.validation_errors.append(
                    ValidationError(file_path, "INVALID_TYPE", "Field 'publishes' must be a list")
                )

            subscribes = config.get("subscribes", [])
            if not isinstance(subscribes, list):
                self.validation_errors.append(
                    ValidationError(file_path, "INVALID_TYPE", "Field 'subscribes' must be a list")
                )

            # Validate publish configurations
            for i, pub in enumerate(publishes):
                if not isinstance(pub, dict):
                    self.validation_errors.append(
                        ValidationError(file_path, "INVALID_TYPE", f"publishes[{i}] must be a dictionary")
                    )
                elif "topic" not in pub:
                    self.validation_errors.append(
                        ValidationError(file_path, "MISSING_FIELD", f"publishes[{i}] missing required field: topic")
                    )

            # Validate subscription configurations
            for i, sub in enumerate(subscribes):
                if not isinstance(sub, dict):
                    self.validation_errors.append(
                        ValidationError(file_path, "INVALID_TYPE", f"subscribes[{i}] must be a dictionary")
                    )
                elif "topic" not in sub:
                    self.validation_errors.append(
                        ValidationError(file_path, "MISSING_FIELD", f"subscribes[{i}] missing required field: topic")
                    )
                elif "callback" not in sub:
                    self.validation_errors.append(
                        ValidationError(file_path, "MISSING_FIELD", f"subscribes[{i}] missing required field: callback")
                    )

            print(f"[ConfigLoader] Validated .messages config: {len(self.validation_errors)} errors")

        except Exception as e:
            self.validation_errors.append(
                ValidationError(file_path, "VALIDATION_ERROR", f"Validation error: {e}")
            )

    def _expand_environment_variables(self, config: Any) -> Any:
        """
        Recursively expand environment variables in configuration.

        Supports:
        - ${VAR} - Required environment variable
        - ${VAR:-default} - Environment variable with default value
        """
        if isinstance(config, dict):
            return {key: self._expand_environment_variables(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._expand_environment_variables(item) for item in config]
        elif isinstance(config, str):
            return self._expand_string_variables(config)
        else:
            return config

    def _expand_string_variables(self, text: str) -> str:
        """Expand environment variables in a string"""
        # Pattern to match ${VAR} or ${VAR:-default}
        pattern = r'\$\{([^}:]+)(?::-(.*?))?\}'

        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else None

            env_value = os.getenv(var_name)

            if env_value is not None:
                return env_value
            elif default_value is not None:
                return default_value
            else:
                # Required variable not found
                error_msg = f"Required environment variable not found: {var_name}"
                print(f"[ConfigLoader] ERROR: {error_msg}")
                return f"${{{var_name}}}"  # Leave unexpanded for debugging

        return re.sub(pattern, replace_var, text)

    def get_validation_errors(self) -> List[ValidationError]:
        """Get list of validation errors encountered during loading"""
        return self.validation_errors

    def has_errors(self) -> bool:
        """Check if any validation errors were encountered"""
        return len(self.validation_errors) > 0

    def print_errors(self):
        """Print all validation errors to console"""
        if not self.validation_errors:
            print("[ConfigLoader] No validation errors")
            return

        print(f"[ConfigLoader] Found {len(self.validation_errors)} validation errors:")
        for error in self.validation_errors:
            print(f"  {error.file_path}: {error.error_type} - {error.message}")