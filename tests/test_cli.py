from rapids_dependency_file_generator.cli import generate_matrix


def test_generate_matrix():
    matrix = generate_matrix("cuda=11.5;arch=x86_64")
    assert matrix == {"cuda": ["11.5"], "arch": ["x86_64"]}

    matrix = generate_matrix(None)
    assert matrix == {}
