## kicad-database-utils (Python 3+)
#### Manual
```
usage: kicad_library_manager_csv.py [-h] [-v] [-d] [-e] [-u] [-f] [-a GLOBAL_FIELD] [-g DEFAULT_VALUE] [-t TEMPLATE] LIB_PATH CSV_PATH

KiCad Symbol Library Manager (CSV)

positional arguments:
  LIB_PATH              KiCad symbol library folder or file (".lib" files)
  CSV_PATH              KiCad symbol CSV folder or file (".csv" files)

optional arguments:
  -h, --help            Show this help message and exit
  -v, --version         Show program's version number and exit
  -d, --debug           Display debug verbose
  -e, --export_csv      Export LIB file(s) as CSV file(s)
  -u, --update_lib      Update LIB file(s) from CSV file(s)
  -f, --force_write     Overwrite for LIB and CSV files
  -a GLOBAL_FIELD, --add_global_field GLOBAL_FIELD
                        Add global field to all components in library
  -g DEFAULT_VALUE, --global_field_default DEFAULT_VALUE
                        Default value for global field
  -t TEMPLATE, --template TEMPLATE
                        Path to symbol template file (.lib) used to add component
```
  
#### Exporting KiCad symbol library to CSV file
Note: `library` and `library_csv` are arbitrary folders, replace with your own.
##### Export single LIB to CSV
```
$ kicad-tools/kicad_library_manager_csv.py library/Transistors.lib library_csv/Transistors.csv --export_csv
```
Output:
```
[[ TRANSISTORS ]]
(LIB)	Parsing library/Transistors.lib file (12 components)
(CSV)	Exporting library to library_csv/Transistors.csv
```
##### Export multiple LIB to CSV
```
$ kicad-tools/kicad_library_manager_csv.py library/ library_csv/ --export_csv
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
##### Force overwrite of CSV file
In case you get the following error during CSV export:
```
[ERROR]	Aborting Export: CSV file aleady exist and contains data
```
You can force overwrite the CSV file with the `--force_write` option (make sure to save any changes to the CSV file beforehand):
```
$ kicad-tools/kicad_library_manager_csv.py library/Transistors.lib library_csv/Transistors.csv --export_csv --force_write

[[ TRANSISTORS ]]
(LIB)	Parsing library/Transistors.lib file (12 components)
[WARN]	File library_csv/Transistors.csv already exists
(CSV)	Parsing library_csv/Transistors.csv file (12 components)
(CSV)	Exporting library to library_csv/Transistors.csv
```
  
#### Updating KiCad symbol library from CSV file
##### Updating single LIB from CSV
```
$ kicad-tools/kicad_library_manager_csv.py library/Transistors.lib library_csv/Transistors.csv --update_lib
```
Output:
```
[[ TRANSISTORS ]]
(LIB)	Parsing library/Transistors.lib file (12 components)
(CSV)	Parsing library_csv/Transistors.csv file (12 components)

Library Update
---
[1]	Processing compare on 12 parts... Differences found
[2]	Updating library file
---

[ U0 :	N-Channel_MOSFET ]
(F.upd) "Footprint" : "F" -> ""

[ U1 :	NPN ]
(F.upd) "Footprint" : "F" -> ""

[ U2 :	P-Channel_MOSFET ]
(F.upd) "Footprint" : "F" -> ""

[ U3 :	PNP ]
(F.upd) "Footprint" : "F" -> ""

[ U4 :	SSR ]
(F.upd) "Footprint" : "F" -> ""

---
Update complete
```
##### Updating multiple LIB from CSV
```
$ kicad-tools/kicad_library_manager_csv.py library/ library_csv/ --update_lib
```
