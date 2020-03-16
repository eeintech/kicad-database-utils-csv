#!/usr/bin/env python
import sys, os
import json, pickle

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
		if self.library:
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

		# Parse Component Name
		try:
			parse_comp['name'] = component.name
		except:
			print('[ERROR] Parse: Component name not found')
			return {}

		# Parse Reference
		# try:
		# 	parse_comp['reference'] = component.definition['reference']
		# except:
		# 	print('[ERROR] Parse: Reference not found')
		# 	return {}

		# parse_comp[name] = {'definition' : {}}
		# for key, value in component.definition.items():
		# 	parse_comp[name]['definition'].update({key : value})

		for index, field in enumerate(component.fields):
			if index == 0:
				parse_comp['reference'] = field['reference'].replace('"','')
			elif index == 1:
				parse_comp['value'] = field['name'].replace('"','')
			elif index == 2:
				parse_comp['footprint'] = field['name'].replace('"','')
			else:
				key = 'f' + str(index)
				if 'fieldname' in field.keys():
					parse_comp[key + '_value'] = field['fieldname'].replace('"','')
				else:
					parse_comp[key + '_value'] = ''

				if 'name' in field.keys():
					parse_comp[key + '_name'] = field['name'].replace('"','')
				else:
					parse_comp[key + '_name'] = ''


		# parse_comp[name].update({'fields' : []})
		# for item in component.fields:
		# 	parse_comp[name]['fields'].append(item)

		#print(component.draw)

		# print(f'name: {component.name}')
		# # print(f'comments:')
		# # for comment in component.comments:
		# # 	print(f'{comment}', end='')
		# print(f'definition: {component.definition["name"]} {component.definition["reference"]}')
		# print(f'fields:')
		# for index, field in enumerate(component.fields):
		# 	try:
		# 		print(f'F{index} {field["fieldname"]} {field["name"]}')
		# 	except:
		# 		try:
		# 			print(f'F{index} {field["name"]}')
		# 		except:
		# 			pass

		return parse_comp

	def ParseLibrary(self):
		parse_lib = []
		for component in self.library.components:
			# try:
			parse_lib.append(self.ParseComponentData(component))
			# except:
			# 	pass

		return parse_lib

# MAIN
if __name__ == '__main__':
	if len(sys.argv) > 1:
		klib = KicadLibrary(sys.argv[1])
		#print(klib.GetAllPartsByName())
		printDict(klib.parse)
