#%%
from NIDAQ import NIDAQ
import numpy as np
import time

#%%
daq = NIDAQ('Dev1', 1e3)

#%%
daq.writeAnalog('ao0',[0])

#%%
data = daq.readAnalog('ai0',1)
print(len(data))
# %%
