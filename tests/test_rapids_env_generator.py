from rapids_env_generator.rapids_env_generator import dedupe, make_env
import yaml


def test_dedupe():
    # simple list
    deduped = dedupe(["dep1", "dep1", "dep2"])
    assert deduped == ["dep1", "dep2"]

    # list w/ pip dependencies
    deduped = dedupe(
        [
            "dep1",
            "dep1",
            {"pip": ["pip_dep1", "pip_dep2"]},
            {"pip": ["pip_dep1", "pip_dep2"]},
        ]
    )
    assert deduped == ["dep1", {"pip": ["pip_dep1", "pip_dep2"]}]


def test_make_env():
    env = make_env("tmp_env", ["rapidsai", "nvidia"], ["dep1", "dep2"])
    assert env == yaml.dump(
        {
            "name": "tmp_env",
            "channels": ["rapidsai", "nvidia"],
            "dependencies": ["dep1", "dep2"],
        }
    )
