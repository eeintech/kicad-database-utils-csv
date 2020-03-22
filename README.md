### kicad-database-utils
#### Exporting CSV from KiCad symbol library
##### Simplest usage
```
$ python kicad-tools/kicad_schlib_wrapper.py /usr/share/kicad/library/Regulator_Switching.lib
```
Output:
```
Parsing Regulator_Switching.lib library
Exporting library to ./library_csv/Regulator_Switching.csv
```
##### Specify output CVS file
```
$ python kicad-tools/kicad_schlib_wrapper.py /usr/share/kicad/library/Regulator_Switching.lib ./kicad-regulators.csv
```
Output:
```
Parsing Regulator_Switching.lib library
Exporting library to ./kicad-regulators.csv
```
