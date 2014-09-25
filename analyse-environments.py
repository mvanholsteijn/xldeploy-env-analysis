# Analyzer of differences between properties in different environments in the XL Deploy repository.
# see README.md for details.
# author: Mark van Holsteijn
from java.io import File
import re
import getopt
import sys
import collections
import datetime

# A dictionary with all dictionaries from an Deployit environment.
#
class AggregateDictionary(object):
	def __init__(self, full_name):
		self.full_name = full_name
		parts = re.compile('/').split(full_name)
		self.short_name = parts[len(parts)-1]
		self.values = {}
		self.diagnostics = []

	def load(self):
		self.values = {}
		existing_keys = {}
		dictionary_entries = repository.search('udm.Dictionary', self.full_name)
		for name in dictionary_entries:
			dictionary = repository.read(name)
			for entry in dictionary.entries.entrySet():
				if entry.key not in existing_keys:
					existing_keys[entry.key] = name
					self.values[entry.key] = entry.value
				else:
					diagnostic = "ERROR: definition of %s both defined in %s and in %s\n" % (entry.key, name, existing_keys[entry.key])
					sys.stderr.write(diagnostic)
					sys.stderr.flush()
					self.diagnostics.add(diagnostic)
					

	def keys(self):
		return self.values.keys()

	def value(self, key):
		return self.values[key] if key in self.values else None

	def write(self, out = sys.stdout):
		for key in self.values:
			out.write("%s=%s\n" % (key, self.values[key]))

	def html_report(self, output):
		if len(self.diagnostics) != 0:
			output.write("<p>Diagnostics from environment %s<ul>" % self.short_name)
			for diagnostic in self.diagnostics:
				output.write("<li>%s</li>" % diagnostic)
			output.write("</ul></p>")
				


class EnvironmentComparator(object):
	def __init__(self):
		self.dictionaries = {}
		self.keys = set()
		self.environments = []
		self.reference = None
		self.overview = {}

	def add(self, dictionary):
		self.dictionaries[dictionary.short_name] = dictionary
		self.keys = self.keys.union(dictionary.keys())
		self.environments.append(dictionary.short_name)
		#self.environments.add(dictionary.short_name)
		if not self.reference:
			self.reference = dictionary.short_name

	def analyze(self):
		for key in self.keys:
			env_compare_result = {}
			for env in self.environments:
				compare_result = {}
				for other_env in self.environments:
					if env != other_env:
						left_value = self.dictionaries[env].value(key)
						right_value = self.dictionaries[other_env].value(key)
						compare_result[other_env] = (left_value == right_value)
				env_compare_result[env] = compare_result
			self.overview[key] = env_compare_result

	def html_report(self, output):
		output.write("<html><head><title>XLDeploy environment analysis dated %s</title></head><body>\n" % str(datetime.date.today()))
		output.write("<p>Total of %d different keys found in %d environments</p>" % (len(self.keys), len(self.environments)))
		output.write('<table><tr>')
		output.write('<td>key</td>')
		for env in self.environments:
			output.write('<td>%s</td>' % env)
		output.write('</tr>\n')

		for key in sorted(self.keys):
			output.write('<tr><td>%s</td>' % key)
			for env in self.environments:
				same_as = set()
				for other_env in self.environments:
					if env != other_env:
						if self.overview[key][env][other_env]:
							same_as.add(other_env)
				if len(same_as) == 0:
					bgcolor = 'green'
					fgcolor = 'white'
					content = 'different from all other environments'
				elif len(same_as) == len(self.environments)-1:
					bgcolor = 'orange'
					fgcolor = 'black'
					content = 'same in all environments'
				else:
					bgcolor = 'red'
					fgcolor = 'white'
					content = "value in %s is the same as in " % env
					for n, env in enumerate(same_as):
						if n == len(same_as):
							content += 'and '
						elif n != 0:
							content += ', '
						content += env

				output.write('<td align="center" style="color:%s; background-color:%s;">%s</br>%s</td>' % (fgcolor, bgcolor, content, self.dictionaries[env].value(key)))
			output.write('</tr>\n')
		output.write('</table>\n')
		for name in self.dictionaries:
			self.dictionaries[name].html_report(output)
		output.write('</body></html>\n')
		output.flush()


import getopt, sys

def usage():
	sys.stderr.write("Usage:%s [output=<file>] env env [env..]\n" % sys.argv[0])
	sys.stderr.write("You need to specify  two or more environments to compare\n")
	
def main():
	filename = None
	comparator = EnvironmentComparator()

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'o:', ['output='])
	except getopt.GetoptError, err:
		usage()
		print str(err)
		sys.exit(2)

	for option, argument in opts:
		if option in ('-o', '-output'):
			filename = File(argument)

	if len(args) < 2:
		usage()
		sys.exit(2)
		
	for entry in args:
		dictionary = AggregateDictionary(entry)
		dictionary.load()
		comparator.add(dictionary)

	comparator.analyze()

	output = open(str(filename), 'w') if filename else sys.stdout
	comparator.html_report(output)
	if filename: 
		print 'Report written to %s' % filename.canonicalPath
		output.close() 

main()
