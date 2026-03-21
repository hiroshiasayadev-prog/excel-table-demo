
import xarray as xr
import numpy as np

from transistor import Analyzer, Display, TransistorModel

# --- prepare transistor ---
hemt = TransistorModel()

# --- measure it ---

# I-V char
iv_data = Analyzer.sweep_IV(
    transistor=hemt,
    vds_from=0.0,
    vds_until=1.0,
    vds_step=0.01,
    vgs_from=-0.4,
    vgs_until=1.0,
    vgs_step=0.2,
)

# transfer char
transfer_data = Analyzer.sweep_Vgs(
    transistor=hemt,
    vgs_from=-1.0,
    vgs_until=1.0,
    vgs_step=0.01,
    vds=1.5,
)




# --- display result ---

# I-V char
Display.show_IV(iv_data)

# transfer char
Display.show_Transfer(transfer_data)
