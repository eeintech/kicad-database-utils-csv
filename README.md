### kicad-database-utils (Python 3+)
##### Manual
```
usage: kicad_library_manager_csv.py [-h] [-lib LIB] [-csv CSV] [-export_csv] [-update_lib] [-force_write] [-add_global_field ADD_GLOBAL_FIELD]
                                    [-global_field_default GLOBAL_FIELD_DEFAULT]
                                    LIB_FOLDER CSV_FOLDER

KiCad Symbol Library Manager (CSV version)

positional arguments:
  LIB_FOLDER            KiCad Symbol Library Folder (containing '.lib' files)
  CSV_FOLDER            KiCad Symbol CSV Folder (containing '.csv' files)

optional arguments:
  -h, --help            show this help message and exit
  -lib LIB              KiCad Symbol Library File ('.lib')
  -csv CSV              KiCad Symbol CSV File ('.csv')
  -export_csv           Export LIB file(s) as CSV file(s)
  -update_lib           Update LIB file(s) from CSV file(s)
  -force_write          Overwrite for LIB and CSV files
  -add_global_field ADD_GLOBAL_FIELD
                        Add global field to all components in library
  -global_field_default GLOBAL_FIELD_DEFAULT
                        Default value for global field
```
#### Exporting KiCad symbol library to CSV file
##### Export single LIB to CSV
```
$ kicad-tools/kicad_library_manager_csv.py library/ -lib Transistors.lib library_csv/ -csv Transistors.csv -export_csv
```
Output:
```
[[ TRANSISTORS ]]
(LIB)	Parsing library/Transistors.lib file (12 components)
(CSV)	Exporting library to library_csv/Transistors.csv
```
##### Export multiple LIB to CSV
```
$ kicad-tools/kicad_library_manager_csv.py library/ library_csv/ -export_csv
```
Output:
```
[[ CAPACITORS ]]
(LIB)	Parsing library/Capacitors.lib file (52 components)
(CSV)	Exporting library to library_csv/Capacitors.csv

[[ TRANSISTORS ]]
(LIB)	Parsing library/Transistors.lib file (12 components)
[WARN]	File library_csv/Transistors.csv already exists
(CSV)	Parsing library_csv/Transistors.csv file (12 components)
[ERROR]	Aborting Export: CSV file aleady exist and contains data
```
#### Updating KiCad symbol library from CSV file
##### Updating single LIB from CSV
```
$ kicad-tools/kicad_library_manager_csv.py library/ -lib Transistors.lib library_csv/ -csv Transistors.csv -update_lib
```
##### Updating multiple LIB from CSV
```
$ kicad-tools/kicad_library_manager_csv.py library/ library_csv/ -update_lib
```
