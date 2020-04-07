#!/usr/bin/env python
import sys, os, argparse, copy
import csv as csv_tool

### DEBUG ONLY
DEBUG_MSG = True
LIB_SAVE = True
ADD_ENABLE = False
DELETE_ENABLE = False

# LIB AND CSV FILE FOLDERS
LIB_FOLDER = None
CSV_FOLDER = None

# Import KiCad schematic library utils
try:
	from schlib import SchLib
except:
	# When this file is executed directly
	sys.path.append('kicad-library-utils/schlib')
	from schlib import SchLib

def printDict(dictionary):
	import json
	print()
	print(json.dumps(dictionary, indent = 4, sort_keys = True))

# KICAD LIBRARY CLASS
class KicadLibrary(object):

	def __init__(self, name = None, lib_file = None, csv_file = None, silent = True):
		self.version = 'kicad-library-0.1'
		self.lib_file = lib_file
		self.csv_file = csv_file
		self.lib_parse = None
		self.csv_parse = None
		self.fieldname_lookup_table = {}

		# Define library name
		if not name:
			try:
				self.name = self.lib_file.split('/')[-1]
			except:
				self.name = self.lib_file
		else:
			self.name = name

		# Process library file
		if self.lib_file:
			self.library = self.OpenLibrary()
			if self.library:
				if not silent:
					print(f'Library: Parsing {self.lib_file} file')
				self.lib_parse = self.ParseLibrary()
			#printDict(self.lib_parse)

		# Process CSV file
		if self.csv_file:
			csv_check = self.CheckCSV()
			if csv_check:
				if not silent:
					print(f'CSV: Parsing {self.csv_file} file')
				self.csv_parse = self.ParseCSV()
			# printDict(self.csv_parse)

	def OpenLibrary(self):
		library = None
		# Check if valid library file
		if not '.lib' in self.lib_file:
			print(f'[ERROR] {self.lib_file} does not have a valid library file format')
			return library
		else:
			# Load library
			try:
				library = SchLib(self.lib_file)
			except:
				print(f'[ERROR] Cannot read library file {self.lib_file}')

			if len(library.components) == 0:
				print(f'[ERROR] Library file is empty {self.lib_file}')
				return None

			return library

	def CheckCSV(self):
		# Check if valid CSV file
		if not '.csv' in self.csv_file:
			print(f'[ERROR] File {self.csv_file} does not have a valid CSV file format')
			return False

		# Check if file exist
		if not os.path.exists(self.csv_file):
			# print(f'[ERROR] File {self.csv_file} does not exist')
			return False

		# Check if file has data
		with open(self.csv_file, 'r') as csvfile:
			try:
				csv_reader = csv_tool.reader(csvfile)
				next_line = csv_reader.__next__()

				if len(next_line) == 0:
					return False
			except:
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
				mapping[index] = item

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

	def CleanFieldname(self, field_value):
		# Return simple fieldname
		return field_value.lower().replace('"','').replace(' ','_').replace('(','').replace(')','')

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
								self.fieldname_lookup_table[fieldname] = field['fieldname']
						except:
							pass
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
					# print(f'\n\ncommon_keys = {common_keys}\ndiff_keys = {diff_keys}')
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

					# Add missing library fields
					for key in diff_keys:
						# Check csv field contains data and add to compare
						if len(csv_part[key]) > 0:
							# Add to compare
							try:
								compare['part_update'][csv_part['name']]['field_add'].update({key : csv_part[key]})
							except:
								compare['part_update'][csv_part['name']] = {}
								compare['part_update'][csv_part['name']].update({'field_add': {key : csv_part[key]}})
								
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

		if not silent:
			print(f'\nLibrary Update:\n[1] ', end='')

		# Compare both parse information and output diff
		if self.lib_parse and self.csv_parse:
			compare = self.CompareParse()
			# print(compare)

			if not compare:
				if not silent:
					print('No differences found between CSV and LIB files')
			else:
				#printDict(compare)
				# Update library file
				if not silent:
					print('Differences found.\n[2] Updating library file\n---')
				
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
		count = 0
		for component_name in compare['part_update'].keys():
			print(f'\n[U{count}]\tUpdating {component_name}\n |')
			self.UpdateComponentInLibrary(component_name, compare['part_update'][component_name])
			count += 1
			updated = True
		# except:
		# 	pass

		if LIB_SAVE:
			if updated:
				self.library.save()
				if not silent:
					print('\n---\nUpdate complete')

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
						# User field
						fieldname = (field['fieldname'] + '.')[:-1]
						fieldname = self.CleanFieldname(fieldname)

					#print(f'fieldname = {fieldname}\tfield[fieldname] = {field["fieldname"]}')

					# Update field values
					for key, new_value in field_data['field_update'].items():
						if fieldname == key:
							old_value = component.fields[index]["name"]
							print(f' /\\ {fieldname}: {old_value} -> {new_value}')
							component.fields[index]['name'] = new_value		

		# Retrieve last field position
		index = len(component.fields)
		if 'field_add' in field_data:
			# Add missing fields
			for key, value in field_data['field_add'].items():
				print(f' ++ {key}: {value}', end='')
				
				try:
					# Deep copy previous field (dict)
					new_field = copy.deepcopy(component.fields[index - 1])
					# All properties from the previous field will be kept except for name, value and Y position
					new_field['name'] = value
					new_field['fieldname'] = self.fieldname_lookup_table[key]
					new_field['posy'] = str(int(new_field['posy']) - 200)
					# Add to component's fields
					component.fields.append(new_field)
					print('\t> Successfully added')
					# Increment index
					index += 1
				except:
					print('\t> [ERROR] Field could not be added')


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
	
	if DEBUG_MSG:
		print(f'lib_folder =\t{LIB_FOLDER}\ncsv_folder =\t{CSV_FOLDER}')	

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
	for lib in lib_files:
		try:
			lib_name = lib.split('.')[0]
		except:
			lib_name = lib
		for csv in csv_files:
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

	if DEBUG_MSG:
		print(f'lib_files =\t{lib_files}\ncsv_files =\t{csv_files}\nlib_to_csv =\t{lib_to_csv}')	

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
		klib = KicadLibrary(name=lib_name, lib_file=LIB_FOLDER + lib, csv_file=CSV_FOLDER + csv, silent=not(DEBUG_MSG))

		# Export library to CSV
		if args.export_csv and not args.update_lib:
			if klib.lib_parse and not klib.csv_parse:
				klib.ExportLibraryToCSV()
			elif klib.lib_parse and klib.csv_parse:
				if DEBUG_MSG:
					print(f'[ERROR] Aborting Export: CSV file aleady exist and contains data')

		# Update library from CSV
		if not args.export_csv and args.update_lib:
			if klib.lib_parse and klib.csv_parse:
				klib.UpdateLibraryFromCSV(silent = not(DEBUG_MSG))
				# print(klib.fieldname_lookup_table)
