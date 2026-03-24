# excel-table demo

A demo app showing real-world usage of [excel-table](https://github.com/hiroshiasayadev-prog/excel-table) read/write.

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
Paste the axis ranges from Page 1's CSV. excel-table generates a blank input-format Excel file for download.

The following excel-table classes are used:

- `SheetWriteSchema` — defines the grid layout of tables in the sheet
- `TableKeyValue` — key-value table for device parameters (W, L)
- `FormattedTable2D` — 2-D table for measurement data grids
- `write_sheet_bytes` — renders the schema to in-memory `.xlsx` bytes

### Page 3: Manual Data Entry
Paste the measured values from the CSV (Page 1) into the Excel template (Page 2), then proceed to Page 4.

### Page 4: Upload & Parse / excel-table read
**Demonstrates excel-table read.**
Upload the filled Excel from Page 3. excel-table parses the structured tables and returns typed Pydantic models.
Results are displayed as current density [mA/mm].

The following excel-table classes are used:

- `SheetReadSchema` — declares the column structure of one logical row of tables
- `TableKeyValueSchema` — schema for a flat key-value table
- `FormattedTable2DSchema` — schema for a 2-D table; `table_type=Table2DFloat` auto-casts values to float
- `read_sheet_bytes` — parses raw `.xlsx` bytes and returns `list[list[...]]`, one inner list per device

### Page 5: Excel Export / excel-table write
**Demonstrates excel-table write with formatting and charts.**
Computes current density and transconductance from the parsed data, then writes a formatted Excel report.

The following excel-table classes are used:

- `FormattedTable2D` with `value_conditional_formats` — color gradient on the Jd IV table
- `ChartConfig` / `LineSeriesConfig` — Excel charts with per-series color gradients and dual Y axes
- `write_sheet_bytes` — renders the full report to in-memory `.xlsx` bytes