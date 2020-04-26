from . import swagger, api

from flask import Flask
from typing import List, Callable, Optional


# appname -> endpoint
# init with appname which is optional and only used for swagger title and root/base_url

# endpoint / appname / title all optional

# make this a class-first implementation ...

class FastFlask:
	def __init__(self, functions: List[Callable], appname:str, app:Optional[Flask]=None, spec:Optional[swagger.APISpec]=None, version:str="1.0.0"):
		self.spec = spec
		self.app = app
		self.version = version
		self.functions = {}
		self.flask_fast(appname=appname, functions=functions)
	
	def flask_fast(self, functions: List[Callable], appname:str):
		self.app, self.spec = api.flaskit(functions=functions, appname=appname, app=self.app, spec=self.spec, version=self.version)	
		self.functions[appname]=functions

	def add_endpoint(self, endpoint, functions):
		self.flask_fast(functions=functions, appname=endpoint)

	def endpoints(self):
		return self.app.url_map

	def function(self, endpoint:str, fname:str):
		endpoint = self.functions.get(endpoint,[])
		named_functions = {f.__name__: f for f in endpoint}
		function = named_functions.get(fname)
		return function


	def url(self, endpoint:str, fname:str):
		"""Return the GET URL that corresponds to the function call signature"""
		function = self.function(endpoint=endpoint, fname=fname)
		return function.url

	def run(*args, **kwargs):
		return self.app.run(*args, **kwargs)

	def __repr__(self):
		return str(self.endpoints())