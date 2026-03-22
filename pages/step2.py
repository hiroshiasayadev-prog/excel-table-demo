# pages/2_input_format.py
"""
Page 2: Input Format Generation

Generates a blank Excel input template using excel-table.
The user pastes measurement data from Page 1's CSV into this template,
then uploads it on Page 3 for parsing.

This page demonstrates excel-table's write API:
    SheetWriteSchema  —  defines the grid layout of tables in the sheet
    TableKeyValue     —  key-value table for device parameters (W, L)
    FormattedTable2D  —  2-D table for measurement data grids
    write_sheet_bytes —  renders the schema to an in-memory .xlsx bytes object
"""

import io
import numpy as np
import streamlit as st

from excel_table.models import (
    Table2D,
    FormattedTable2D,
    TableKeyValue,
)
from excel_table.writer import SheetWriteSchema, write_sheet_bytes

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SHEET_NAME = "Transistor Input"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_excel_clipboard(clip: str) -> list[list[str]]:
    """Parse a tab-separated block of text copied from Excel.

    When the user selects a range in Excel and copies it, the clipboard
    contains tab-separated columns and newline-separated rows. This function
    splits that text into a 2-D list of strings.

    Args:
        clip: Raw clipboard text from an Excel range selection.

    Returns:
        A list of rows, each row being a list of cell strings.
        Empty trailing rows are discarded.
    """
    col_sep = "\t"
    row_sep = "\n"
    rows = [row.split(col_sep) for row in clip.split(row_sep) if row.strip()]
    return rows


def build_input_template(
    num_devices: int,
    iv_vds: list[str],
    iv_vgs: list[str],
    transfer_vgs: list[str],
) -> bytes:
    """Build a blank Excel input template as in-memory bytes.

    Generates a single worksheet with ``num_devices`` repeated rows of
    three side-by-side tables:

    - **Model Params** (:class:`~excel_table.models.TableKeyValue`):
      GateWidth and GateLength cells, left blank for the user to fill in.
    - **IV Result** (:class:`~excel_table.models.FormattedTable2D`):
      A blank Ids grid with Vds as the row axis and Vgs as the column axis.
    - **Transfer Result** (:class:`~excel_table.models.FormattedTable2D`):
      A blank Ids grid with Vgs as the row axis and forward/backward sweep
      as the column axis.

    The axes (Vds, Vgs values) are pre-filled from the sweep conditions
    supplied by the user, so the user only needs to paste the measured Ids
    values into the blank cells.

    This layout is written by :class:`~excel_table.writer.SheetWriteSchema`,
    which requires all rows to have the same column structure (same number
    of items, same types per column position). Repeating the identical
    schema ``num_devices`` times satisfies that constraint while allowing
    the user to fill in data for multiple devices in one file.

    Args:
        num_devices: Number of device rows to include in the template.
            Each row contains one set of Model Params, IV Result, and
            Transfer Result tables.
        iv_vds: Vds axis values for the IV sweep, as strings (e.g. ``["0.00", "0.01", ...]``).
        iv_vgs: Vgs axis values for the IV sweep, as strings (e.g. ``["-0.40", "0.00", ...]``).
        transfer_vgs: Vgs axis values for the Transfer sweep, as strings.

    Returns:
        Raw ``.xlsx`` file contents as a :class:`bytes` object.

    Example usage in Streamlit::

        template_bytes = build_input_template(
            num_devices=3,
            iv_vds=["0.00", "0.01", ..., "1.00"],
            iv_vgs=["-0.40", "0.00", ..., "1.00"],
            transfer_vgs=["-1.00", "-0.99", ..., "1.00"],
        )
        st.download_button("Download template", template_bytes, "format.xlsx")
    """
    # --- Model Params (key-value, blank values for user to fill in) ---
    model_params = TableKeyValue(
        title="Model Params",
        column=["GateWidth [um]", "GateLength [um]"],
        value=[None, None],
    )

    # --- IV Result (blank 2-D grid: rows=Vds, cols=Vgs) ---
    iv_table = FormattedTable2D(
        table=Table2D(
            title="IV Result",
            column_label="Vgs [V]",
            row_label="Vds [V]",
            column=iv_vgs,
            row=iv_vds,
            values=np.full((len(iv_vds), len(iv_vgs)), None).tolist(),
        )
    )

    # --- Transfer Result (blank 2-D grid: rows=Vgs, cols=sweep direction) ---
    transfer_table = FormattedTable2D(
        table=Table2D(
            title="Transfer Result",
            column_label="Sweep Direction",
            row_label="Vgs [V]",
            column=["forward", "backward"],
            row=transfer_vgs,
            values=np.full((len(transfer_vgs), 2), None).tolist(),
        )
    )

    # --- Layout: num_devices rows, each with the same 3-column structure ---
    schema = SheetWriteSchema(
        rows=[
            [model_params, iv_table, transfer_table]
            for _ in range(num_devices)
        ]
    )

    return write_sheet_bytes(sheet_name=SHEET_NAME, schema=schema)


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

st.set_page_config(layout="wide")
st.title("Page 2: Input Format Generation / excel-table write")

left, right = st.columns(2)

with left:
    with st.container(border=True):
        st.header("Sweep Conditions")
        st.markdown(
            "Copy each range from the CSV downloaded on Page 1 and paste it below."
        )

        num_devices = st.number_input(
            "Number of devices",
            min_value=1,
            step=1,
            value=1,
        )
        iv_clip = st.text_area(
            "IV data range (paste from CSV — include Vgs header row and Vds column)",
            height=80,
        )
        transfer_clip = st.text_area(
            "Transfer Vgs column (paste from CSV — Vgs column only)",
            height=80,
        )

# ---------------------------------------------------------------------------
# Parse clipboard input
# ---------------------------------------------------------------------------

iv_vgs: list[str] | None = None
iv_vds: list[str] | None = None
transfer_vgs: list[str] | None = None

if iv_clip:
    iv_rows = parse_excel_clipboard(iv_clip)
    iv_vgs = iv_rows[0][1:]                     # first row, skip leading empty cell
    iv_vds = [row[0] for row in iv_rows[1:]]    # first column of remaining rows

if transfer_clip:
    transfer_rows = parse_excel_clipboard(transfer_clip)
    transfer_vgs = [row[0] for row in transfer_rows]

# ---------------------------------------------------------------------------
# Preview + download
# ---------------------------------------------------------------------------

with right:
    with st.container(border=True):
        st.header("Preview & Download")

        if not iv_clip:
            st.info("Paste the IV data range on the left to continue.")
        else:
            iv_vgs_f = [float(v) for v in iv_vgs]
            iv_vds_f = [float(v) for v in iv_vds]
            st.write(
                f"**IV** — Vgs: {min(iv_vgs_f):.2f} ~ {max(iv_vgs_f):.2f} V "
                f"({len(iv_vgs_f)} points), "
                f"Vds: {min(iv_vds_f):.2f} ~ {max(iv_vds_f):.2f} V "
                f"({len(iv_vds_f)} points)"
            )

        if not transfer_clip:
            st.info("Paste the Transfer Vgs column on the left to continue.")
        else:
            transfer_vgs_f = [float(v) for v in transfer_vgs]
            st.write(
                f"**Transfer** — Vgs: {min(transfer_vgs_f):.2f} ~ {max(transfer_vgs_f):.2f} V "
                f"({len(transfer_vgs_f)} points)"
            )

        if iv_clip and transfer_clip:
            template = build_input_template(
                num_devices=int(num_devices),
                iv_vds=iv_vds,
                iv_vgs=iv_vgs,
                transfer_vgs=transfer_vgs,
            )
            st.download_button(
                label="Download input template (.xlsx)",
                data=template,
                file_name="transistor_input_format.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )