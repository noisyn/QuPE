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


# %%
# Sweep scheme for crosstalk and transfer function measurement
sweepScheme = {'junctionAmplitude (V)': 10e-3,
            'frequencySweepPower (dBm)': 0,
            'startFrequency (Hz)': 100e6,
            'endFrequency (Hz)': 800e6,
            'frequencyStep (Hz)': 5e6,
            'powerSweepFrequency (Hz)': 350e6,
            'startPower (dBm)': -30,
            'endPower (dBm)': 0,
            'powerStep (dBm)': 0.5,
            'modulationFrequency (Hz)': 95,
            'acquisitionTime (s)': 1.0
            }


# %%
# Output continious wave
outputContinuousWave(generalSettingsSG, 'OFF', 350e6, -10, modulationFrequency=None)
# outputContinuousWave(generalSettingsSG, 'OFF', 350e6, -10, modulationFrequency=95)


#%%
# Measure Crosstalk
comment = {'Bias (mV)': -72, 'Current (pA)': 0, 'LockIn T.C (ms)': 300, 'LockIn Sens. (mV)': 20, 'Amplifier': 'Femto'}
frequency, scalingFactorsPowerFunction = measureCrosstalkSignal(generalSettingsSG, sweepScheme, comment)

plt.figure()
plt.title(comment)
plt.plot(frequency/1e6, scalingFactorsPowerFunction, '.')
plt.xlabel('Frequency (MHz)')
plt.ylabel('Scaling (relative)')
plt.show()


#%%
# Measure transfer function
comment = {'Bias (mV)': -72, 'Current (pA)': 100, 'LockIn T.C (ms)': 300, 'LockIn Sens. (mV)': 20, 'Amplifier': 'Femto'}
calibrationValues = {'Frequency': 350e6, 'SourcePower': -10, 'junctionAmplitude (V)': 15e-3, 'CurrentChange': 2.1e-12}
frequency, transmission = measureTransferFunction(generalSettingsSG, sweepScheme, calibrationValues, comment, iterations=1)

plt.figure()
plt.title(comment)
plt.plot(frequency/1e6, transmission, '.')
plt.xlabel('Frequency (MHz)')
plt.ylabel('Transmission (normalized)')
plt.show()


#%%
# Perform frequency sweep with constant amplitude
# Sweep parameters, Note: General settings defined above
sweepScheme = {'junctionAmplitude (V)': 10e-3,
            'startFrequency (Hz)': 100e6,
            'endFrequency (Hz)': 800e6,
            'frequencyStep (Hz)': 5e6,
            'modulationFrequency (Hz)': 95,
            'acquisitionTime (s)': 1.0
            }
comment = {'Bias (mV)': -72, 'Current (pA)': 100}
frequency, lockinSignal, junctionCurrentChange, junctionVoltageMeasured = measureConstantAmplitudeSweep(generalSettingsSG, sweepScheme, comment)

plt.figure()
plt.title(comment)
plt.plot(frequency/1e6, junctionVoltageMeasured/1e-3, '.', label='V_RF = {} mV'.format(sweepScheme['junctionAmplitude (V)']/1e-3))
# plt.plot(frequency/1e6, junctionCurrentChange/1e-12, '.', label='V_RF = {} mV'.format(sweepScheme['junctionAmplitude (V)']/1e-3))
plt.xlabel('Frequency (MHz)')
plt.ylabel('Junction Voltage (mV)')
# plt.ylabel('Junction Current Change (pA)')
plt.legend()
plt.show()


#%%
# Perform power/frequency sweep
# For sweep scheme parameters see above
power, lockinSignal = measurePowerSweep(generalSettingsSG, sweepScheme)
# frequency, lockinSignal = measureFrequencySweep(generalSettingsSG, sweepScheme)
plt.figure()
plt.plot(power, lockinSignal, '.')
# plt.plot(frequency, lockinSignal, '.')
plt.xlabel('Power (dBm)')
# plt.xlabel('Frequency (Hz)')
plt.ylabel('LockIn Signal (V)')
plt.show()