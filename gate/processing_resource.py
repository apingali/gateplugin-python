from document import Document
from corpus import Corpus
import sys, json, codecs, inspect

def fill_params(params, function):
	"""
		Uses reflection to safely call method with scriptParams as values.
	"""
	args, _varargs, _keywords, defaults = inspect.getargspec(function)

	if defaults and args:
		defaults_offset = len(args) - len(defaults)
		defaults = {args[defaults_offset + index]: value for index, value in enumerate(defaults)}
	else:
		defaults = {}
	execParams = {
		arg: params.get(arg, defaults.get(arg)) for arg in args if arg in params or arg in defaults
	}

	return execParams

class ProcessingResource(object):
	def __init__(self):
		self.logger = []
		self.scriptParams = dict()
		self.inputAS = None
		self.outputAS = None
		self.input_line = ""
		self.document = None

	def start(self):
		line = sys.stdin.readline().strip()
		while line:
			line = codecs.decode(line, "utf8")

			if line:
				self.input_line = line
				input_json = json.loads(line)

				if "command" in input_json:
					if input_json["command"] == "BEGIN_EXECUTION":
						self.corpus = Corpus(input_json)
						self.scriptParams = input_json["parameterMap"]

						self.init(**fill_params(self.scriptParams, self.init))
						self.beginExecution()

					elif input_json["command"] == "ABORT_EXECUTION":
						self.abortExecution()
						return
					elif input_json["command"] == "END_EXECUTION":
						self.endExecution()
						return
				else:
					self.document = Document.load(input_json)
					self.inputAS = self.document.annotationSets[self.scriptParams.get("inputAS", None)]
					self.outputAS = self.document.annotationSets[self.scriptParams.get("outputAS", None)]

					self.execute(self.document, **fill_params(self.scriptParams, self.execute))

					print json.dumps(self.document.logger)
					sys.stdout.flush()

			line = sys.stdin.readline().strip()

	def init(self):
		pass

	def execute(self, document):
		raise NotImplementedError("No execute method for pipeline")

	def beginExecution(self):
		pass

	def endExecution(self):
		pass

	def abortExecution(self):
		pass

def executable(function):
	"""Decorator which adds ProcessingResource methods to the given executable function"""
	inner_pr = ProcessingResource()
	inner_pr.execute = function
	function.start = inner_pr.start
	return function