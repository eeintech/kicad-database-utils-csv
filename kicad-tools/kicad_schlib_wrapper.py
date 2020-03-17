#!/usr/bin/env python
import sys, os, csv
import json, pickle

# CSV DEFAULT OUTPUT FILE PATH
CSV_OUTPUT_PATH = './libraries/'

# Import KiCad schematic library utils
try:
	from schlib import SchLib
except:
	# When this file is executed directly
	sys.path.append('kicad-library-utils/schlib')
	from schlib import SchLib

def printDict(dictionary):
	print(json.dumps(dictionary, indent = 4, sort_keys = True))

# COMPONENT LIBRARY MANAGER
class KicadLibrary(object):

	def __init__(self, file):
		self.version = 'kicad-library-0.1'
		self.file = file
		if self.file:
			self.library = self.OpenLibrary()
			try:
				self.name = self.file.split('/')[-1]
			except:
				self.name = self.file
		if self.library:
			print(f'Parsing {self.name} library')
			self.parse = self.ParseLibrary()
		else:
			self.parse = None

	def OpenLibrary(self):
		# Check if valid library file
		if not '.lib' in self.file:
			print('Not a library file')
			return None
		else:
			# Load library
			library = SchLib(self.file)
			return library

	def GetAllPartsByName(self):
		components = []
		for component in self.library.components:
			components.append(component.name)

		return components

	def ParseComponentData(self, component):
		parse_comp = {}

		# Parse name
		try:
			parse_comp['name'] = component.name
		except:
			print('[ERROR] Parse: Component name not found')
			return {}

		# Parse documentation
		try:
			parse_comp['description'] = component.documentation['description']
			parse_comp['datasheet'] = component.documentation['datasheet']
			parse_comp['keywords'] = component.documentation['keywords']
		except:
			print('[ERROR] Parse: Component documentation not found')
			return {}

		# Parse fields
		for index, field in enumerate(component.fields):
			if index == 0:
				parse_comp['reference'] = field['reference'].replace('"','')
				#parse_comp['reference'] = component.definition['reference']
			elif index == 1:
				parse_comp['value'] = field['name'].replace('"','')
			elif index == 2:
				parse_comp['footprint'] = field['name'].replace('"','')
			else:
				if 'fieldname' in field.keys():
					try:
						fieldname = field['fieldname'].lower().replace('"','').replace(' ','_').replace('(','').replace(')','')
					except:
						fieldname = field['fieldname'].lower()
					if fieldname != '':
						# Find value
						if 'name' in field.keys():
							parse_comp[fieldname] = field['name'].replace('"','')
						else:
							parse_comp[fieldname] = ''

		#print(component.draw)

		return parse_comp

	def ParseLibrary(self):
		parse_lib = []
		for component in self.library.components:
			# try:
			parse_lib.append(self.ParseComponentData(component))
			# except:
			# 	pass

		return parse_lib

	def ExportToCSV(self, csv_output = None):
		if not csv_output:
			try:
				csv_output = CSV_OUTPUT_PATH + self.name.split('.')[-2] + '.csv'
			except:
				csv_output = CSV_OUTPUT_PATH + self.name + '.csv'

		print(f'Exporting library to {csv_output}')

		# Check mapping from all parts
		mapping = {}
		key_count = 0
		for component in self.parse:
			for key in component.keys():
				if key not in mapping.keys():
					mapping[key] = key_count
					key_count += 1

		#print(mapping)

		with open(csv_output, 'w') as csvfile:
			csv_writer = csv.writer(csvfile)
			row_size = len(mapping)

			# Write header
			header = []
			for key in mapping.keys():
				header.append(key)
			csv_writer.writerow(header)

			# Write line for each component
			for component in self.parse:
				row = []
				count = 0
				for column in range(row_size):
					col_value = ''
					for key, value in component.items():
						if mapping[key] == count:
							col_value = value
							break

					row.append(col_value)
					count += 1

				#print(row)
				csv_writer.writerow(row)

# MAIN
if __name__ == '__main__':
	if len(sys.argv) > 1:
		klib = KicadLibrary(sys.argv[1])
		#print(klib.GetAllPartsByName())
		#printDict(klib.parse)
		klib.ExportToCSV()
