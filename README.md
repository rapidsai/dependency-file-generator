# rapids-env-generator

`rapids-env-generator` is a Python package that generates multiple `conda` environment files from a single YAML file. When installed via `pip`, it makes the `rapids-env-generator` CLI command available which is responsible for parsing an `envs.yaml` configuration file and generating the appropriate `conda` environment files.

## Usage

By default, when `rapids-env-generator` is run, it will look for a `conda/environments/envs.yaml` file relative to the directory from which it's invoked. `rapids-env-generator` will then generate the corresponding environment files based on the contents of the `envs.yaml` file. By default, the generated environment files will be output to the same directory as the `envs.yaml` file (i.e. `conda/environments`).

Here is an example of an `envs.yaml` file:

```yaml
# `envs` object contains the names and configurations of the environment files that should be created
envs:
  build: # environment name & file name
    matrix:
      cuda_version: ["11.5", "11.6"] # the CUDA variants that should be generated
      arch: [x86_64] # the architecture variants that should be generated
    includes: # the names of the keys whose lists should be included in the final environment file
      - build
channels: # which channels should be included in environment file
  - rapidsai
  - nvidia
specifics: # CUDA/arch specific dependencies go in here
  x86_64-11.5: # key which defines packages that are specific to x86_64 architecture and CUDA 11.5
    build: # arbitrarily named key whose contents will be merged with a top-level `build` list if it exists
      - cudatoolkit==11.5.0
      - &gcc_x86 gcc_linux-64=9.*
      - &sysroot_x86 sysroot_linux-64==2.17
      - nvcc_linux-64=11.5
      - pip:
          - random_dep
  x86_64-11.6:
    build:
      - cudatoolkit==11.6.0
      - *gcc_x86 # YAML anchors can be used to keep things DRY
      - *sysroot_x86
      - nvcc_linux-64=11.6
      - pip:
          - random_dep
# arbitrarily named bifurcated dependency lists
build:
  - django=3
  - pytorch
  - pip:
      - snakes
```

Running `rapids-env-generator` on the `envs.yaml` file above will produce the following two files, where the dependencies from the top-level `build` key and the `build` keys in the `specifics` object have been merged.

```yaml
# build_cuda-11.5_arch-x86_64.yaml
channels:
  - rapidsai
  - nvidia
dependencies:
  - cudatoolkit==11.5.0
  - django=3
  - gcc_linux-64=9.*
  - nvcc_linux-64=11.5
  - pytorch
  - sysroot_linux-64==2.17
  - pip:
      - random_dep
      - snakes
name: build_cuda-11.5_arch-x86_64
```

and

```yaml
# build_cuda-11.6_arch-x86_64.yaml
channels:
  - rapidsai
  - nvidia
dependencies:
  - cudatoolkit==11.6.0
  - django=3
  - gcc_linux-64=9.*
  - nvcc_linux-64=11.6
  - pytorch
  - sysroot_linux-64==2.17
  - pip:
      - random_dep
      - snakes
name: build_cuda-11.6_arch-x86_64
```

Mutliple environments can be specified. For instance, the following `envs.yaml` file:

```yaml
envs:
  build: # `build` environment configuration
    matrix:
      cuda_version: ["11.5"]
      arch: [x86_64]
    includes:
      - build
  build_and_test: # `build_and_test` environment configuration
    matrix:
      cuda_version: ["11.5"]
      arch: [x86_64]
    includes:
      - build
      - test
channels:
  - rapidsai
  - nvidia
specifics:
build:
  - django=3
  - pytorch
  - pip:
      - snakes
test:
  - pytest
```

will create `build_and_test_cuda-11.5_arch-x86_64.yaml` and `build_cuda-11.5_arch-x86_64.yaml`, with the only difference being that the `build_and_test_cuda-11.5_arch-x86_64.yaml` file will also include `pytest` as a dependency.

### CLI Arguments

`rapids-env-generator` can also be invoked with arguments. This is useful for creating a one-off environment file that shouldn't necessarily be committed to the source repository. For example:

```sh
ENV_NAME="cudf_test"

rapids-env-generator \
  --file_key "test" \
  --generate "conda" \
  --cuda_version "11.5" \
  --arch $(arch) > env.yaml
mamba env create --file env.yaml
mamba activate "$ENV_NAME"

# install cudf packages built in CI and test them in newly created environment...
```

Run `rapids-env-generator -h` to see the most up-to-date CLI arguments.
