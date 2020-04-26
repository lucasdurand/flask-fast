from typing import List, Callable, Union, Tuple, Any, Dict, Optional

from functools import partial
import inspect
import pandas as pd

import flask
import json

import dash
import dash_html_components as html
import dash_core_components as dcc

from . import swagger

class FastFlaskError(Exception):
    pass


def generate_rule(f: Callable, app: flask.Blueprint):
    """
    Generate Flask rule to map URL positional and query params to function inputs
    """

    ENDPOINT = f.__name__

    positional, _, _, _ = parse_args(f)
    url_args = "/".join([f"<{arg}>" for arg in positional])

    rule = f"{ENDPOINT}/{url_args}"
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
    func: Callable, app: flask.Blueprint, *args, **kwargs
) -> str:
    """Generate the url to GET the function once you `dashit`"""

    signature = inspect.signature(func)
    call_errors = ["missing a required argument", "unexpected keyword argument"]
    try:
        arguments = signature.bind(*args, **kwargs).arguments
    except TypeError as e:
        if any([error in str(e) for error in call_errors]):
            msg = f"{e}. {func.__name__} is called like {func.__name__}{signature}"
            raise FastFlaskError(msg) from e
        else:
            raise

    these_arguments = arguments.copy() 
    kwargs = arguments.pop("kwargs", {})
    url = rule = generate_rule(func, app)
    # postional args
    for arg in arguments:
        if f"/<{arg}>" in url:
            url = url.replace(f"<{arg}>", json.dumps(these_arguments.pop(arg)))

    these_arguments.update(kwargs)
    # query params
    url += "?"
    url += "&".join([f"{keyword}={json.dumps(val)}" for keyword, val in these_arguments.items()])
    url = url.strip("?")
    url = f"{app.url_prefix}/{url}"
    return url


def eval_params(params) -> Dict[str, Any]:
    """Attempt to evaluate dictionary values as python code, else return them as is"""

    kwargs = {}
    for k, v in params:
        try:
            kwargs[k] = json.loads(v)
        except:
            kwargs[k] = v
    return kwargs


def inject_flask_params_as_kwargs(func, **kwargs):
    """Flask converts the url variables into kwargs. We pass those back to our function as args. We also want to inject as kwargs the optional URL parameters"""
    positional = eval_params(kwargs.items())
    params = (
        eval_params(flask.request.args.to_dict(flat=True).items())
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


def add_rule(blueprint: flask.Blueprint, f: Callable):
    """
    Register function as Flask route. Positional and named arguments are all required. 
    In order to handle optional arguments, use **kwargs. *args is right out.
    """
    rule = generate_rule(f, blueprint)
    view_func = partial(_all_the_small_things, function=f)
    view_func.__doc__ = f.__doc__
    blueprint.add_url_rule(
        rule, endpoint=rule.replace(blueprint.url_prefix,"",1), view_func=view_func
    )
    f.url = partial(whats_the_url, f, blueprint)
    f.rule = rule
    return rule


def handle_wacky_types(thing):
    """Not really a good idea to keep this"""
    if isinstance(thing, pd.DataFrame):
        thing = thing.to_json(orient="table")
    return thing


def _all_the_small_things(function, **kwargs):
    response = inject_flask_params_as_kwargs(function, **kwargs)
    response = handle_wacky_types(response)
    return response

def make_blueprint(functions: List[Callable], appname:str, spec:Optional[swagger.APISpec]=None, version:str=""):
    blueprint = flask.Blueprint(f"instantapi-{appname}", __name__, url_prefix=f"/api/{appname}")
    spec = spec or swagger.create_apispec(appname=appname, version=version)
    paths = [swagger.register_swag(app=blueprint, spec=spec, func=func, path=add_rule(blueprint=blueprint, f=func)) for func in functions]
    return blueprint, spec

def flaskit(functions: List[Callable], appname:str, app:Optional[flask.Flask]=None, spec:Optional[swagger.APISpec]=None, version:str="1.0.0") -> Tuple[flask.Flask, swagger.APISpec]:
    app = app or flask.Flask(__name__)
    blueprint, spec = make_blueprint(functions, appname=appname, spec=spec, version=version)
    app.register_blueprint(blueprint)
    
    try:
        swagger_blueprint, _ = make_blueprint([], "")
        swagger.register_swagger_endpoints(app=swagger_blueprint, spec=spec)
        app.register_blueprint(swagger_blueprint)
    except AssertionError as e:
        if not "A name collision" in str(e):
            raise
    print(app.url_map)
    return app, spec

def dashit(functions: List[Callable], appname: str, app:Optional[dash.Dash]=None, server:Optional[flask.Flask]=None, version:str="1.0.0") -> Tuple[dash.Dash, swagger.APISpec]:
    """
    Why does this exist? It's just the flask app with an empty home page ... 
    If we wanted to append to an existing Dash app, we can just use flaskit on app.server ...
    
    Create a QUICK Dash app exposing your functions as API endpoints!
        
    All positional arguments will be required in the url. Named and keyword args are passed as query params.
    """
    
    app = app or dash.Dash(__name__, server, url_base_pathname=f"/{appname}/")

    server = app.server or server

    server, spec = flaskit(functions=functions, appname=appname, app=server, version=version)
    app.server = server
    app.layout = app.layout or html.Div(html.A("/api",href="/api"))

    print(app.server.url_map)
    return app, spec