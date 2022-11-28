"""Logic for validating dependency files."""

import sys
import textwrap

import jsonschema

SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://github.com/rapidsai/dependency-file-generator/schema.json",
    "type": "object",
    "title": "Dependencies",
    "description": "A list of all dependencies for a project.",
    "properties": {
        "files": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "output": {
                            "type": ["string", "array"],
                            "if": {"type": "array"},
                            "then": {"items": {"type": "string"}},
                        },
                        "conda_dir": {"type": "string"},
                        "requirements_dir": {"type": "string"},
                        "matrix": {"type": "object"},
                        "includes": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["output", "includes"],
                }
            },
        },
        "channels": {
            "type": ["array", "string"],
            "if": {"type": "array"},
            "then": {"items": {"type": "string"}},
        },
        "dependencies": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "common": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "output_types": {
                                        "type": ["array", "string"],
                                        "if": {"type": "array"},
                                        "then": {"items": {"type": "string"}},
                                    },
                                    "packages": {
                                        "type": ["array", "string"],
                                        "if": {"type": "array"},
                                        "then": {
                                            "items": {"type": ["string", "object"]},
                                            "if": {"type": "object"},
                                            "then": {
                                                "patternProperties": {
                                                    ".*": {
                                                        "type": ["array", "string"],
                                                        "if": {"type": "array"},
                                                        "then": {
                                                            "items": {"type": "string"}
                                                        },
                                                    }
                                                }
                                            },
                                        },
                                    },
                                },
                            },
                        },
                        "specific": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "output_types": {
                                        "type": ["array", "string"],
                                        "if": {"type": "array"},
                                        "then": {"items": {"type": "string"}},
                                    },
                                    "matrices": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "matrix": {"type": ["null", "object"]},
                                                "packages": {
                                                    "type": ["null", "array", "string"],
                                                    "if": {"type": "array"},
                                                    "then": {
                                                        "items": {
                                                            "type": ["string", "object"]
                                                        },
                                                        "if": {"type": "object"},
                                                        "then": {
                                                            "patternProperties": {
                                                                ".*": {
                                                                    "type": [
                                                                        "array",
                                                                        "string",
                                                                    ],
                                                                    "if": {
                                                                        "type": "array"
                                                                    },
                                                                    "then": {
                                                                        "items": {
                                                                            "type": "string"
                                                                        }
                                                                    },
                                                                }
                                                            }
                                                        },
                                                    },
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                }
            },
        },
    },
    "required": ["files", "dependencies"],
}


def validate_dependencies(dependencies):
    """Valid a dictionary against the dependencies.yaml spec.

    Parameters
    ----------
    dependencies : dict
        The parsed dependencies.yaml file.

    Raises
    ------
    jsonschema.exceptions.ValidationError
        If the dependencies do not conform to the schema
    """
    validator = jsonschema.Draft7Validator(SCHEMA)
    if not validator.is_valid(dependencies):
        for i, error in enumerate(validator.iter_errors(dependencies), start=1):
            print(f"Error #{i}:", file=sys.stderr)
            print(textwrap.indent(str(error), "\t"), file=sys.stderr)
        raise RuntimeError("The provided dependencies data is invalid.")
