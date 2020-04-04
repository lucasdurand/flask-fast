from apispec import APISpec

# from apispec_webframeworks.flask import FlaskPlugin
import flask, dash
import yaml, json
from flask import Flask
from typing import List, Callable, Dict, Union
import inspect

from . import dashit


def create_apispec(appname: str, version: str = "1.0.0") -> APISpec:
    # Create an APISpec
    spec = APISpec(title=appname, version=version, openapi_version="3.0.3")
    return spec


def swagger_format(param_in, name, type=None, default=None, **other_stuff):
    param = {
        "in": param_in,
        "name": name,
        "schema": {"type": type, **({"default": default} if default else {})},
        **other_stuff,
    }
    return param


def process_type_name(param_type, default=None):
    """Allowed types: array, boolean, integer, number, object, string"""

    types = {
        "list": "array",
        "dict": "object",
        "str": "string",
        "bool": "boolean",
        "int": "integer",
        "float": "number",
        "tuple": "array",
        "it's complicated": "object",
    }

    if not param_type and default:  # assume the type of the default value
        name = type(default).__name__
    elif not param_type:
        name = None
    else:
        try:  # is this a native python type?
            name = param_type.__name__
        except AttributeError:  # ah, so it's from typing?
            name = (
                param_type.__origin__
                if param_type and param_type.__origin__ in types
                else "it's complicated"
            )

    js_name = types.get(name, "")

    return js_name


def swagger_params(function: Callable, **yet_other_stuff):
    positional, named, defaults, types = dashit.parse_args(function)
    print(types, defaults, positional, named)
    path_args = [
        swagger_format(
            param_in="path", name=arg, type=process_type_name(types.get(arg)),
        )
        for arg in positional
    ]
    query_args = (
        [
            swagger_format(
                param_in="query",
                name=arg,
                type=process_type_name(types.get(arg), default),
                default=default,
            )
            for default, arg in zip(defaults, named)
        ]
        if defaults and named
        else []
    )

    return path_args + query_args


def register_swag(app, spec, func, path):
    docstring = func.__doc__ if func.__doc__ else ""

    spec.path(
        path=path.replace("<", "{").replace(">", "}"),
        operations={
            "get": {
                "responses": {
                    "200": {  # TODO: add info on expected return type
                        "description": "Success!"
                    },
                },
                "summary": docstring.split("\n")[0],
                "description": docstring,
            }
        },
        parameters=swagger_params(func),
    )
    return path


def register_function_spec(app: Union[flask.Flask, dash.Dash], spec: APISpec):
    # Register the path and the entities within it
    APP_BASE = app.config.get("url_base_pathname") or app.config.get(
        "APPLICATION_ROOT", "/"
    )
    server = app if isinstance(app, flask.Flask) else app.server
    view_functions = server.view_functions
    # print(view_functions)
    for name, function in view_functions.items():
        if name[0] != "_" and f"{APP_BASE}_" not in name:
            with server.test_request_context():
                spec.path(view=function)
    return server


def register_swagger_endpoints(app: Union[flask.Flask, dash.Dash], spec: APISpec):
    APP_BASE = app.config.get("url_base_pathname") or app.config.get(
        "APPLICATION_ROOT", "/"
    )
    server = app if isinstance(app, flask.Flask) else app.server
    swagger_endpoint = f"""{APP_BASE}swagger"""

    swagger_ui = f"""<!DOCTYPE html>
    <html>
      <head>
        <title>Swagger</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" type="text/css" href="//unpkg.com/swagger-ui-dist@3/swagger-ui.css" />
      </head>
      <body>
        <div id="swagger-ui"></div>
        <script src="//unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js"></script>
        <script>
        const ui = SwaggerUIBundle({{
            url: "{swagger_endpoint}",
            dom_id: '#swagger-ui',
            presets: [
              SwaggerUIBundle.presets.apis,
              SwaggerUIBundle.SwaggerUIStandalonePreset
            ],
            layout: "BaseLayout",
            requestInterceptor: (request) => {{
              request.headers['X-CSRFToken'] = "{{{{ csrf_token }}}}"
              return request;
            }}
          }})
        </script>
      </body>
    </html>"""

    @server.route(f"{APP_BASE}swagger_ui")
    def serve_swagger_ui():
        return swagger_ui

    @server.route(swagger_endpoint)
    def serve_swagger_spec():
        return json.dumps(spec.to_dict())

    print("Swagger at: " + swagger_endpoint)
    return server
