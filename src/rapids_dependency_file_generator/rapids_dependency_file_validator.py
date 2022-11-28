"""Logic for validating dependency files."""

import jsonschema
import yaml

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


fn = "/home/nfs/vyasr/local/dependency-file-generator/tests/examples/no-specific-match/dependencies.yaml"
with open(fn) as f:
    dependency_data = yaml.load(f, Loader=yaml.FullLoader)

jsonschema.validate(dependency_data, schema=SCHEMA)
