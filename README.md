# excel-table demo

A demo app showing real-world usage of [excel-table](https://github.com/your-repo/excel-table) read/write.

## Use Case

Processing CSVs from measurement instruments (or analysis companies) via Excel into excel-table.

A common workflow in the field:
1. An instrument (or analysis company) outputs a CSV
2. The CSV values are manually pasted into a fixed Excel format
3. That Excel is fed into a tool

This demo reproduces that workflow end-to-end.

## Pages

### Page 1: Dummy Instrument / CSV Generation
Runs a GaAs HEMT simulator to measure I-V and Transfer characteristics, then exports the results as CSV.
This mimics raw instrument output and has nothing to do with excel-table.
W and L are entered in um.

### Page 2: Input Format Generation / excel-table write
**Demonstrates excel-table write.**
Enter sweep conditions and excel-table generates a blank input-format Excel file for download.
Paste the CSV values from Page 1 into this Excel, then bring it to Page 3.

### Page 3: Upload & Parse / excel-table read
**Demonstrates excel-table read.**
Upload the Excel filled in from Page 2 and parse it with excel-table.

### Page 4: Visualization
Visualize the parsed data.
Drain current is normalized by gate width and plotted as current density [mA/mm].

### Page 5: Excel Export / excel-table write
**Demonstrates excel-table write.**
Export the visualization results as an Excel file with embedded charts.