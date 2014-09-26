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
				

class KeyComparator(object):
	def __init__(self,  all_environments, dictionaries):
		self.all_environments = all_environments
		self.dictionaries = dictionaries

		self.key = None
		self.env = None
		self.match_count = 0
		self.percentage = 0
		self.matching_environments = set()
		self.total_match_count = 0

	def set_key_and_environment(self, key, env):
		self.key = key
		self.env = env
		if self.key and self.env:
			self.compare()

	def set_environment(self, env):
		self.env = env
		if self.key and self.env:
			self.compare()

	def compare(self):
		self.match_count = 0
		self.percentage = 0
		self.matching_environments = set()
		for other_env in self.all_environments:
			left_value = self.dictionaries[self.env].value(self.key)
			right_value = self.dictionaries[other_env].value(self.key)
			if self.env != other_env and left_value == right_value:
				self.match_count += 1
				self.matching_environments.add(other_env)
		self.percentage = int (self.match_count * 100.0 / (len(self.all_environments) - 1))

	def color_for_percentage(self, percentage):
		point = collections.namedtuple('Color', ['background', 'foreground'])
		if percentage == 0:
			result = point("green", "white")
		elif percentage == 100:
			result = point("orange", "black")
		else:
			result = point("red", "white")
		return result

	def color(self):
		return self.color_for_percentage(self.percentage)

	def analytic(self):
		if self.percentage == 0:
			result = 'different from all other environments'
		elif self.percentage == 100:
			result = 'same in all environments'
		else:
			result = "value in %s is the same as in " % self.env
			for n, env in enumerate(self.matching_environments):
				if n == len(self.matching_environments):
					result += 'and '
				elif n != 0:
					result += ', '
				result += env
		return result

	def key_color(self, key):
		self.key = key
		self.total_match_count = 0

		for env in self.all_environments:
			self.set_environment(env)
			self.total_match_count += self.match_count
		self.total_percentage = int (self.total_match_count * 100.0 / (len(self.all_environments) * (len(self.all_environments) - 1)))

		return self.color_for_percentage(self.total_percentage)


class EnvironmentComparator(object):
	def __init__(self):
		self.dictionaries = {}
		self.keys = set()
		self.environments = []

	def add(self, dictionary):
		self.dictionaries[dictionary.short_name] = dictionary
		self.keys = self.keys.union(dictionary.keys())
		self.environments.append(dictionary.short_name)

	def html_report(self, output):
		output.write("<html><head><title>XLDeploy environment analysis dated %s</title></head><body>\n" % str(datetime.date.today()))
		output.write("<p>Total of %d different keys found in %d environments</p>" % (len(self.keys), len(self.environments)))
		output.write('<table><tr>')
		output.write('<td>key</td>')
		for env in self.environments:
			output.write('<td>%s</td>' % env)
		output.write('</tr>\n')

		key_comparator = KeyComparator(self.environments, self.dictionaries)
		for key in sorted(self.keys):
			color = key_comparator.key_color(key)
			output.write('<tr><td style="color:%s; background-color:%s;">%s</td>' % (color.foreground, color.background, key))
			for env in self.environments:
				key_comparator.set_key_and_environment(key,env)
				color = key_comparator.color()
				output.write('<td align="center" style="color:%s; background-color:%s;">%s</br>%s</td>' % (color.foreground, color.background, key_comparator.analytic(), self.dictionaries[env].value(key)))
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

	output = open(str(filename), 'w') if filename else sys.stdout
	comparator.html_report(output)
	if filename: 
		print 'INFO: Report written to %s' % filename.canonicalPath
		output.close() 

main()
