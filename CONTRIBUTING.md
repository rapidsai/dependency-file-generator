# Contributing

## Releases

Releases for `dependency-file-generator` are handled by [semantic-release][semantic-release]. To ensure that every commit on the `main` branch has a semantic commit message, the following settings have been configured:

- Only squash commits are allowed
- The default squash commit message is derived from the pull-request's title and body
- Pull request titles are required to be semantic commit messages

The table below (from [semantic-release][semantic-release] docs) shows the types of changes that correspond to each release type.

| Commit message                                                                                                                                                                                   | Release type                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| `fix(pencil): stop graphite breaking when too much pressure applied`                                                                                                                             | ~~Patch~~ Fix Release                                                                                               |
| `feat(pencil): add 'graphiteWidth' option`                                                                                                                                                       | ~~Minor~~ Feature Release                                                                                           |
| `perf(pencil): remove graphiteWidth option`<br><br>`BREAKING CHANGE: The graphiteWidth option has been removed.`<br>`The default graphite width of 10mm is always used for performance reasons.` | ~~Major~~ Breaking Release <br /> (Note that the `BREAKING CHANGE: ` token must be in the body of the pull-request) |

[semantic-release]: https://github.com/semantic-release/semantic-release
