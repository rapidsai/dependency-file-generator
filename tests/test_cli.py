from rapids_env_generator.cli import generate_env_obj


def test_generate_env_obj():
    # valid env
    env_obj = generate_env_obj(
        "tmp_env", "cuda_version=11.5;arch=x86_64,aarch64", "build,test"
    )
    assert env_obj == {
        "tmp_env": {
            "matrix": {"cuda_version": ["11.5"], "arch": ["x86_64"]},
            "includes": ["build", "test"],
        }
    }

    # invalid env: missing matrix
    env_obj = generate_env_obj("tmp_env", "", "build,test")
    assert env_obj == {}

    # invalid env: missing includes
    env_obj = generate_env_obj("tmp_env", "cuda_version=11.5;arch=x86_64,aarch64", "")
    assert env_obj == {}

    # invalid env: missing matrix & includes
    env_obj = generate_env_obj("tmp_env", "", "")
    assert env_obj == {}
