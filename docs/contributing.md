# Contributing

## How to contribute to the carbon-txt validator project

The Carbon.txt validator is an open source project and contributions are welcome.

Our [issue tracker is on Github](https://github.com/thegreenwebfoundation/carbon-txt-validator/issues), and maintain a high level roadmap of coming releases as milestones.


### Getting set up

Follow the instructions in [installation](installation.md) to get set up if you are on a local machine.

If you prefer to use remote workspace - see [this issue for setting up a Github Codespace, (contributions welcome!)](https://github.com/thegreenwebfoundation/carbon-txt-validator/issues/29)


### Publishing a release

To publish a release to PyPi, on the branch you want to release, you need to create a tag matching the version number in `pyproject.toml`, and then push that tag to the main repository.

If you have origin set to this repository like so:

```
# output from git remote -v

origin  git@github.com:thegreenwebfoundation/carbon-txt-validator.git (fetch)
origin  git@github.com:thegreenwebfoundation/carbon-txt-validator.git (push)
```

And you wanted to push tag 1.2.3, first check that your `pyproject.toml` has that release number:

```
# pyproject.toml

[project]
name = "carbon-txt"
version = "1.2.3"
```

Then make a git tag, making sure you have the `v` prefix for the version number:

```
git tag v1.2.3
```

There is a Github action set up in `.github/workflows/release.yml` that listens for new tags being pushed to the main repository. When a new tag is pushed to the repository, the action builds the python package, and then pushes the release to PyPi using the [Trusted publisher](https://docs.pypi.org/trusted-publishers/) process.

To push a git tag, use the tag name when pushing to the origin repository. In our case of creating  tag `v1.2.3` we push tag `v1.2.3` to `origin`:

```
git push origin v1.2.3
```

#### What happens after I push a tag?

It's worth reviewing [the Github action source directly as the final source of truth](https://github.com/thegreenwebfoundation/carbon-txt-validator/blob/main/.github/workflows/release.yml), but in the nutshell, the Github action responsible for creating releases does the following:

1. Checkout that specific tag from the git source repository
2. Install dependencies for building the python package
3. Build the package, checking that the git tag and the python release version match
4. Publish to the main PyPi package repository

Assuming the action has successfully run, your release should be visible on PyPi at [https://pypi.org/project/carbon-txt](https://pypi.org/project/carbon-txt).

If your release version was 1.2.3, it would be available at [https://pypi.org/project/carbon-txt/1.2.3/](https://pypi.org/project/carbon-txt/1.2.3)


#### Deleting a tag

Tags are tied to specific commits, not branches. So if you have created a tag for a release _but have not pushed it_, you can delete the tag, locally like so:

```
git tag -d v1.2.3
```

You can then re-tag the relevant commit, ready to push and publish:

```
git tag v1.2.3
git push origin v1.2.3
```

Once a tag has been pushed to Github, and used in the publishing workflow, you will not be able to re-use it. See the steps below to avoid 'wasting' a tag.

##### If you're not sure about pushing a release yet

This project broadly follows Semantic versioning.as defined on [the Python Packaging website page on versioning](https://packaging.python.org/en/latest/discussions/versioning/).

**If you want to test the package with others first**

If you want to test out publishing a release on the main PyPi site, use a release candidate suffix, (i.e. `v1.2.3rc1`) with your tags and versions.


**If you want to test the release process itself to get comfortable with it**

Use the PyPi test site. Can deploy to the test PyPi site by setting up a `.pypirc` file in your home directory and adding inside that file tokens issued on the [test.pypi.org](https://test.pypi.org) website.

```
# ~/.pypirc

[pypi]
username = __token__
password = pypi-LONGPASSWORD

[testpypi]
username = __token__
password = pypi-LONGPASSWORD
```

You can then trigger an upload manually using the [twine](https://pypi.org/project/twine/) library :

```
uv run twine upload --repository testpypi dist/* --verbose
```

Assuming you have set up Trusted Publishing on [test.pypi.org](https://test.pypi.org) you can try a test publish by adjusting the `Publish to PyPi` Github action in `release.yml` like so:

```yaml
      - name: Publish package distributions to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # this bit switches where the "Publish to PyPi" action
        # publishes to
        with:
          repository-url: https://test.pypi.org/legacy
```

###### Using a `just` task to manually upload builds

If you prefer, there is also a handy `just ` task for publishing the carbon-txt-validator from a local machine. Run `just publish` to build and upload the latest release to PyPi:

```
just publish
```



## Seeing and building documentation

The documentation for this project are built using Sphinx, using the [myst_parser](https://myst-parser.readthedocs.io/en/latest/intro.html) to support Markdown, and the [furo theme](https://github.com/pradyunsg/furo).

### Updating the documentation locally

You can build docs once using `just docs` to generate the docs, placing the generated html in `./docs/_build/_html`.

If you're working on the docs, it's helpful to see them update as you work.

Use the `just docs-watch` command to start a live-updating server, by default listening at [http://127.0.0.1:8000](http://127.0.0.1:8000).

As you make changes to the documentation source files, the rendered results will show in your browser.

### Updating the public documentation

Every time changes are merged into the `main` branch, a build script at [Read the docs](https://about.readthedocs.com/?ref=readthedocs.org) generates the documentation to serve at the URL below:

[https://carbon-txt-validator.readthedocs.io](https://carbon-txt-validator.readthedocs.io)
