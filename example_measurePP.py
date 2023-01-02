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