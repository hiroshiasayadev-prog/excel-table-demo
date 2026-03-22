# pages/1_csv_generation.py
import io
import csv
import streamlit as st
from transistor import Analyzer, TransistorModel
from transistor import iv_to_list, transfer_to_list

from statics import STATICS

st.set_page_config(
    layout="wide"
)

st.title("Page 1: Dummy Instrument / CSV Generation")

# --- layout ---
l, r = st.columns(2)
with l:
    l_container = st.container(border=True)
with r:
    r_container = st.container(border=True)

# --- パラメータ入力 ---
with l_container:
    st.header("Device Parameters")
    l, r = st.columns([0.5, 0.5])
    with l:
        st.image(STATICS.device_svg)
    with r:
        W = st.number_input("Gate Width [um]", value=100.0) * 1e-6
        L = st.number_input("Gate Length [um]", value=1.0) * 1e-6

    st.header("Sweep Conditions")
    st.image(STATICS.hanpara_svg, width=200)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("I-V")
        vds_from = st.number_input("Vds from [V]", value=0.0)
        vds_until = st.number_input("Vds until [V]", value=1.0)
        vds_step = st.number_input("Vds step [V]", value=0.01)
        vgs_from_iv = st.number_input("Vgs from [V]", value=-0.4, key="vgs_from_iv")
        vgs_until_iv = st.number_input("Vgs until [V]", value=1.0, key="vgs_until_iv")
        vgs_step_iv = st.number_input("Vgs step [V]", value=0.2, key="vgs_step_iv")
    with col2:
        st.subheader("Transfer")
        vgs_from_tr = st.number_input("Vgs from [V]", value=-1.0, key="vgs_from_tr")
        vgs_until_tr = st.number_input("Vgs until [V]", value=1.0, key="vgs_until_tr")
        vgs_step_tr = st.number_input("Vgs step [V]", value=0.01, key="vgs_step_tr")
        vds_tr = st.number_input("Vds [V] (const)", value=1.5)
        dt = st.number_input("dt [s]", value=1e-4, format="%.2e")

    # --- 実行 ---
    if st.button("Run"):
        hemt = TransistorModel()
        hemt.W = W
        hemt.L = L

        iv = Analyzer.sweep_IV(
            transistor=hemt,
            vds_from=vds_from, vds_until=vds_until, vds_step=vds_step,
            vgs_from=vgs_from_iv, vgs_until=vgs_until_iv, vgs_step=vgs_step_iv,
        )
        transfer = Analyzer.sweep_Vgs(
            transistor=hemt,
            vgs_from=vgs_from_tr, vgs_until=vgs_until_tr, vgs_step=vgs_step_tr,
            vds=vds_tr, dt=dt,
        )

        st.session_state["iv"] = iv
        st.session_state["transfer"] = transfer
        st.session_state["W"] = W
        st.session_state["L"] = L

with r_container:
    # --- 表示 ---
    st.header("Result")
    if "iv" in st.session_state:
        from transistor import Display
        import plotly.io as pio

        st.subheader("I-V Characteristics")
        fig_iv = pio.from_json(Display.generate_IV_map(st.session_state["iv"]))
        st.plotly_chart(fig_iv)

        st.subheader("Transfer Characteristics")
        fig_tr = pio.from_json(Display.generate_Transfer_map(st.session_state["transfer"]))
        st.plotly_chart(fig_tr)

        # --- CSVダウンロード ---
        st.subheader("Download CSV")
        W = st.session_state["W"]
        L = st.session_state["L"]

        buf_iv = io.StringIO()
        csv.writer(buf_iv).writerows(iv_to_list(st.session_state["iv"], W, L))
        st.download_button("Download IV CSV", buf_iv.getvalue(), "IV_HEMT.csv")

        buf_tr = io.StringIO()
        csv.writer(buf_tr).writerows(transfer_to_list(st.session_state["transfer"], W, L))
        st.download_button("Download Transfer CSV", buf_tr.getvalue(), "Transfer_HEMT.csv")