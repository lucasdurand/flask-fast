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

Bump `version` in `pyproject.toml` (`uv version --bump patch`), then publish a GitHub release tagged with that version (e.g. `v0.1.5`). [The Publish workflow](.github/workflows/publish.yml) checks that the tag matches, builds the package and uploads it to PyPI. It needs a `PYPI_API_TOKEN` Actions secret.
