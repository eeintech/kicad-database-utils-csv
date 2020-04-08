#!/usr/bin/env python
import sys, os, json, argparse, copy
import csv as csv_tool
import builtins

# Import KiCad schematic library utils
try:
	# When library is imported
	from schlib import SchLib
except:
	# When this file is executed directly from root folder
	sys.path.append('kicad-library-utils/schlib')
	from schlib import SchLib

### DEBUG ONLY
# Verbose if set to True
VERBOSE = True
# More verbose for debug
DEBUG_DEEP = True
# Save library file if set to True
LIB_SAVE = True
# Enable add component method if set to True
ADD_ENABLE = False
# Enable delete component method if set to True
DELETE_ENABLE = False

### GLOBAL SETTINGS
# Library (.lib) and CSV files folders
LIB_FOLDER = None
CSV_FOLDER = None

# New component field offset
POSY_OFFSET = -100

# Overload print function for pretty-print of dictionaries
def print(*args, **kwargs):
	# Check if silent=True is set
	try:
		silent = kwargs.pop('silent')
	except:
		silent = False
	if not silent:
		if type(args[0]) is dict:
			return builtins.print(json.dumps(*args, **kwargs, indent = 4, sort_keys = True))
		else:
			return builtins.print(*args, **kwargs)

### KICAD LIBRARY CLASS
class KicadLibrary(object):

	def __init__(self, name = None, lib_file = None, csv_file = None, silent = True):
		# Version
		self.version = 'kicad-library-0.1'
		# Library file name and extension (path NOT included)
		self.lib_file = lib_file
		# CSV file name and extension (path NOT included)
		self.csv_file = csv_file
		# Parsed list of library components
		self.lib_parse = None
		# Parsed list of csv components
		self.csv_parse = None
		# Store relationship between parse 'label'
		# (space => underscores) and actual field name 
		self.fieldname_lookup_table = {}

		# Define library instance name
		if not name:
			try:
				self.name = self.lib_file.split('/')[-1]
			except:
				self.name = self.lib_file
		else:
			self.name = name

		# Process library file
		if self.lib_file:
			# Load library file from schlib module
			self.library = self.LoadLibrary()
			if self.library:
				# Parse library file
				print(f'Library: Parsing {self.lib_file} file', silent=silent)
				self.lib_parse = self.ParseLibrary()
			# print(self.lib_parse, silent=not(DEBUG_DEEP))

		# Process CSV file
		if self.csv_file:
			# Check if file exists, has a valid format, can be read and contains data
			csv_check = self.CheckCSV()
			if csv_check:
				# Parse CSV file
				print(f'CSV: Parsing {self.csv_file} file', silent=silent)
				self.csv_parse = self.ParseCSV()
			# print(self.csv_parse, silent=not(DEBUG_DEEP))

	def LoadLibrary(self):
		# Check if valid library file
		if not '.lib' in self.lib_file:
			print(f'[ERROR] {self.lib_file} does not have a valid library file format')
			return None
		else:
			try:
				# Load library using schlib module
				library = SchLib(self.lib_file)
			except:
				library = None
				print(f'[ERROR] Cannot read library file {self.lib_file}')

			if len(library.components) == 0:
				print(f'[WARNING] Library file is empty {self.lib_file}')

			return library

	def CheckCSV(self):
		# Check if file exists
		if not os.path.exists(self.csv_file):
			print(f'[ERROR]\tFile {self.csv_file} does not exists')
			print(f'\tUse "-export_csv" argument to export CSV file')
			return False

		# Check if valid CSV file
		if not '.csv' in self.csv_file:
			print(f'[ERROR] File {self.csv_file} does not have a valid CSV file format')
			return False

		# Check if file can be read and contains data
		with open(self.csv_file, 'r') as csvfile:
			try:
				csv_reader = csv_tool.reader(csvfile)
				next_line = csv_reader.__next__()

				if len(next_line) == 0:
					print(f'[WARNING] CSV file is empty {self.csv_file}')
			except:
				print(f'[ERROR] Cannot read CSV file {self.csv_file}')
				return False

		return True

	def ParseCSV(self, csv_input = None):
		csv_db = None

		# Hook to save CSV filename in this method
		if csv_input:
			self.csv_file = csv_input

		csv_db = []
		# Parse CSV
		with open(self.csv_file, 'r') as csvfile:
			csv_reader = csv_tool.reader(csvfile)

			# Process header and mapping
			header = csv_reader.__next__()
			mapping = {}
			for index, item in enumerate(header):
				mapping[index] = self.CleanFieldname(item)
				if item not in self.fieldname_lookup_table.keys():
					self.fieldname_lookup_table[mapping[index]] = '"' + self.RestoreFieldname(mapping[index]) + '"'

			# Process component information
			for line in csv_reader:
				csv_parse_line = {}
				for index, item in enumerate(line):
					csv_parse_line[mapping[index]] = item
				# Add to parse
				csv_db.append(csv_parse_line)
		
		if csv_input:
			self.csv_parse = csv_db
		else:
			return csv_db

	def CleanFieldname(self, fieldname):
		# Return simple fieldname
		return fieldname.lower().replace('"','').replace(' ','_').replace('(','').replace(')','')

	def RestoreFieldname(self, fieldname):
		# Build field name
		new_field_name = []
		fieldname_restored = ''
		# Split user field name
		if '_' in fieldname:
			new_field_name = fieldname.split('_')
		elif ' ' in fieldname:
			new_field_name = fieldname.split(' ')
		else:
			new_field_name.append(fieldname)

		for index, word in enumerate(new_field_name):
			# Capitalize first letter of each word
			new_field_name[index] = word[0].upper() +  word[1:]
			# Add whitespace
			if (index + 1) < len(new_field_name):
				new_field_name[index] += ' '

		for word in new_field_name:
			fieldname_restored += word

		# print(fieldname_restored)
		return fieldname_restored

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
					fieldname = self.CleanFieldname(field['fieldname'])

				# If fieldname already exist
				if fieldname in parse_comp.keys():
					# TODO: Improve handling of multiple instance of same fieldname, if necessary
					fieldname += '2'

				if fieldname != '':
					# Find value
					if 'name' in field.keys():
						parse_comp[fieldname] = field['name']
						
						# Append to lookup table
						try:
							if field['fieldname']:
								self.fieldname_lookup_table[fieldname] = '"' + self.RestoreFieldname(mapping[index]) + '"'
						except:
							pass
					else:
						parse_comp[fieldname] = ''
				else:
					# If also name is empty: process to delete empty user field
					if field['name'] == '""':
						parse_comp['empty'] = field['name']
						# print(f'field = {component.fields[index]}')

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

		for key2 in part2.keys():
			if key2 not in part1.keys():
				diff_keys.append(key2)

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
					# print(f'\n\ncommon_keys = {common_keys}\ndiff_keys = {diff_keys}')
					# Check for field discrepancies
					for key in common_keys:
						# field_add = False
						field_delete = False
						field_update = False

						if lib_part[key]:
							# CSV field exists and fields are different
							if lib_part[key] != csv_part[key] and csv_part[key]:
								field_update = True

							# Handle case where the CSV sheet does not have double-quotes (intention is to delete field from component)
							#if lib_part[key] == '""' and not csv_part[key]:
							if not csv_part[key]:
								field_delete = True

						if field_update:
							try:
								compare['part_update'][csv_part['name']].update({'field_update': {key : csv_part[key]}})
							except:
								if csv_part['name'] not in compare['part_update'].keys():
									compare['part_update'][csv_part['name']] = {}
								compare['part_update'][csv_part['name']].update({'field_update': {key : csv_part[key]}})

						if field_delete:
							try:
								compare['part_update'][csv_part['name']]['field_delete'].update({key : lib_part[key]})
							except:
								if csv_part['name'] not in compare['part_update'].keys():
									compare['part_update'][csv_part['name']] = {}
								compare['part_update'][csv_part['name']].update({'field_delete': {key : lib_part[key]}})

					# Add missing library fields
					for key in diff_keys:
						# Check csv field contains new fields and add to compare
						if key not in lib_part and key in csv_part:
							if len(csv_part[key]) > 0:
								# Add to compare
								try:
									compare['part_update'][csv_part['name']]['field_add'].update({key : csv_part[key]})
								except:
									if csv_part['name'] not in compare['part_update'].keys():
										compare['part_update'][csv_part['name']] = {}
									compare['part_update'][csv_part['name']].update({'field_add': {key : csv_part[key]}})

						# Check if field was removed from CSV part
						if key in lib_part and key not in csv_part:
							# Add to compare
							try:
								compare['part_update'][csv_part['name']]['field_delete'].update({key : lib_part[key]})
							except:
								if csv_part['name'] not in compare['part_update'].keys():
									compare['part_update'][csv_part['name']] = {}
								compare['part_update'][csv_part['name']].update({'field_delete': {key : lib_part[key]}})
								
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

	def UpdateLibraryFromCSV(self, silent = False):
		updated = False

		print(f'\nLibrary Update:\n[1]\t', end='', silent=silent)

		# Compare both parse information and output diff
		if self.lib_parse and self.csv_parse:
			compare = self.CompareParse()
			# print(compare, silent=not(DEBUG_DEEP))

			if not compare:
				# Compare report is empty (no differences between lib and csv found)
				print('No differences found between library and CSV components', silent=silent)
			else:
				# Update library file
				print('Differences found\n[2]\tUpdating library file\n---', silent=silent)
				
		if ADD_ENABLE:
			# Process add
			for component_name in compare['part_add']:
				print(f'>> Adding {component_name}')
				self.AddComponentToLibrary(component_name)
				updated = True

		if DELETE_ENABLE:
			# Process delete
			for component_name in compare['part_delete']:
				print(f'>> Deleting {component_name}')
				self.RemoveComponentFromLibrary(component_name)
				updated = True

		# try:
		# Process update
		if 'part_update' in compare:
			count = 0
			for component_name in compare['part_update'].keys():
				print(f'\n[U{count}]\tUpdating {component_name}\n |')
				self.UpdateComponentInLibrary(component_name, compare['part_update'][component_name])
				count += 1
				updated = True
		# except:
		# 	print('[ERROR] Could not update library part')
		# 	pass

		if updated and LIB_SAVE:
			self.library.save()
		
		if updated:
			if LIB_SAVE:
				print('\n---\nUpdate complete', silent=silent)
		else:
			print('\tUpdate aborted', silent=silent)

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
		# print(component.fields)

		if 'field_update' in field_data:
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
						# Create string copy before altering
						fieldname = (field['fieldname'] + '.')[:-1]
						fieldname = self.CleanFieldname(fieldname)

					# print(f'fieldname = {fieldname}\tfield[fieldname] = {field["fieldname"]}')

					# Update field values
					if fieldname in field_data['field_update'].keys():
						old_value = component.fields[index]["name"]
						new_value = field_data['field_update'][fieldname]	
						try:
							print(f'(F.upd) {self.fieldname_lookup_table[fieldname]} : {old_value} -> {new_value}')
						except:
							print(f'(F.upd) \"{fieldname}\" : {old_value} -> {new_value}')
						try:
							component.fields[index]['name'] = new_value
							# print('\t> Successfully updated')
						except:
							print('\t[ERROR] Field could not be updated')

		# Delete extra fields from lib
		if 'field_delete' in field_data:
			for key, value in field_data['field_delete'].items():
				try:
					print(f'(F.del) {self.fieldname_lookup_table[key]}')
				except:
					print(f'(F.del) \"{key}\"')
				field_index_to_delete = None

				for index, field in enumerate(component.fields):
					# Iterate over user fields only
					if index > 2:
						# Create string copy before altering
						fieldname = (field['fieldname'] + '.')[:-1]
						fieldname = self.CleanFieldname(fieldname)

						if fieldname == key:
							field_index_to_delete = index
							break
						elif fieldname == "":
							field_index_to_delete = index
							break

				try:
					# Update Y position for fields present deleted index
					# for index in range(field_index_to_delete + 1, len(component.fields)):
					# 	component.fields[index]['posy'] = str(float(component.fields[index]['posy']) + POSY_OFFSET)
					# Remove field
					# print(component.fields[field_index_to_delete])
					component.fields.pop(field_index_to_delete)
					# print('\t> Successfully removed')
				except:
					print('\t[ERROR] Field could not be removed')

		# Retrieve last field position
		index = len(component.fields)
		# Add missing fields from lib
		if 'field_add' in field_data:
			for key, value in field_data['field_add'].items():
				try:
					print(f'(F.add) {self.fieldname_lookup_table[key]} : {value}')
				except:
					print(f'(F.add) \"{key}\" : {value}')
				
				try:
					# Deep copy previous field (dict)
					new_field = copy.deepcopy(component.fields[index - 1])
					# All properties from the previous field will be kept except for name, value, Y position and visibility
					new_field['name'] = value
					# Check if fieldname already exist in library
					if key in self.fieldname_lookup_table.keys():
						# Fetch field name
						new_field['fieldname'] = self.fieldname_lookup_table[key]
					else:
						new_field['fieldname'] = self.RestoreFieldname(key)

						# Add double-quotes
						new_field['fieldname'] = '"' + new_field['fieldname'] + '"'

						# print(f'New Field Name = {new_field["fieldname"]}')

					# Find user fields Y positions
					posy = []
					for posy_idx in range(0, len(component.fields)):
						posy.append(int(component.fields[posy_idx]['posy']))

					# Set the new field below the lowest one
					new_field['posy'] = str(min(posy) + POSY_OFFSET)
					# Set the visibility to hidden
					new_field['visibility'] = 'I'
					# Add to component's fields
					component.fields.append(new_field)
					# print('\t> Successfully added')
					# Increment index
					index += 1
				except:
					print('\t[ERROR] Field could not be added')

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

	def ExportLibraryToCSV(self, csv_output = None):
		if not self.lib_parse:
			print('[ERROR] CSV Export: Library parse is empty')
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
					csv_file = CSV_FOLDER + self.name.split('.')[-2] + '.csv'
				except:
					csv_file = CSV_FOLDER + self.name + '.csv'

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
			csv_writer = csv_tool.writer(csvfile)
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
	### ARGPARSE
	parser = argparse.ArgumentParser(description = """KiCad Symbol Library Manager (CSV version)""")
	parser.add_argument("LIB_FOLDER",
						help = "KiCad Symbol Library Folder (containing '.lib' files)")
	parser.add_argument("-lib", required = False, default = "",
						help = "KiCad Symbol Library File ('.lib')")
	parser.add_argument("CSV_FOLDER",
						help = "KiCad Symbol CSV Folder (containing '.csv' files)")
	parser.add_argument("-csv", required = False, default = "",
						help = "KiCad Symbol CSV File ('.csv')")
	parser.add_argument("-export_csv", action='store_true',
						help = "Export LIB file(s) as CSV file(s)")
	parser.add_argument("-update_lib", action='store_true',
						help = "Update LIB file(s) from CSV file(s)")
	# parser.add_argument("-add_global_field", required = False, default = "",
	# 					help = "Add global field to all parts in library")

	args = parser.parse_args()
	###

	# Check and store library folder
	if args.LIB_FOLDER[-1] == '/':
		LIB_FOLDER = args.LIB_FOLDER
	else:
		LIB_FOLDER = args.LIB_FOLDER + '/'

	# Check and store CSV folder
	if args.CSV_FOLDER[-1] == '/':
		CSV_FOLDER = args.CSV_FOLDER
	else:
		CSV_FOLDER = args.CSV_FOLDER + '/'
	
	print(f'lib_folder =\t{LIB_FOLDER}\ncsv_folder =\t{CSV_FOLDER}', silent=not(VERBOSE))	

	lib_files = []
	csv_files = []
	lib_to_csv = {}

	if args.lib and args.csv:
		if args.lib:
			# Append to library files
			lib_files.append(args.lib)

		if args.csv:
			# Append to CSV files
			csv_files.append(args.csv)
	else:
		# Find all library files in folder
		for dirpath, folders, files in os.walk(LIB_FOLDER):
			for file in files:
				if '.lib' in file and file not in lib_files:
					lib_files.append(file)

		# Find all CSV files in folder
		for dirpath, folders, files in os.walk(CSV_FOLDER):
			for file in files:
				if '.csv' in file and file not in csv_files:
					csv_files.append(file)

	# Match lib and csv files by name
	for lib in sorted(lib_files):
		try:
			lib_name = lib.split('.')[0]
		except:
			lib_name = lib
		for csv in sorted(csv_files):
			try:
				csv_name = csv.split('.')[0]
			except:
				csv_name = csv

			if lib_name == csv_name:
				lib_to_csv[lib] = csv
				break

		# Did not find match
		if lib not in lib_to_csv:
			lib_to_csv[lib] = ''

	print(f'lib_files =\t{sorted(lib_files)}\ncsv_files =\t{sorted(csv_files)}\nlib_to_csv =\n', end='', silent=not(VERBOSE))
	print(lib_to_csv, silent=not(VERBOSE))

	for lib, csv in lib_to_csv.items():
		try:
			lib_name = lib.split(".")[0]
		except:
			lib_name = lib

		# Append CSV file name if empty
		if not csv:
			csv = lib_name + '.csv'

		print(f'\n[ {lib_name} ]')

		# Define library instance
		klib = KicadLibrary(name=lib_name, lib_file=LIB_FOLDER + lib, csv_file=CSV_FOLDER + csv, silent=not(VERBOSE))

		# Export library to CSV
		if args.export_csv and not args.update_lib:
			if klib.lib_parse and not klib.csv_parse:
				klib.ExportLibraryToCSV()
			elif klib.lib_parse and klib.csv_parse:
				print(f'[ERROR] Aborting Export: CSV file aleady exist and contains data', silent=not(VERBOSE))

		# Update library from CSV
		if not args.export_csv and args.update_lib:
			if klib.lib_parse and klib.csv_parse:
				klib.UpdateLibraryFromCSV(silent = not(VERBOSE))
				# print(klib.fieldname_lookup_table, silent=not(DEBUG_DEEP))