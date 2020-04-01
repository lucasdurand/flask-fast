from apispec import APISpec
from apispec_webframeworks.flask import FlaskPlugin
import flask
import yaml
from flask import Flask
from typing import List, Callable, Dict
import inspect

from . import parse_args


def create_apispec(appname: str, version: str = "1.0.0") -> APISpec:
    # Create an APISpec
    spec = APISpec(
        title=appname,
        version=version,
        openapi_version="3.0.2",
        plugins=[FlaskPlugin()],
    )
    return spec


def swagger_format(param_in, name, description, type=None, default=None, **other_stuff):
    param = {
        "in": param_in,
        "name": name,
        "schema": {"type": type, "default": default},
        **other_stuff,
    }
    return param


def swagger_params(function: Callable, **yet_other_stuff):
    positional, named, defaults, types = parse_args(function)
    print(types, defaults, positional, named)
    path_args = [
        swagger_format(
            param_in="path", name=arg, description=arg, type=types.get(arg, "")
        )
        for arg in positional
    ]
    query_args = [
        swagger_format(
            param_in="query",
            name=arg,
            description=arg,
            type=types.get(arg, ""),
            default=defaults.get(arg) if defaults else None,
        )
        for arg in named
    ]

    return path_args + query_args


def jigger_the_docstring(function: Callable):
    docstring = function.__doc__

    if "---" in docstring:
        return docstring

    name = function.__name__

    swaggered = {
        "get": {
            "sumary": f"Why not {name}?",
            "description": docstring,
            "parameters": swagger_params(function),
        }
    }

    swagger_docstring = "\n---\n" + yaml.dump(swaggered)
    return docstring + swagger_docstring


def register_function_specs(app: flask.Flask, spec: APISpec):
    # Register the path and the entities within it
    view_functions = app.view_functions
    with app.test_request_context():
        for function in view_functions.values():
            function.__doc__ = jigger_the_docstring(function)
            spec.path(view=function)
