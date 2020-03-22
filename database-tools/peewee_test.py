import sys
from peewee import *
sys.path.append('kicad-tools')
from kicad_schlib_wrapper import KicadLibrary

# FIELDS
FIELD_IDX_MIN = 3
FIELD_IDX_MAX = 21

# DATABASE FILE
db_path = './library.sqlite3'

# LOAD DATABASE
mydb = SqliteDatabase(db_path)

class Component(Model):
	name = CharField()#primary_key = True)
	reference = CharField()
	value = CharField()
	footprint = CharField()

	class Meta:
		database = mydb

class LibraryDatabase:

	def __init__(self):
		#print('Library Database')
		mydb.connect()
		self.InitComponentTable()

	def InitComponentTable(self):
		for index in range(FIELD_IDX_MIN, FIELD_IDX_MAX):
			Component._meta.add_field('f' + str(index) + '_name', CharField(null = True))
			Component._meta.add_field('f' + str(index) + '_value', CharField(null = True))

	def CreateTable(self, table):
		#print(table._meta.table_name)
		if not mydb.table_exists(table._meta.table_name):
			print(Component._meta.fields)
			mydb.create_tables([table])

	def AddComponentToDatabase(self, component):
		data_source = {	'name': component['name'],
						'reference': component['reference'],
						'value': component['value'],
						'footprint': component['footprint']
						}

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
		mylib.CreateTable(Component)
		# Load file
		kicad_lib = KicadLibrary(sys.argv[1])
		for component in kicad_lib.parse:
			#print(component)
			mylib.AddComponentToDatabase(component)

		#mylib.WriteToDatabase(sys.argv[1], sys.argv[2])

	mylib.CloseDatabase()