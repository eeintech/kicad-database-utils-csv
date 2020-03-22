import sys
from peewee import *
sys.path.append('kicad-tools')
from kicad_schlib_wrapper import KicadLibrary

# FIELDS
FIELD_IDX_MIN = 3
FIELD_IDX_MAX = 21

# DATABASE FILE
db_path = './database-tools/library.sqlite3'

# LOAD DATABASE
mydb = SqliteDatabase(db_path)

class Component(Model):
	name = CharField()
	description_doc = CharField()
	datasheet_doc = CharField()
	keywords_doc = CharField()
	reference = CharField()
	value = CharField()
	footprint = CharField()

	class Meta:
		database = mydb
		table_name = 'component'

class LibraryDatabase:

	def __init__(self):
		mydb.connect()
		self.InitComponentTable()

	def InitComponentTable(self):
		return
		# TODO: User fields
		for index in range(FIELD_IDX_MIN, FIELD_IDX_MAX):
			Component._meta.add_field('f' + str(index) + '_name', CharField(null = True))
			Component._meta.add_field('f' + str(index) + '_value', CharField(null = True))

	def CreateTable(self, table, force_update = False):
		if force_update:
			mydb.drop_tables([table])
		if not mydb.table_exists(table._meta.table_name):
			#print(Component._meta.fields)
			mydb.create_tables([table])			

	def AddComponentToDatabase(self, component):
		data_source = {	'name': component['name'],
						'description_doc': component['description_doc'],
						'datasheet_doc': component['datasheet_doc'],
						'keywords_doc': component['keywords_doc'],
						'reference': component['reference'],
						'value': component['value'],
						'footprint': component['footprint']
						}

		# TODO: User fields
		if False:
			for index in range(FIELD_IDX_MIN, FIELD_IDX_MAX):
				name_key = 'f' + str(index) + '_name'
				value_key = 'f' + str(index) + '_value'

				if name_key not in component:
					break

				data_source[name_key] = component[name_key]
				data_source[value_key] = component[value_key]

		#print(data_source)
		item = Component.create(**data_source)
			

	def CloseDatabase(self):
		mydb.close()

if __name__ == '__main__':
	mylib = LibraryDatabase()

	if len(sys.argv) > 1:
		# Create table if does not exists
		mylib.CreateTable(Component, force_update = True)
		# Load file
		kicad_lib = KicadLibrary(sys.argv[1])
		print(f'Adding components to database', end='')
		count = 0
		for component in kicad_lib.parse:
			if count >= 4:
				print('.', end='')
				sys.stdout.flush()
				count = 0
			#print(f'Adding {component["name"]} to database')
			mylib.AddComponentToDatabase(component)
			count += 1
		print('\nAll components added to database')

	mylib.CloseDatabase()