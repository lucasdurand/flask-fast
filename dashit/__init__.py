from typing import List, Callable, Union, Tuple, Any, Dict

from functools import partial
import inspect
import pandas as pd

import flask
import json

import dash
import dash_html_components as html
import dash_core_components as dcc


class DashitError(Exception):
    pass


def generate_rule(f: Callable, app: Union[dash.Dash, flask.Flask]) -> str:
    """
    Generate Flask rule to map URL positional and query params to function inputs
    """

    # Pull base url from either Flask or Dash app config.
    APP_BASE = app.config.get("APPLICATION_ROOT") or app.config.get("url_base_pathname")
    ENDPOINT = f.__name__

    positional, _, _, _ = parse_args(f)
    url_args = "".join([f"/<{arg}>" for arg in positional])

    rule = f"{APP_BASE}{ENDPOINT}{url_args}"
    return rule


def parse_args(f: Callable):

    argspec = inspect.getfullargspec(f)
    args = argspec.args
    defaults = argspec.defaults
    positional, named = (
        args[: -len(defaults) if defaults else None],
        args[-len(defaults) if defaults else None :],
    )
    types = argspec.annotations
    return positional, named, defaults, types


def whats_the_url(
    func: Callable, app: Union[dash.Dash, flask.Flask], *args, **kwargs
) -> str:
    """Generate the url to GET the function once you `dashit`"""

    signature = inspect.signature(func)
    call_errors = ["missing a required argument", "unexpected keyword argument"]
    try:
        arguments = signature.bind(*args, **kwargs).arguments
    except TypeError as e:
        if any([error in str(e) for error in call_errors]):
            msg = f"{e}. {func.__name__} is called like {func.__name__}{signature}"
            raise DashitError(msg) from e
        else:
            raise

    args = arguments.pop("args", [])
    kwargs = arguments.pop("kwargs", {})
    url = rule = generate_rule(func, app)
    print(args, kwargs, rule)
    # postional args
    for arg, val in arguments.items():
        url = url.replace(f"<{arg}>", json.dumps(val))
    # query params
    url += "?"
    url += "&".join([f"{keyword}={str(val)}" for keyword, val in kwargs.items()])
    url = url.strip("?")

    return url


def eval_params() -> Dict[str, Any]:
    """Attempt to evaluate dictionary values as python code, else return them as is"""
    import ast

    kwargs = {}
    for k, v in flask.request.args.to_dict(flat=True).items():
        try:
            kwargs[k] = json.loads(v)
        except:
            kwargs[k] = v
    return kwargs


def inject_flask_params_as_kwargs(func, **kwargs):
    """Flask converts the url variables into kwargs. We pass those back to our function as args. We also want to inject as kwargs the optional URL parameters"""
    positional = kwargs

    params = (
        eval_params()
    )  # &var1=["this"]&another=true -> {"var":["this"],"another":"true"}

    call_errors = ["missing a required argument", "unexpected keyword argument"]

    try:
        value = func(**positional, **params)

    except TypeError as e:
        if any([error in str(e) for error in call_errors]):
            signature = inspect.signature(func)
            msg = f"{func.__name__} is called like {func.__name__}{signature}. {e}."
            raise DashitError(msg) from e
        else:
            raise

    return value


def add_rule(app: Union[flask.Flask, dash.Dash], f: Callable):
    """
    Register function as Flask route. Positional and named arguments are all required. 
    In order to handle optional arguments, use **kwargs. *args is right out.
    """
    rule = generate_rule(f, app)

    server = app if isinstance(app, flask.Flask) else app.server
    server.add_url_rule(
        rule, endpoint=f.__name__, view_func=partial(_all_the_small_things, function=f)
    )
    f.url = partial(whats_the_url, f, server)
    return rule


def handle_wacky_types(thing):
    if isinstance(thing, pd.DataFrame):
        thing = thing.to_json(orient="table")
    return thing


def _all_the_small_things(function, **kwargs):
    response = inject_flask_params_as_kwargs(function, **kwargs)
    response = handle_wacky_types(response)
    return response


def dashit(functions: List[Callable], appname: str):
    """
    Create a QUICK Dash app exposing your functions as API endpoints!
    
    endpoint url:  
    
    All positional arguments will be required in the url. Named and keyword args are passed as query params.
    """

    app = dash.Dash(__name__, url_base_pathname=f"/{appname}/")

    new_routes = [
        {
            "name": func.__name__,
            "docstring": inspect.cleandoc(func.__doc__) if func.__doc__ else "",
            "endpoint": add_rule(app, func),
        }
        for func in functions
    ]

    def generate_endpoint_html(route):
        return (
            dcc.Markdown(
                [f"""**{route["name"]}:** [{route["endpoint"]}]({route["endpoint"]})"""]
            ),
            html.Blockquote([dcc.Markdown([route["docstring"]])]),
        )

    flatten = lambda l: [item for sublist in l for item in sublist]

    app.layout = html.Div(
        [
            html.H1([appname]),
            html.H3(
                ["DASHIT: Functions Are APIs Now."]
            ),  # some explanation on how the app works. Use function docstring.
            html.Div(flatten([generate_endpoint_html(route) for route in new_routes])),
        ]
    )
    print(new_routes)

    return app
