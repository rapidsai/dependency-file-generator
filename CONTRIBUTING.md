# Contributing

## Releases

Releases for `dependency-file-generator` are handled by [semantic-release][semantic-release]. To ensure that every commit on the `main` branch has a semantic commit message, the following settings have been configured:

- Only squash commits are allowed
- The default squash commit message is derived from the pull-request's title and body
- Pull request titles are required to be semantic commit messages

The table below (from [semantic-release][semantic-release] docs) shows the types of changes that correspond to each release type.

| Commit message                                                                                                                                                                                   | Release type                                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| `fix(pencil): stop graphite breaking when too much pressure applied`                                                                                                                             | Patch Release                                                                                   |
| `feat(pencil): add 'graphiteWidth' option`                                                                                                                                                       | Minor Release                                                                                   |
| `perf(pencil): remove graphiteWidth option`<br><br>`BREAKING CHANGE: The graphiteWidth option has been removed.`<br>`The default graphite width of 10mm is always used for performance reasons.` | Major <br /> (Note that the `BREAKING CHANGE: ` string must be in the body of the pull-request) |

If a change type not listed in the table above is used, it will not trigger a release. For example:

- `docs: fix README type`
- `ci: update GHAs workflow`
- `chore: some miscellaneous work`

[semantic-release]: https://github.com/semantic-release/semantic-release
