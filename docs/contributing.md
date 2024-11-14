# Contributing to the carbon-txt validator project

The Carbon-txt validator is an open source project and contributions are welcomed.

Our [issue tracker is on Github](https://github.com/thegreenwebfoundation/carbon-txt-validator/issues), and maintain a high level roadmap of coming releases as milestones.

### Getting set up

Follow the instructions in [installation](installation.md) to get set up if you are on a local machine.

If you prefer to use remote workspace - see [this issue for setting up a github Codespace, (contributions welcome!)](https://github.com/thegreenwebfoundation/carbon-txt-validator/issues/29)


### Publishing a release

To publish a release to PyPi, on the branch you want to release, you need to create a tag matching the version number in `pyproject.toml`, and then push that tag to the main repository.

If you have origin set to this repository like so:

```
# output from git remote -v

origin  git@github.com:thegreenwebfoundation/carbon-txt-validator.git (fetch)
origin  git@github.com:thegreenwebfoundation/carbon-txt-validator.git (push)
```

And you wanted to push tag 1.2.3, first check that your `pyproject.toml` has that release numbers:

```
# pyproject.toml

[project]
name = "carbon-txt"
version = "0.0.8rc1"
```

Then make a git tag, making sure you have the `v` prefix for the version number:

```
git tag v1.2.3
```

There is a Github action set up in `.github/workflows/release.yml` that listens for new tags being pushed to the main repo, and then pushes the arelease to PyPi using the [Trusted publisher](https://docs.pypi.org/trusted-publishers/) process.

To push a git tag, use the tag name when pushing to the origin repository.

In our case we could push like so:

```
git push origin v1.2.3
```
