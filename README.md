# rapids-dependency-file-generator

`rapids-dependency-file-generator` is a Python CLI tool that generates conda `environment.yaml` files and `requirements.txt` files from a single YAML file, typically named `dependencies.yaml`.

When installed, it makes the `rapids-dependency-file-generator` CLI command available which is responsible for parsing a `dependencies.yaml` configuration file and generating the appropriate conda `environment.yaml` and `requirements.txt` dependency files.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [`dependencies.yaml` Format](#dependenciesyaml-format)
  - [`files` key](#files-key)
  - [`channels` key](#channels-key)
  - [`dependencies` key](#dependencies-key)
- [How Dependency Lists Are Merged](#how-dependency-lists-are-merged)
- [Additional CLI Notes](#additional-cli-notes)
- [Examples](#examples)

## Installation

`rapids-dependency-file-generator` is available on [PyPI](https://pypi.org/project/rapids-dependency-file-generator/). To install, run:

```sh
pip install rapids-dependency-file-generator
```

## Usage

When `rapids-dependency-file-generator` is invoked, it will read a `dependencies.yaml` file from the current directory and generate children dependency files.

The `dependencies.yaml` file has the following characteristics:

- it is intended to be committed to the root directory of repositories
- it can define matrices that enable the output dependency files to vary according to any arbitrary specification (or combination of specifications), including CUDA version, machine architecture, Python version, etc.
- it contains bifurcated lists of dependencies based on the dependency's purpose (i.e. build, runtime, test, etc.). The bifurcated dependency lists are merged according to the description in the [_How Dependency Lists Are Merged_](#how-dependency-lists-are-merged) section below.

## `dependencies.yaml` Format

> The [Examples](#examples) section below has instructions on where example `dependency.yaml` files and their corresponding output can be viewed.

The `dependencies.yaml` file has three relevant top-level keys: `files`, `channels`, and `dependencies`. These keys are described in detail below.

### `files` Key

The top-level `files` key is responsible for determining the following:

- which types of dependency files should be generated (i.e. conda `environment.yaml` files and/or `requirements.txt` files)
- where the generated files should be written to (relative to the `dependencies.yaml` file)
- which variant files should be generated (based on the provided matrix)
- which of the dependency lists from the top-level `dependencies` key should be included in the generated files

Here is an example of what the `files` key might look like:

```yaml
files:
  all: # used as the prefix for the generated dependency file names
    output: [conda, requirements] # which dependency file types to generate. required, can be "conda", "requirements", "none" or a list of non-"none" values
    conda_dir: conda/environments # where to put conda environment.yaml files. optional, defaults to "conda/environments"
    requirements_dir: python/cudf # where to put requirements.txt files. optional, but recommended. defaults to "python"
    matrix: # contains an arbitrary set of key/value pairs to determine which dependency files that should be generated. These values are included in the output filename.
      cuda: ["11.5", "11.6"] # which CUDA version variant files to generate.
      arch: [x86_64] # which architecture version variant files to generate. This value should be the result of running the `arch` command on a given machine.
    includes: # a list of keys from the `dependencies` section which should be included in the generated files
      - build
      - test
      - runtime
  build: # multiple `files` children keys can be specified
    output: requirements
    conda_dir: conda/environments
    requirements_dir: python/cudf
    matrix:
      cuda: ["11.5"]
      arch: [x86_64]
      py: ["3.8"]
    includes:
      - build
```

The result of the above configuration is that the following dependency files would be generated:

- `conda/environments/all_cuda-115_arch-x86_64.yaml`
- `conda/environments/all_cuda-116_arch-x86_64.yaml`
- `python/cudf/requirements_all_cuda-115_arch-x86_64.txt`
- `python/cudf/requirements_all_cuda-116_arch-x86_64.txt`
- `python/cudf/requirements_build_cuda-115_arch-x86_64_py-38.txt`

The `all*.yaml` and `requirements_all*.txt` files would include the contents of the `build`, `test`, and `runtime` dependency lists from the top-level `dependency` key. The `requirements_build*.txt` file would only include the contents of the `build` dependency list from the top-level `dependency` key.

The value of `output` can also be `none` as shown below.

```yaml
files:
  test:
    output: none
    includes:
      - test
```

When `output: none` is used, the `conda_dir`, `requirements_dir` and `matrix` keys can be omitted. The use case for `output: none` is described in the [_Additional CLI Notes_](#additional-cli-notes) section below.

### `channels` Key

The top-level `channels` key specifies the channels that should be included in any generated conda `environment.yaml` files.

It might look like this:

```yaml
channels:
  - rapidsai
  - conda-forge
```

In the absence of a `channels` key, some sensible defaults for RAPIDS will be used (see [constants.py](./src/rapids_dependency_file_generator/constants.py)).

### `dependencies` Key

The top-level `dependencies` key is where the bifurcated dependency lists should be specified.

Underneath the `dependencies` key is a list of objects. Each object has the following children keys:

- `output_types` - determines which output types the dependency lists in the list item are applicable too
- `common` - contains dependency lists that are the same across all matrix variations
- `specific` - contains dependency lists that are specific to a particular matrix combination

The structure of these two keys varies slightly.

The `common` key has children which are simple key-value pairs, where the key is an arbitrary name for the dependency list (i.e. `build`, `test`, `libcuml_build`, `cuml_build`, etc.) and the value is a list of dependencies.

The `specific` key's value is an array of objects. Each object contains a `matrix` key and some arbitrarily named dependency lists (similar to the dependency lists under `common`). The `matrix` key is used to define which matrix combinations from `files.[*].matrix` these dependency lists should apply to. This is elaborated on in [How Dependency Lists Are Merged](#how-dependency-lists-are-merged)

An example of the above structure is exemplified below:

```yaml
dependencies:
  - output_types: [conda, requirements] # common dependencies between conda environment.yaml & requirements.txt files
    common: # common between all matrix variations
      build: # arbitrarily named dependency list
        - common_build_dep
      test: # arbitrarily named dependency list
        - pytest
    specific:
      # dependencies specific to x86_64 and 11.5
      - matrix:
          cuda: "11.5"
          arch: x86_64
        build:
          - a_random_x86_115_specific_dep
  - output_types: [conda] # dependencies specific to conda environment.yaml files
    common:
      build:
        - cupy
        - pip: # supports `pip` key for conda environment.yaml files
            - some_random_dep
    specific:
      - matrix:
          cuda: "11.5"
        build:
          - cudatoolkit=11.5
      - matrix:
          cuda: "11.6"
        build:
          - cudatoolkit=11.6
  - output_types: [requirements] # dependencies specific to requirements.txt files
    specific:
      - matrix:
          cuda: "11.5"
        build:
          - another_random_dep=11.5.0
      - matrix:
          cuda: "11.6"
        build:
          - another_random_dep=11.6.0
```

## How Dependency Lists Are Merged

The information from the top-level `files` and `dependencies` keys are used to determine which dependencies should be included in the final output of the generated dependency files.

Consider the following top-level `files` key configuration:

```yaml
files:
  all:
    output: conda
    conda_dir: conda/environments
    requirements_dir: python/cudf
    matrix:
      cuda: ["11.5", "11.6"]
      arch: [x86_64]
    includes:
      - build
      - test
```

Since the `output` value is `conda`, `rapids-dependency-file-generator` will iterate through each entry in the top-level `dependencies` list and use any entry whose `output_types` key is `conda` or `[conda, ...]`.

From those `dependencies` entries, it will look for any `.common.build` and `.common.test` dependency lists to merge.

Further, for the `11.5` and `x86_64` matrix combination, any `build` and `test` lists from entries under the `.specific` key whose matrix value matches any of the definitions below would also be merged:

```yaml
specific:
  - matrix:
      cuda: "11.5"
      arch: "x86_64"
    build:
      - some_dep1
    test:
      - some_dep2
# or
specific:
  - matrix:
      cuda: "11.5"
    build:
      - some_dep1
    test:
      - some_dep2
# or
specific:
  - matrix:
      arch: "x86_64"
    build:
      - some_dep1
    test:
      - some_dep2
```

Merged dependency lists are also deduped.

## Additional CLI Notes

Invoking `rapids-dependency-file-generator` without any arguments is meant to be the default behavior for RAPIDS developers. It will generate all of the necessary dependency files as specified in the top-level `files` configuration.

However, there are CLI arguments that can augment the `files` configuration values before the files are generated.

Consider the example when `output: none` is used:

```yaml
files:
  test:
    output: none
    includes:
      - test
```

The `test` file generated by the configuration above is useful for CI, but it might not make sense to necessarily commit those files to a repository. In such a scenario, the following CLI arguments can be used:

```sh
ENV_NAME="cudf_test"

rapids-dependency-file-generator \
  --file_key "test" \
  --output "conda" \
  --matrix "cuda=11.5;arch=$(arch)" > env.yaml
mamba env create --file env.yaml
mamba activate "$ENV_NAME"

# install cudf packages built in CI and test them in newly created environment...
```

The `--file_key` argument is passed the `test` key name from the `files` configuration. Additional flags are used to generate a single dependency file. When the CLI is used in this fashion, it will print to `stdout` instead of writing the resulting contents to the filesystem.

The `--file_key`, `--output`, and `--matrix` flags must be used together.

Running `rapids-dependency-file-generator -h` will show the most up-to-date CLI arguments.

## Examples

The [tests/examples](./tests/examples/) directory has example `dependencies.yaml` files along with their corresponding output files.

To create new `example` tests do the following:

- Create a new directory with a `dependencies.yaml` file in [tests/examples](tests/examples/)
- Ensure the `output` directories (e.g. `conda_dir`, `requirements_dir`, etc.) are set to write to `output/actual`
- Run `rapids-dependency-file-generator --config tests/examples/<new_folder_name>/dependencies.yaml` to generate the initial output files
- Manually inspect the generated files for correctness
- Copy the contents of `output/actual` to `output/expected`, so it will be committed to the repository and used as a baseline for future changes
- Add the new folder name to [test_examples.py](./tests/test_examples.py)
