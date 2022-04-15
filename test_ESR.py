#%%
from ESR import *
from DataManagement import *

#%%
generalSettings = {'SG_Name': 'SMA100B',
                    'SG_VisaResource': 'TCPIP::169.254.2.20::hislip0::INSTR',
                    'SG_PowerMin': -30,
                    'SG_PowerMax': 20,
                    'DAQ_Device': 'Dev1',
                    'DAQ_SamplingRate': 10e3,
                    'DAQ_InputChannel_LockIn': 'ai0',
                    'DAQ_InputChannel_SignalValid': 'ai1',
                    'Data_Folder': 'data',
                    'TF_Folder': 'TF',
                    'TF_Latest': '2021-10-20/19-05-22'
                    }

sweepScheme = { 'UseLatestTF': True,
            'junctionAmplitudeForCompensation': 11,
            'frequencySweepPower': -10,
            'startFrequency': 100e6,
            'endFrequency': 700e6,
            'frequencyStep': 2e6,
            'powerSweepFrequency': 200e6,
            'startPower': -30,
            'endPower': -5,
            'powerStep': 1,
            'modulationFrequency': 95,
            'dwellTime': 0.5
            }

#%%
calibrationValues = {'Frequency': 200e6, 'SourcePower': -10, 'JunctionAmplitude': 11e-3, 'LockInValue': 0.565}
frequency, transmission = measureTransferFunction(generalSettings, sweepScheme, calibrationValues, iterations=2)

plt.figure()
plt.plot(frequency, transmission, '.')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Transmission (normalized)')
plt.show()

#%%
frequency, junctionVoltage = measureESRSweep(generalSettings, sweepScheme, 10e-3)
plt.figure()
plt.plot(frequency, junctionVoltage, '.')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Junction Amplitude (V)')
plt.show()

#%%
power, transmission = measurePowerSweep(generalSettings, sweepScheme)

plt.figure()
plt.plot(power, transmission, '.')
plt.xlabel('Power (dBm)')
plt.ylabel('Transmission (a.u.)')
plt.show()

#%%
frequency, transmission = measureFrequencySweep(generalSettings, sweepScheme)

plt.figure()
plt.plot(frequency, transmission, '.')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Transmission (a.u.)')
plt.show()

# %%
outputContinuousWave(generalSettings, 'OFF', 200e6, -10, modulationFrequency=95)

#%%
tfData = loadData(generalSettings['Data_Folder'], '2021-10-20/19-33-57')
frequency = np.array(tfData['Data']['Frequency (Hz)'])
junctionVoltage = np.array(tfData['Data']['Junction Amplitude (V)'])
plt.figure()
plt.plot(frequency, junctionVoltage, '.')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Junction Amplitude (V)')
plt.show()

# %%
