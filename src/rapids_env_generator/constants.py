default_channels = [
    "rapidsai",
    "nvidia",
    "rapidsai-nightly",
    "dask/label/dev",
    "conda-forge",
]

default_env_dir = "conda/environments"

arch_cuda_key_fmt = lambda arch, cuda_ver: f"{arch}-{cuda_ver}"
