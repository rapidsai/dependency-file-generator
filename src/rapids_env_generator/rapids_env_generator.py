import itertools
import yaml
from collections import defaultdict
from os.path import join


def dedupe(dependencies):
    deduped = [dep for dep in dependencies if not isinstance(dep, dict)]
    deduped = sorted(list(set(deduped)))
    dict_like_deps = [dep for dep in dependencies if isinstance(dep, dict)]
    dict_deps = defaultdict(list)
    for dep in dict_like_deps:
        for key, values in dep.items():
            dict_deps[key].extend(values)
            dict_deps[key] = sorted(list(set(dict_deps[key])))
    if dict(dict_deps):
        deduped.append(dict(dict_deps))
    return deduped


def grid(gridspec):
    """Yields the Cartesian product of a `dict` of iterables.

    The input ``gridspec`` is a dictionary whose keys correspond to
    parameter names. Each key is associated with an iterable of the
    values that parameter could take on. The result is a sequence of
    dictionaries where each dictionary has one of the unique combinations
    of the parameter values.
    """
    for values in itertools.product(*gridspec.values()):
        yield dict(zip(gridspec.keys(), values))


def make_env(name, channels, dependencies):
    return yaml.dump(
        {
            "name": name,
            "channels": channels,
            "dependencies": dependencies,
        }
    )


def main(config_file, envs, output_path, to_stdout):
    with open(config_file, "r") as f:
        parsed_config = yaml.load(f, Loader=yaml.FullLoader)
    default_channels = [
        "rapidsai",
        "nvidia",
        "rapidsai-nightly",
        "dask/label/dev",
        "conda-forge",
    ]
    channels = parsed_config.get("channels") or default_channels
    envs = envs if envs else parsed_config["envs"]
    for env_name, env_config in envs.items():
        includes = env_config["includes"]
        env_pkgs = []
        for include in includes:
            env_pkgs.extend(parsed_config[include])

        for matrix_combo in grid(env_config["matrix"]):
            full_env_name = env_name
            cuda_version = matrix_combo["cuda_version"]
            arch = matrix_combo["arch"]
            full_env_name += f"_cuda-{cuda_version}_arch-{arch}"
            matrix_combo_pkgs = []
            for include in includes:
                matrix_combo_pkgs.extend(
                    (parsed_config.get("specifics", {}) or {})
                    .get(f"{arch}-{cuda_version}", {})
                    .get(include, [])
                )
            deduped_pkgs = dedupe(env_pkgs + matrix_combo_pkgs)
            env = make_env(full_env_name, channels, deduped_pkgs)
            if to_stdout:
                print(env)
            if output_path:
                with open(join(output_path, f"{full_env_name}.yaml"), "w") as f:
                    f.write(env)
