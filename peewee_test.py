import sys
from peewee import *

# DATABASE FILE
db_path = './library.sqlite3'

# LOAD DATABASE
mydb = SqliteDatabase(db_path)

class LibraryDict(Model):
	key = CharField()
	value = CharField()

	class Meta:
		database = mydb

class LibraryDatabase:

	def __init__(self):
		print('Library Database')
		mydb.connect()

	def CreateTable(self, table):
		if not mydb.table_exists(table):
			mydb.create_tables([table])

	def WriteToDatabase(self, key, value):
		item = LibraryDict.create(key=key, value=value)

	def CloseDatabase(self):
		mydb.close()

if __name__ == '__main__':
	mylib = LibraryDatabase()

	if len(sys.argv) > 2:
		# Create table if does not exists
		mylib.CreateTable(LibraryDict)
		# Add value to table
		mylib.WriteToDatabase(sys.argv[1], sys.argv[2])

	mylib.CloseDatabase()