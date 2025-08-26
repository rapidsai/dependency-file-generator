__all__ = [
    "DependencyFileGeneratorWarning",
]


class DependencyFileGeneratorWarning(UserWarning):
    pass


class UnusedDependencySetWarning(DependencyFileGeneratorWarning):
    pass
