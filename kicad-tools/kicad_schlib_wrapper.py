#!/usr/bin/env python
import sys, os, csv, json

### DEBUG ONLY
LIB_SAVE = True
ADD_ENABLE = False
DELETE_ENABLE = False

# CSV DEFAULT OUTPUT FILE PATH
CSV_OUTPUT_PATH = './library_csv/'

# Import KiCad schematic library utils
try:
	from schlib import SchLib
except:
	# When this file is executed directly
	sys.path.append('kicad-library-utils/schlib')
	from schlib import SchLib

def printDict(dictionary):
	print()
	print(json.dumps(dictionary, indent = 4, sort_keys = True))

# KICAD LIBRARY CLASS
class KicadLibrary(object):

	def __init__(self, lib_file, csv_file = None):
		self.version = 'kicad-library-0.1'
		self.lib_file = lib_file
		self.csv_file = csv_file
		self.lib_parse = None
		self.csv_parse = None

		# Define library name
		try:
			self.name = self.lib_file.split('/')[-1]
		except:
			self.name = self.lib_file

		# Process library file
		self.library = self.OpenLibrary()
		if self.library:
			print(f'Library: Parsing {self.lib_file} file')
			self.lib_parse = self.ParseLibrary()
			#printDict(self.lib_parse)

		# Process CSV file
		if self.csv_file:
			print(f'CSV: Parsing {self.csv_file} file')
			self.csv_parse = self.ParseCSV()
			#printDict(self.csv_parse)

		# Compare both parse information and output diff
		if self.lib_parse and self.csv_parse:
			compare = self.CompareParse()

			if not compare:
				print('No differences found between CSV and LIB files')
			else:
				#printDict(compare)
				# Update library file
				print('Differences found.\n\nUpdating library file\n---')
				self.UpdateLibraryFromCSV(compare)
				print('\n---\nUpdate complete')

	def OpenLibrary(self):
		library = None
		# Check if valid library file
		if not '.lib' in self.lib_file:
			print(f'[ERROR] {self.lib_file} is not a valid library file')
			return library
		else:
			# Load library
			try:
				library = SchLib(self.lib_file)
			except:
				print(f'[ERROR] Cannot read library file {self.lib_file}')
			return library

	def ParseCSV(self):
		csv_db = None
		# Check if valid CSV file
		if not '.csv' in self.csv_file:
			print(f'[ERROR] File {self.csv_file} is not a valid CSV')
			return csv_db

		# Check if file exist
		if not os.path.exists(self.csv_file):
			print(f'[ERROR] File {self.csv_file} does not exist')
			return csv_db

		else:
			csv_db = []
			# Parse CSV
			with open(self.csv_file, 'r') as csvfile:
				csv_reader = csv.reader(csvfile)

				# Process header and mapping
				header = csv_reader.__next__()
				mapping = {}
				for index, item in enumerate(header):
					mapping[index] = item

				# Process component information
				for line in csv_reader:
					csv_parse_line = {}
					for index, item in enumerate(line):
						csv_parse_line[mapping[index]] = item
					# Add to parse
					csv_db.append(csv_parse_line)
			
			return csv_db

	def ParseComponent(self, component):
		parse_comp = {}

		# Parse name
		try:
			parse_comp['name'] = component.name
		except:
			print('[ERROR] Parse: Component name not found')
			return {}

		# Parse documentation
		try:
			for key, value in component.documentation.items():
				if value != None:
					parse_comp[key + '_doc'] = value
				else:
					parse_comp[key + '_doc'] = ''
		except:
			print('[ERROR] Parse: Component documentation not found')
			return {}

		# Parse fields
		for index, field in enumerate(component.fields):
			if index == 0:
				parse_comp['reference'] = field['reference']
			else:
				if index == 1:
					fieldname = 'value'
				elif index == 2:
					fieldname = 'footprint'
				else:
					try:
						fieldname = field['fieldname'].lower().replace('"','').replace(' ','_').replace('(','').replace(')','')
					except:
						fieldname = field['fieldname'].lower()

					# If fieldname already exist
					if fieldname in parse_comp.keys():
						fieldname += '_2'

					if fieldname != '':
						# Find value
						if 'name' in field.keys():
							parse_comp[fieldname] = field['name']
						else:
							parse_comp[fieldname] = ''

		return parse_comp

	def ParseLibrary(self):
		parse_lib = []
		for component in self.library.components:
			try:
				parse_lib.append(self.ParseComponent(component))
			except:
				pass

		return parse_lib

	def GetCommonAndDiffKeys(self, part1, part2):
		# Find common keys based on first part of each library file
		common_keys = []
		diff_keys = []
		for key1 in part1.keys():
			for key2 in part2.keys():
				if key1 == key2:
					common_keys.append(key1)
					break

			if key1 not in common_keys:
				diff_keys.append(key1)

		return common_keys, diff_keys

	def CompareParse(self):
		compare = {}

		number_of_parts_to_process = max(len(self.csv_parse), len(self.lib_parse))
		# Check that there are parts in library files
		if not (number_of_parts_to_process > 0):
			print(f'[ERROR] No part found in library and CSV files')
			return compare
		print(f'Processing compare on {number_of_parts_to_process} parts... ', end='')
		
		if ADD_ENABLE:
			compare['part_add'] = []
		if DELETE_ENABLE:
			compare['part_delete'] = []
		compare['part_update'] = {}
		# Find parts to delete from lib
		for lib_part in self.lib_parse:
			delete = True
			for csv_part in self.csv_parse:
				if lib_part['name'] == csv_part['name']:
					delete = False
					# Get common and diff keys
					common_keys, diff_keys = self.GetCommonAndDiffKeys(csv_part, lib_part)
					#print(f'\n\ncommon_keys = {common_keys}\ndiff_keys = {diff_keys}')
					# Check for field discrepancies
					for key in common_keys:
						field_add = False
						field_delete = False
						field_update = False

						if lib_part[key] != csv_part[key]:
							field_update = True

						if field_add or field_delete or field_update:
							if csv_part['name'] not in compare['part_update']:
								compare['part_update'][csv_part['name']] = {}

						if field_update:
							if 'field_update' not in compare['part_update'][csv_part['name']].keys():
								compare['part_update'][csv_part['name']].update({'field_update': {key : csv_part[key]}})
							else:
								compare['part_update'][csv_part['name']]['field_update'].update({key : csv_part[key]})
								
					break
			# Part not found in CSV
			if DELETE_ENABLE:
				if delete:
					compare['part_delete'].append(lib_part['name'])

		# Find parts to add to lib
		for csv_part in self.csv_parse:
			add = True
			for lib_part in self.lib_parse:
				if lib_part['name'] == csv_part['name']:
					add = False
					break
			# Part not found in CSV
			if ADD_ENABLE:
				if add:
					compare['part_add'].append(csv_part['name'])

		if not compare['part_update']:
			compare.pop('part_update')

		return compare

	def UpdateLibraryFromCSV(self, parse_compare):
		if ADD_ENABLE:
			# Process add
			for component_name in parse_compare['part_add']:
				print(f'>> Adding {component_name}')
				self.AddComponentToLibrary(component_name)
		if DELETE_ENABLE:
			# Process delete
			for component_name in parse_compare['part_delete']:
				print(f'>> Deleting {component_name}')
				self.RemoveComponentFromLibrary(component_name)
		# Process update
		count = 0
		for component_name in parse_compare['part_update'].keys():
			print(f'\n[U{count}]\tUpdating {component_name}\n |')
			self.UpdateComponentInLibrary(component_name, parse_compare['part_update'][component_name])
			count += 1

		if LIB_SAVE:
			self.library.save()

	def AddComponentToLibrary(self, component_name):
		print('[ERROR] Adding component to library is not supported yet')

	def RemoveComponentFromLibrary(self, component_name):
		if LIB_SAVE & False:
			#self.library.removeComponent(component_name)
			print('Component', component_name, 'was removed from library')
		else:
			print('[ERROR] Component could not be removed (protected)')

	def UpdateComponentInLibrary(self, component_name, field_data):
		component = self.library.getComponentByName(component_name)
		# Process documentation
		for key, new_value in field_data['field_update'].items():
			if '_doc' in key[-4:]:
				component_key = key[:-4]
				old_value = component.documentation[component_key]
				print(f' {key}: "{old_value}" -> "{new_value}"')

				if new_value != '' and old_value != None:
					component.documentation[component_key] = new_value

		# Process fields
		for index, field in enumerate(component.fields):
			if index == 0:
				# Reference line does not have fieldname key
				# It needs to be handled separately
				if 'reference' in field_data['field_update'].keys():
					old_value = component.fields[index]['reference']
					new_value = field_data['field_update']['reference']
					print(f' reference: {old_value} -> {new_value}')
					component.fields[index]['reference'] = new_value	
			else:
				if index == 1:
					fieldname = 'value'
				elif index == 2:
					fieldname = 'footprint'
				else:
					# User field
					fieldname = (field['fieldname'] + '.')[:-1]
					try:
						fieldname = fieldname.lower().replace('"','').replace(' ','_').replace('(','').replace(')','')
					except:
						fieldname = fieldname.lower()

				#print(f'fieldname = {fieldname}\tfield[fieldname] = {field["fieldname"]}')

				for key, new_value in field_data['field_update'].items():
					if fieldname == key:
						old_value = component.fields[index]["name"]
						print(f' {fieldname}: {old_value} -> {new_value}')
						component.fields[index]['name'] = new_value		

		if LIB_SAVE:
			return True
		else:
			print('[ERROR] Component could not be updated (protected)')
			return False

	def GetAllPartsByName(self):
		components = []
		for component in self.library.components:
			components.append(component.name)

		return components

	def ExportToCSV(self, csv_output = None):
		if not self.lib_parse:
			print('[ERROR] Library parse is empty')
			return

		# Select CSV filename and path
		if csv_output:
			# Check if path exist
			if not os.path.isdir(os.path.dirname(csv_output)):
				raise Exception(f'[ERROR] Path to {csv_output} does not exist')
			# Use user provided CSV filename
			csv_file = csv_output
		else:
			if self.csv_file:
				# Use CSV filename defined in class
				csv_file = self.csv_file
			else:
				# Use autogenerated filename
				try:
					csv_file = CSV_OUTPUT_PATH + self.name.split('.')[-2] + '.csv'
				except:
					csv_file = CSV_OUTPUT_PATH + self.name + '.csv'

		print(f'Exporting library to {csv_file}')

		# Check mapping from all parts
		mapping = {}
		key_count = 0
		for component in self.lib_parse:
			for key in component.keys():
				if key not in mapping.keys():
					mapping[key] = key_count
					key_count += 1

		with open(csv_file, 'w') as csvfile:
			csv_writer = csv.writer(csvfile)
			row_size = len(mapping)

			# Write header
			header = []
			for key in mapping.keys():
				header.append(key)
			csv_writer.writerow(header)

			# Write line for each component
			for component in self.lib_parse:
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

				csv_writer.writerow(row)

# MAIN
if __name__ == '__main__':
	if len(sys.argv) > 2:
		# CSV provided: update library
		klib = KicadLibrary(sys.argv[1], sys.argv[2])
	else:
		# No CSV: generate it
		klib = KicadLibrary(sys.argv[1])
		klib.ExportToCSV()
