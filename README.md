# QuPE
QuPE is a Python library for pump-probe measurements and constant amplitude radio-frequency sweeps in a scanning tunneling microscope (STM) using the lock-in detection technique.

It allows for the correction of losses due to frequency-dependent transmission in the cabling. Furthermore, additional signals due to capacitive crosstalk can be accounted for when calculating the transfer function.

The generation of the constant amplitude radio-frequency (RF) sweeps essentially follows the description of Paul et al. - [Review of Scientific Instruments 87, 074703 (2016)](https://doi.org/10.1063/1.4955446). However, it extends the implementation by compensation for additional crosttalk signals. The pump-probe measurement technique in the STM is described, for example, by Loth. et al. - [Science 329, 1628 (2010)](https://doi.org/10.1126/science.1191688)

The implementations here are designed for the following hardware:
- Keysight M8190A Arbitrary Waveform Generator
- R&S®SMA100B RF Signal Generator
- NI USB-6212

Current version 0.23 (02.01.2022)

## Installation
Clone the Github repository using
<code>git clone https://github.com/noisyn/QuPE</code>

## Dependencies
QuPE requires the following libraries:
- numpy
- matplotlib
- nidaqmx
- pyvisa

## Documentation
Example code for a pump-probe measurement: [example_measurePP.py](example_measurePP.py)
```python
#%%
from PumpProbe import *
import matplotlib.pyplot as plt

#%%
# General settings of AWG
generalSettingsAWG = {'AWG_Name': 'M8190A',
                    'AWG_VisaResource': 'TCPIP0::localhost::inst0::INSTR',
                    'AWG_ModeBit': 12,
                    'AWG_Format': 'NRZ',
                    'AWG_MinimumSegmentSize': 320,
                    'AWG_VectorSize': 64,
                    'AWG_SamplingFrequencyMax (1/s)': 12e9,
                    'AWG_SamplingFrequencyMin (1/s)': 125e6,
                    'AWG_Route': 'DC',
                    'AWG_Channel': 1,
                    'AWG_Amplitude (V)': 150e-3,
                    'AWG_SampleMarkerAmplitude (V)': 500e-3,
                    'AWG_TriggerLevel (V)': 500e-3,
                    'DAQ_Device': 'Dev1',
                    'DAQ_SamplingRate (1/s)': 1e3,
                    'DAQ_InputChannel_LockIn': 'ai0',
                    'DAQ_OutputChannel_TriggerAWG': 'ao0',
                    'DAQ_OutputAmplitude_TriggerAWG (V)': 0.7,
                    'Data_Folder': 'data'
                    }


#%%
# Sweep scheme
Pump = {'name': 'Pump', 'type': 'DC', 'cycle': 'A',
        'startTime (s)': 3e-9, 'endTime (s)': 50e-9, 'sweepTime': False,
        'startDuration (s)': 0.4e-9, 'endDuration (s)': 20e-9, 'sweepDuration': False,
        'startAmplitude (V)': 50e-3, 'endAmplitude (V)': 20e-3, 'sweepAmplitude': False}

Probe = {'name': 'Probe', 'type': 'DC', 'cycle': 'A',
        'startTime (s)': 2e-9, 'endTime (s)': 10e-9, 'sweepTime': True,
        'startDuration (s)': 0.4e-9, 'endDuration (s)': 6e-9, 'sweepDuration': False,
        'startAmplitude (V)': 20e-3, 'endAmplitude (V)': 20e-3, 'sweepAmplitude': False}

pulseScheme = {'pulses': [Pump, Probe], 'repetitions': 200000, 
                'resolution (s)': 100e-12, 'odulationFreq (Hz)': 90,
                'sweepSteps': 9}


#%%
# Display Pump-Probe scheme
showPumpProbeSegment(generalSettingsAWG, pulseScheme, 8)


#%%
# Perform Pump-Probe measurements
sweepNumber, data = measurePumpProbe(generalSettingsAWG, pulseScheme, acquisitionTime=2, settlingTime=2)


# %%
# Display results
t = np.linspace(Probe['startTime (s)'], Probe['endTime (s)'], pulseScheme['sweepSteps'])
t = t-Pump['startTime (s)']
plt.figure()
plt.plot(t/1e-9, data, '.-')
plt.xlabel('Time (ns)')
plt.ylabel('Lock-In signal (arb.)')
plt.show()
```

Example code for a RF measurements: [example_measureRF.py](example_measureRF.py)
```python
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
```

## License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.