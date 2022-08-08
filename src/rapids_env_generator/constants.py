default_channels = [
    "rapidsai",
    "nvidia",
    "rapidsai-nightly",
    "dask/label/dev",
    "conda-forge",
]

default_conda_dir = "conda/environments"
default_txt_dir = "python"

arch_cuda_key_fmt = lambda arch, cuda_ver: f"{arch}-{cuda_ver}"
