from typing import List, Callable

from functools import partial
import inspect
import pandas as pd

import flask
    
import dash
import dash_html_components as html
import dash_core_components as dcc

def whats_the_url(function: Callable, app, *args, **kwargs):
    """Generate the url to GET the function once you `dashit`"""
    url = ""
    rule = generate_rule(function, app)
    for i,arg in inspect.getfullargspec(function).args:
        rule = rule.replace(f"<{arg}>", args[i])
    return url

def generate_rule(f, app):
    """
    Generate Flask rule to map URL positional and query params to function inputs
    """

    APP_BASE = app.config["url_base_pathname"]

    argspec = inspect.getfullargspec(f)
    argspec

    BASE = f.__name__
    args = argspec.args
    args = "".join([f"/<{arg}>" for arg in argspec.args])

    rule = f"{APP_BASE}{BASE}{args}"        
    return rule

def whats_the_url(function: Callable, app, *args, **kwargs):
    """Generate the url to GET the function once you `dashit`"""
    arguments = inspect.signature(function).bind(*args,**kwargs).arguments
    args = arguments.pop("args",[])
    kwargs = arguments.pop("kwargs",{})
    url = rule = generate_rule(function, app)
    print(args, kwargs, rule)
    # postional args
    for arg, val in arguments.items():
        url = url.replace(f"<{arg}>", str(val))
    # query params
    url += "?"
    url += "&".join([f"{keyword}={str(val)}" for keyword, val in kwargs.items()])
    url = url.strip("?")
    return url

def dashit(functions: List[Callable], appname: str):
    """
    Create a QUICK Dash app exposing your functions as API endpoints!
    
    endpoint url:  
    
    All positional and named arguments will be required in the url
    """
    app = dash.Dash(__name__, url_base_pathname = f"/{appname}/")

    def eval_params(dict):
        """Attempt to evaluate dictionary values as python code, else return them as is"""
        import ast
        kwargs = {}
        for k,v in flask.request.args.to_dict(flat=True).items():
            try:
                kwargs[k] = ast.literal_eval(v)
            except:
                kwargs[k] = v
        return kwargs

    def inject_flask_params_as_kwargs(func, **kwargs):
        """Flask converts the url variables into kwargs. We pass those back to our function as args. We also want to inject as kwargs the optional URL parameters"""
        args = kwargs
        # kwargs = flask.request.args.to_dict(flat=False) &var=1&var=2 -> var:[1,2]
        kwargs = eval_params(flask.request.args.to_dict(flat=True)) #&var1=["this"]&another=true -> {"var":["this"],"another":"true"} 
        # TODO: ast.literal_eval on args to catch bools, dicts, etc.s
        print(args, kwargs)
        return func(**args, **kwargs )

    def handle_wacky_types(thing):
        if isinstance(thing, pd.DataFrame):
            thing = thing.to_json(orient="table")
        return thing
    
    def all_the_small_things(func, **kwargs):
        response = inject_flask_params_as_kwargs(func, **kwargs)
        response = handle_wacky_types(response)
        return response

    
    def add_rule(app, f):
        """
        Register function as Flask route. Positional and named arguments are all required. 
        In order to handle optional arguments, use **kwargs. *args, is right out.
        """
        rule = generate_rule(f, app)
        app.server.add_url_rule(rule, endpoint = f.__name__, view_func = partial(all_the_small_things,func=f))
        return rule

    new_routes = [{"name": func.__name__, "docstring": inspect.cleandoc(func.__doc__) if func.__doc__ else "", "endpoint": add_rule(app,func)} for func in functions]

    def generate_endpoint_html(route):
        return dcc.Markdown([f"""**{route["name"]}:** [{route["endpoint"]}]({route["endpoint"]})"""]), html.Blockquote([dcc.Markdown([route["docstring"]])])
    flatten = lambda l: [item for sublist in l for item in sublist]

    app.layout = html.Div([
        html.H1([appname]),
        html.H3(["DASHIT: Functions Are APIs Now."]), #some explanation on how the app works. Use function docstring.
        html.Div(flatten([
            generate_endpoint_html(route) for route in new_routes
        ]))
    ])
    print(new_routes)
    
    return app
