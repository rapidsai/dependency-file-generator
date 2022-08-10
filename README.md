# dependency-file-generator

`dependency-file-generator` is a Python CLI tool that generates `conda` environment files and `requirements.txt` files from a single YAML file, typically named `dependencies.yaml`. When installed via `pip`, it makes the `rapids-dep-file-generator` CLI command available which is responsible for parsing a `dependencies.yaml` configuration file and generating the appropriate `conda` environment and `requirements.txt` dependency files.

## Usage

When `rapids-dep-file-generator` is invoked, it will read a `dependencies.yaml` file from the current directory and generate children dependency files. `dependencies.yaml` is intended to be committed to the root directory of repositories. It has specific keys (described below) that enable the bifurcation of dependencies for different CUDA versions, architectures, and dependency file types (i.e. `conda` environment files vs `requirements.txt`).

<!-- TALK ABOUT MERGING SECTIONS -->

## `dependencies.yaml` Format

The `dependencies.yaml` file has three relevant top-level keys: `files`, `channels`, and `dependencies`. These keys are described in detail below.

### `files` Key

The top-level `files` key is responsible for determining the following:

- which types of dependency files should be generated (i.e. `conda` environment files and/or `requirements.txt` files)
- where the generated files should be written to
- which architecture and CUDA version variant files should be generated
- which of the dependency lists from the top-level `dependencies` key should be included in the generated files

Here is an example of what the `files` key might look like:

```yaml
files:
  all: # used as the prefix for the generated dependency file names
    generate: both # which dependency file types to generate. required, can be "both", "env", "requirements", or "none"
    conda_dir: conda/environments # where to put conda environment files. optional, defaults to "conda/environments"
    requirements_dir: python/cudf # where to put requirements.txt files. optional, but recommended. defaults to "python"
    matrix:
      cuda_version: ["11.5", "11.6"] # which CUDA version variant files to generate. The CUDA version is included in the output file name
      arch: [x86_64] # which architecture version variant files to generate. The architecture is included in the output file name. This value should be the result of running the `arch` command on a given machine.
    includes: # a list of keys from the `dependencies` section which should be included in the generated files
      - build
      - test
      - runtime
  build: # multiple `files` children keys can be specified
    generate: requirements
    conda_dir: conda/environments
    requirements_dir: python/cudf
    matrix:
      cuda_version: ["11.5"]
      arch: [x86_64]
    includes:
      - build
```

The result of the above configuration is that the following dependency files would be generated:

- `conda/environments/all_cuda-11.5_arch-x86_64.yaml`
- `conda/environments/all_cuda-11.6_arch-x86_64.yaml`
- `python/cudf/requirements_all_cuda-11.5_arch-x86_64.txt`
- `python/cudf/requirements_all_cuda-11.6_arch-x86_64.txt`
- `python/cudf/requirements_build_cuda-11.5_arch-x86_64.txt`

The `all*.yaml` and `requirements_all*.txt` files would include the contents of the `build`, `test`, and `runtime` dependency lists from the top-level `dependency` key. The `build*.yaml` and `requirements_build*.txt` files would only include the contents of the `build` dependency list from the top-level `dependency` key.

The value of `generate` can also be `none` as shown below.

```yaml
files:
  test:
    generate: none
    includes:
      - test
```

When `generate: none` is used, the `conda_dir`, `requirements_dir` and `matrix` keys can be ommitted. The use case for `generate: none` is described in the _Additional CLI Notes_ section below.

### `channels` Key

The top-level `conda` key specifies the channels that should be included in any generated `conda` environment files.

It might look like this:

```yaml
channels:
  - rapidsai
  - conda-forge
```

In the absence of a `channels` key, some sensible defaults for RAPIDS will be used (see [constants.py](./src/rapids_env_generator/constants.py)).

### `dependencies` Key

The top-level `dependencies` key is where the bifurcated dependency lists should be specified. Directly beneath the `dependencies` key are 3 unique keys:

- `conda_requirements` - contains dependency lists that are the sames for both `conda` environment files and `requirements.txt` files
- `conda` - contains dependency lists that are specific to `conda` environment files
- `requirements` - contains dependency lists that are specific to `requirements.txt` files

Each of the above keys has the following children keys:

- `common` - contains dependency lists that are the same across CUDA versions and architectures
- `<arch>-<cuda_version>` (i.e. `x86_64-11.5`) - contains dependency lists that are specific to the respective architecture and CUDA versions

Below these keys are any number of arbitrarily named dependency lists (i.e. `build`, `test`, `libcuml_build`, `cuml_build`, etc.).

An example of the above structure is exemplified below:

```yaml
dependencies:
  conda_requirements: # common dependencies between conda & requirements.txt
    common: # common between archs/cudas
      build: # arbitrarily named dependency list
        - common_build_dep
      test: # arbitrarily named dependency list
        - pytest
    x86_64-11.5:
      build:
        - a_random_x86_115_specific_dep
  conda: # dependencies specific to conda environment files
    common:
      build:
        - cupy
        - pip: # supports `pip` key for `conda` environment files
            - some_random_dep
    x86_64-11.5:
      build:
        - cudatoolkit=11.5
    x86_64-11.6:
      build:
        - cudatoolkit=11.6
  requirements: # dependencies specific to requirements.txt files
    x86_64-11.5:
      build:
        - another_random_dep=11.5.0
    x86_64-11.6:
      build:
        - another_random_dep=11.6.0
```

## How Dependency Lists Are Merged

The information from the top-level `files` and `dependencies` keys are used to determine which dependencies should be included in the final output of the generated dependency files.

Consider the following top-level `files` key configuration:

```yaml
files:
  all:
    generate: conda
    conda_dir: conda/environments
    requirements_dir: python/cudf
    matrix:
      cuda_version: ["11.5", "11.6"]
      arch: [x86_64, arm]
    includes:
      - build
      - test
```

For the `11.5` and `x86_64` matrix combination, the following dependency lists would be merged if they exist:

- `conda_requirements.common.build`
- `conda_requirements.x86_64-11.5.build`
- `conda.common.build`
- `conda.x86_64-11.5.build`
- `conda_requirements.common.test`
- `conda_requirements.x86_64-11.5.test`
- `conda.common.test`
- `conda.x86_64-11.5.test`

Merged dependency lists are also deduped.

## Additional CLI Notes

Invoking `rapids-dep-file-generator` without any arguments is meant to be the default behavior for RAPIDS developers. It will generate all of the necessary dependency files as specified in the top-level `files` configuration.

However, there are CLI arguments that can augment the `files` configuration values before the files are generated.

Consider the example when `generate: none` is used:

```yaml
files:
  test:
    generate: none
    includes:
      - test
```

The `test` configuration above is useful for CI, but it might not make sense to necessarily commit those files to a repository. In such a scenario, the following CLI arguments can be used:

```sh
ENV_NAME="cudf_test"

rapids-dep-file-generator \
  --file_key "test" \
  --generate "conda" \
  --cuda_version "11.5" \
  --arch $(arch) > env.yaml
mamba env create --file env.yaml
mamba activate "$ENV_NAME"

# install cudf packages built in CI and test them in newly created environment...
```

The `--file_key`, `--generate`, `--cuda_version`, and `--arch` flags are mutually inclusive and therefore need to be used together. When the CLI is used in this fashion, it will print to `stdout` instead of writing the resulting contents to the filesystem.

Running `rapids-dep-file-generator -h` will show the most up-to-date CLI arguments.
