#%%
from RF import *
from DataManagement import *

#%%
# General settings SG
generalSettingsSG = {'SG_Name': 'SMA100B',
                    'SG_VisaResource': 'TCPIP::169.254.2.20::hislip0::INSTR',
                    'SG_PowerMin (dBm)': -30,
                    'SG_PowerMax (dBm)': 20,
                    'DAQ_Device': 'Dev1',
                    'DAQ_SamplingRate (1/s)': 10e3,
                    'DAQ_InputChannel_LockIn': 'ai0',
                    'DAQ_InputChannel_SignalValid': 'ai1',
                    'Data_Folder': 'data',
                    'TF_Folder': 'TF',
                    'TF_File': '2022-12-09/14-37-33',
                    'UseTF': False,
                    'CT_Folder': 'CT',
                    'CT_File': '2022-12-09/13-40-22',
                    'UseCT': True
                    }


#%%
from DataManagement import *
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
tfData = loadData(generalSettingsSG['Data_Folder'], '2022-12-09/14-40-32')
frequency = np.array(tfData['Data']['Frequency (Hz)'])
junctionVoltage = np.array(tfData['Data']['Junction Amplitude (V)'])
plt.figure()
plt.title(tfData['Comment'])

sweepScheme = {'junctionAmplitude (V)': 10e-3,
            'frequencySweepPower (dBm)': -10,
            'startFrequency (Hz)': 100e6,
            'endFrequency (Hz)': 800e6,
            'frequencyStep (Hz)': 5e6,
            'modulationFrequency (Hz)': 95,
            'acquisitionTime (s)': 1.0
            }

def line(x, b):
    return 0*x + b

Vrfmean = np.mean(junctionVoltage)
Vrfstd = np.std(junctionVoltage)

plt.plot(frequency, line(frequency, np.mean(junctionVoltage)), c='black', label='Vrf = {:.1f} +- {:.1f} mV'.format(Vrfmean/1e-3, Vrfstd/1e-3))

plt.plot(frequency, junctionVoltage, '.', label='V_RF = {} mV'.format(sweepScheme['junctionAmplitude (V)']/1e-3))
plt.xlabel('Frequency (MHz)')
plt.ylabel('Junction Amplitude (V)')
plt.ylim(8e-3,12e-3)
plt.legend()
plt.show()

# %%
tfFrequency, tfTransmission, _, _ = loadTransferFunction(generalSettingsSG)
plt.figure()
plt.plot(tfFrequency, tfTransmission, '.')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Transmission (normalized)')
plt.xlim(100e6, 800e6)
plt.ylim(0,0.3)
plt.show()

# %%
import Emia.SPMLibs.Nanonis as nn
import Emia.spectroscopy.broadening as bd

folder = 'spectra'
file = 'Bias-Spectroscopy00002.dat'
fileRF = 'Bias-Spectroscopy00003.dat'
header, data = nn.getSpectroscopyData(folder, file)
header, dataRF = nn.getSpectroscopyData(folder, fileRF)

bias = data[:, 0]
dIdV = data[:, 2]
dIdVRF = dataRF[:, 2]

bd.estimateRFBroadening(bias, dIdV, dIdVRF, [-90e-3, -50e-3], 12e-3)


# %%
