## kicad-database-utils-csv
After putting on my librarian hat and needing to update multiple components at once, this tool came to mind.
Instead of clicking multiple times on each component property and manually update them, I thought I could make my life a bit easier and convert symbol library (.lib) files to the CSV format, which can be easily manipulated.
After the CSV file is updated, this tool pushes all the changes to the library file, without the need to open KiCad.

Here are some examples this tool can be used for:
* Updating all the component footprint names, in the case you've decided to reformat the structure of your footprint library
* Update all the datasheet links of a vendor who's decided to change their web location
* Update the references and/or keywords for a specific type of component
* Add or remove user fields for all or a specific type of component
* Remove obsolete or add new components quickly
* Any other global symbol library updates you're thinking of.

This tool does not have any dependency other than the [schlib library parsing tool](https://github.com/KiCad/kicad-library-utils/tree/master/schlib) provided by the KiCad team (already included). Be sure to run it with Python 3+.
And please let me know if you run into any issue.

#### Manual
```
$ kicad-tools/kicad_library_manager_csv.py --help
usage: kicad_library_manager_csv.py [-h] [-v] [-d] [-e] [-u] [-f] [-t TEMPLATE] [-a GLOBAL_FIELD] [-g DEFAULT_VALUE] LIB_PATH CSV_PATH

KiCad Symbol Library Manager (CSV)

positional arguments:
  LIB_PATH              KiCad symbol library folder or file (.lib files)
  CSV_PATH              KiCad symbol CSV folder or file (.csv files)

optional arguments:
  -h, --help            Show this help message and exit
  -v, --version         Show program's version number and exit
  -d, --debug           Display debug verbose
  -e, --export_csv      Export LIB file(s) as CSV file(s)
  -u, --update_lib      Update LIB file(s) from CSV file(s)
  -f, --force_write     Overwrite for LIB and CSV files
  -t TEMPLATE, --template TEMPLATE
                        Path to symbol template file (.lib) used to add component
  -a GLOBAL_FIELD, --add_global_field GLOBAL_FIELD
                        Add global field to all components in library
  -g DEFAULT_VALUE, --global_field_default DEFAULT_VALUE
                        Default value for global field
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
[1]	Processing compare on 12 components... Differences found
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
##### Adding components to library
Both ".lib" and ".dcm" files located in the `templates` folder are used to add a component in the library. You'll need to refer to the template file ".lib" to be able to add components.

Note that the template file do not have a pre-defined symbol drawing, you'll have to draw it yourself.
If you intend to re-use a symbol drawing, it is maybe easier to copy-paste the component in KiCad before running an update on the new component.

Example 1: Templates file is missing, components aren't added to library
```
$ kicad-tools/kicad_library_manager_csv.py library/Transistors.lib library_csv/Transistors.csv --update_lib

[[ TRANSISTORS ]]
(LIB)	Parsing library/Transistors.lib file (12 components)
(CSV)	Parsing library_csv/Transistors.csv file (14 components)

Library Update
---
[1]	Processing compare on 14 components... Differences found
[2]	Updating library file
---
[ERROR]	Component DMG1024-7 could not be added: missing template file
[ERROR]	Component DMP3099-7 could not be added: missing template file

---
Update complete
```

Example 2: Template file is specified, components are added to library
```
$ kicad-tools/kicad_library_manager_csv.py library/Transistors.lib library_csv/Transistors.csv --update_lib --template templates/TEMPLATE_SYMBOL.lib 

[[ TRANSISTORS ]]
(LIB)	Parsing library/Transistors.lib file (12 components)
(CSV)	Parsing library_csv/Transistors.csv file (14 components)

Library Update
---
[1]	Processing compare on 14 components... Differences found
[2]	Updating library file
---
[INFO]	Adding DMG1024-7 to library using templates/TEMPLATE_SYMBOL.lib file
[INFO]	Adding DMP3099-7 to library using templates/TEMPLATE_SYMBOL.lib file

[ U0 :	DMG1024-7 ]
(F.add) "Supplier" : "Digikey"
(F.add) "Supplier Part Number" : "DMG1024UV-7DICT-ND"
(F.add) "Manufacturer" : "Diodes Incorporated"
(F.add) "Manufacturer Part Number" : "DMG1024UV-7"
(F.add) "Description" : "MOSFET 2N-CH 20V 1.38A SOT563"

[ U1 :	DMP3099-7 ]
(F.add) "Supplier" : "Digikey"
(F.add) "Supplier Part Number" : "DMP3099L-7DICT-ND"
(F.add) "Manufacturer" : "Diodes Incorporated"
(F.add) "Manufacturer Part Number" : "DMP3099L-7"
(F.add) "Description" : "MOSFET P-CH 30V SOT23"

---
Update complete
```

#### Adding global field to multiple libraries
Note: The CSV file won't be updated, you'll have to re-run the export.
```
$ kicad-tools/kicad_library_manager_csv.py library/ library_csv/ --update_lib --add_global_field "Variant" --global_field_default "dnp"

[[ CAPACITORS ]]
(LIB)	Parsing library/Capacitors.lib file (5 components)
(CSV)	Parsing library_csv/Capacitors.csv file (5 components)

Library Update
---
[1]	Processing compare on 5 components... Differences found
[2]	Updating library file
---

[ U0 :	C0402C100J3GACTU ]
(F.add) "Variant" : "dnp"

...

[ U4 :	GRM155R70J105KA12J ]
(F.add) "Variant" : "dnp"

[[ TRANSISTORS ]]
(LIB)	Parsing library/Transistors.lib file (12 components)
(CSV)	Parsing library_csv/Transistors.csv file (12 components)

Library Update
---
[1]	Processing compare on 12 components... Differences found
[2]	Updating library file
---

[ U0 :	BSS138-7-F ]
(F.add) "Variant" : "dnp"

...

[ U11 :	SSR ]
(F.add) "Variant" : "dnp"

---
Update complete
```
