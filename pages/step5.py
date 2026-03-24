"""
Page 5: Excel Export / excel-table write

Demonstrates excel-table's write API with formatting and charts.

Takes the parsed device data from Page 4 (via session state),
computes current density and transconductance, then writes a
formatted Excel report using excel-table.

excel-table write API used here
--------------------------------
SheetWriteSchema
    Defines the grid layout of tables and charts in the sheet.
    All rows must share the same column structure (same item types
    per column position), which naturally maps to one row per device.

TableKeyValue
    Flat key-value table for device parameters (W, L).

FormattedTable2D
    2-D table with rendering metadata.
    ``value_conditional_formats`` is used here to apply a color
    gradient to the Jd IV table, illustrating how conditional
    formatting rules are attached to a table at write time.

ChartConfig / LineSeriesConfig
    Declares an Excel chart that references Table2D blocks by title.
    ``color_axis`` splits the IV series per Vgs value and applies
    a color gradient from the ColorScale.
    ``y_axis`` on LineSeriesConfig assigns each series to the primary
    (``"y1"``) or secondary (``"y2"``) Y axis, enabling dual-axis charts
    such as Jd and gm overlaid on a single Transfer chart.

write_sheet_bytes
    Renders the schema to in-memory ``.xlsx`` bytes for download.
"""
import numpy as np
import xarray as xr
import streamlit as st

from excel_table.models import (
    Table2D,
    FormattedTable2D,
    TableKeyValue,
    ColorScale,
    LineSeriesConfig,
    ChartConfig,
)
from excel_table.writer import SheetWriteSchema, write_sheet_bytes

from transistor import iv_to_xarray, transfer_to_xarray, to_current_density, gm_from_transfer

SHEET_NAME = "Transistor Output"


def build_report(parse_result: list[list]) -> bytes:
    """Build a formatted Excel report from all parsed devices.

    For each device row in ``parse_result``, computes current density
    and transconductance, then assembles the following tables per row:

    - **Model Params** (:class:`~excel_table.models.TableKeyValue`):
      GateWidth and GateLength in um.
    - **Jd IV** (:class:`~excel_table.models.FormattedTable2D`):
      Current density [mA/mm] grid (Vds × Vgs).
      A 3-color gradient conditional format is applied to the values.
    - **Jd Transfer** (:class:`~excel_table.models.FormattedTable2D`):
      Current density [mA/mm] grid (Vgs × sweep direction).
      No conditional format — contrast with Jd IV.
    - **gm** (:class:`~excel_table.models.FormattedTable2D`):
      Transconductance [mS/mm] grid (Vgs × sweep direction),
      derived as d(Jd)/d(Vgs).
    - **IV Chart** (:class:`~excel_table.models.ChartConfig`):
      Excel line chart of Jd IV, with Vgs-based color gradient.
    - **Transfer Chart** (:class:`~excel_table.models.ChartConfig`):
      Excel line chart of Jd Transfer (forward and backward).

    Args:
        parse_result: Output of ``read_input()`` from Page 4.
            Each inner list is ``[TableKeyValue, Table2DFloat, Table2DFloat]``.

    Returns:
        Raw ``.xlsx`` file contents as :class:`bytes`.
    """
    rows = []

    for device_row in parse_result:
        params: TableKeyValue = device_row[0]
        W_um = float(params.value[0])

        iv_data = iv_to_xarray(device_row[1])
        transfer_data = transfer_to_xarray(device_row[2])

        jd_iv = to_current_density(iv_data, W_um)
        jd_tr = to_current_density(transfer_data, W_um)
        gm = gm_from_transfer(jd_tr)

        vds = [v for v in jd_iv.coords["vds"].values]
        vgs = [v for v in jd_iv.coords["vgs"].values]
        tr_vgs = [v for v in jd_tr.coords["vgs"].values]

        # --- Model Params ---
        model_params = TableKeyValue(
            title="Model Params",
            column=["GateWidth [um]", "GateLength [um]"],
            value=params.value,
        )

        # --- Jd IV (with color gradient) ---
        jd_iv_table = FormattedTable2D(
            table=Table2D(
                title="Jd IV",
                column_label="Vgs [V]",
                row_label="Vds [V]",
                column=vgs,
                row=vds,
                values=jd_iv.values.T.tolist(),
            ),
            value_conditional_formats=[
                {
                    "type": "3_color_scale",
                    "min_color": "#FFFFFF",
                    "mid_color": "#FFF176",
                    "max_color": "#FF5722",
                },
            ],
        )

        # --- Jd Transfer (no conditional format — contrast with IV) ---
        jd_tr_table = FormattedTable2D(
            table=Table2D(
                title="Jd Transfer",
                column_label="Sweep Direction",
                row_label="Vgs [V]",
                column=["forward", "backward"],
                row=tr_vgs,
                values=jd_tr.values.T.tolist(),
            ),
        )

        # --- gm ---
        gm_table = FormattedTable2D(
            table=Table2D(
                title="gm",
                column_label="Sweep Direction",
                row_label="Vgs [V]",
                column=["forward", "backward"],
                row=tr_vgs,
                values=gm.values.T.tolist(),
            ),
        )

        # --- IV Chart ---
        iv_chart = ChartConfig(
            chart_type="line",
            x_label="Vds [V]",
            y_label="Jd [mA/mm]",
            series=[
                LineSeriesConfig(
                    label="Jd IV",
                    source_block="Jd IV",
                    style="line",
                    color_axis="column",
                    series_colorscale=ColorScale(
                        min_color="#2196F3",
                        mid_color="#4CAF50",
                        max_color="#F44336",
                    ),
                    x_axis="row",
                )
            ],
        )

        # --- Transfer Chart ---
        transfer_chart = ChartConfig(
            chart_type="line",
            x_label="Vgs [V]",
            y_label="Jd [mA/mm]",
            series=[
                LineSeriesConfig(
                    label="Jd forward",
                    source_block="Jd Transfer",
                    style="line",
                    series_color="#1565C0",
                    col_filter="column == 'forward'",
                    x_axis="row",
                ),
                LineSeriesConfig(
                    label="Jd backward",
                    source_block="Jd Transfer",
                    style="line",
                    series_color="#1565C0",
                    col_filter="column == 'backward'",
                    x_axis="row",
                    y_axis="y1",
                ),
                LineSeriesConfig(
                    label="gm forward",
                    source_block="gm",
                    style="line",
                    series_color="#E65100",
                    col_filter="column == 'forward'",
                    x_axis="row",
                    y_axis="y2",
                ),
                LineSeriesConfig(
                    label="gm backward",
                    source_block="gm",
                    style="line",
                    series_color="#E65100",
                    col_filter="column == 'backward'",
                    x_axis="row",
                    y_axis="y2",
                ),
            ],
        )

        rows.append([
            model_params,
            jd_iv_table,
            jd_tr_table,
            gm_table,
            iv_chart,
            transfer_chart,
        ])

    schema = SheetWriteSchema(rows=rows)
    return write_sheet_bytes(sheet_name=SHEET_NAME, schema=schema)


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

st.set_page_config(layout="wide")
st.title("Page 5: Excel Export / excel-table write")

if "parse_result" not in st.session_state:
    st.info("Please upload and parse a file on Page 4 first.")
else:
    parse_result = st.session_state["parse_result"]

    if st.button("Generate Excel report"):
        report = build_report(parse_result)
        st.session_state["report"] = report

    if "report" in st.session_state:
        st.download_button(
            label="Download report (.xlsx)",
            data=st.session_state["report"],
            file_name="transistor_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )