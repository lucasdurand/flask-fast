instantapi
==========

[![](https://badgen.net/pypi/v/flask-fast)](https://pypi.org/project/flask-fast/)
[![](https://badgen.net/pypi/license/flask-fast)](https://pypi.org/project/flask-fast/)
![PyPI - Downloads](https://img.shields.io/pypi/dm/flask-fast)
![PyPI - Status](https://img.shields.io/pypi/status/flask-fast.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Quickly generate a flask (or Dash) app with endpoints exposed from arbitrary functions. Swagger UI will also be generated and default to the app root. 

Flaskit. Dashit. It's instantapi.


## Releasing

[The Release workflow](.github/workflows/release.yml) publishes to PyPI based on the version in `pyproject.toml`. It needs a `PYPI_API_TOKEN` Actions secret.

- **Merge to `main`:** if that version isn't tagged yet, it's published to PyPI and tagged (`v<version>`) with a GitHub release. To release, bump the version (`uv version --bump patch`) and merge to `main`.
- **Merge to `develop`:** a dev pre-release `<version>.dev<N>` is published (N is the workflow run number). If the version is already released, dev builds count towards the next patch version. Install one with `pip install --pre flaskfast`.
