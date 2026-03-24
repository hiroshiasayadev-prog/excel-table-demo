"""
Page 4: Upload & Parse / excel-table read

Demonstrates excel-table's read API.

The user uploads the Excel file filled in on Page 3.
excel-table parses the structured tables from the sheet and returns
typed Pydantic models, which are then converted to xarray DataArrays
and plotted as current density [mA/mm].

excel-table read API used here
-------------------------------
SheetReadSchema
    Declares the column structure of one logical row of tables:
    the title, type, and layout of each table in the row.
    The reader scans the sheet for repeated occurrences of this
    structure, returning one parsed row per device.

TableKeyValueSchema
    Schema for a flat key-value table (title + header row + value row).
    Values are returned as ``str`` regardless of Excel cell type;
    type conversion is the caller's responsibility.

FormattedTable2DSchema
    Schema for a 2-D table with row and column axes.
    ``table_type=Table2DFloat`` instructs the reader to cast all
    values to ``float`` during model validation.

read_sheet_bytes(data, sheet_name, schema)
    Accepts raw ``.xlsx`` bytes (e.g. from ``st.file_uploader``),
    locates each table by its title, and returns a
    ``list[list[...]]`` — one inner list per detected device row.
"""
import numpy as np
import xarray as xr
import streamlit as st
import plotly.io as pio

from excel_table.reader import SheetReadSchema, read_sheet_bytes
from excel_table.models import Table2DFloat, TableKeyValue
from excel_table.models.table_format import FormattedTable2DSchema, TableKeyValueSchema

from transistor import (
    Display,
    iv_to_xarray, transfer_to_xarray, to_current_density,
)

SHEET_NAME = "Transistor Input"


def read_input(data: bytes) -> list[list]:
    """Parse structured tables from the uploaded Excel file.

    Defines a :class:`~excel_table.reader.SheetReadSchema` that matches
    the layout written by Page 2, then calls
    :func:`~excel_table.reader.read_sheet_bytes` to extract the tables.

    The schema declares three columns per device row:

    - **Model Params** (:class:`~excel_table.models.TableKeyValueSchema`):
      GateWidth and GateLength in um. Values are returned as ``str``;
      the caller converts to ``float`` as needed.
    - **IV Result** (:class:`~excel_table.models.FormattedTable2DSchema`
      with ``table_type=Table2DFloat``):
      Ids [A] grid with Vds as the row axis and Vgs as the column axis.
      Values are automatically cast to ``float`` by model validation.
    - **Transfer Result** (:class:`~excel_table.models.FormattedTable2DSchema`
      with ``table_type=Table2DFloat``):
      Ids [A] grid with Vgs as the row axis and forward/backward sweep
      as the column axis.

    The reader scans the sheet for repeated occurrences of the first
    column title (``"Model Params"``), so one inner list is returned
    per device filled in by the user.

    Args:
        data: Raw ``.xlsx`` file contents from ``st.file_uploader``.

    Returns:
        ``list[list]`` — one inner list per device row, each containing
        ``[TableKeyValue, Table2DFloat, Table2DFloat]``.
    """
    schema = SheetReadSchema(
        columns=[
            TableKeyValueSchema(title="Model Params"),
            FormattedTable2DSchema(title="IV Result", table_type=Table2DFloat),
            FormattedTable2DSchema(title="Transfer Result", table_type=Table2DFloat),
        ]
    )
    return read_sheet_bytes(data, SHEET_NAME, schema)


def device_label(row: list) -> str:
    params: TableKeyValue = row[0]
    return f"GateWidth: {params.value[0]} um, GateLength: {params.value[1]} um"


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

st.set_page_config(layout="wide")
st.title("Page 4: Upload & Parse / excel-table read")

uploaded = st.file_uploader("Upload filled input template (.xlsx)")

if uploaded:
    result = read_input(uploaded.getvalue())
    st.session_state["parse_result"] = result

if "parse_result" in st.session_state:
    result = st.session_state["parse_result"]

    with st.container(border=True):
        selected = st.selectbox(
            "Select device",
            result,
            format_func=device_label,
        )

        iv_data = iv_to_xarray(selected[1])
        transfer_data = transfer_to_xarray(selected[2])
        W_um = float(selected[0].value[0])

        jd_iv = to_current_density(iv_data, W_um)
        jd_tr = to_current_density(transfer_data, W_um)

        l, r = st.columns(2)
        with l:
            st.plotly_chart(pio.from_json(Display.generate_IV_density_map(jd_iv)))
        with r:
            st.plotly_chart(pio.from_json(Display.generate_Transfer_density_map(jd_tr)))