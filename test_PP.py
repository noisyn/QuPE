#%%
from PumpProbe import *
import matplotlib.pyplot as plt

#%%
generalSettings = {'AWG_Name': 'M8190A',
                    'AWG_VisaResource': 'TCPIP0::localhost::inst0::INSTR',
                    'AWG_ModeBit': 12,
                    'AWG_Format': 'NRZ',
                    'AWG_MinimumSegmentSize': 320,
                    'AWG_VectorSize': 64,
                    'AWG_SamplingFrequencyMax':12e9,
                    'AWG_SamplingFrequencyMin': 125e6,
                    'AWG_Route': 'DC',
                    'AWG_Channel': 1,
                    'AWG_Amplitude': 150e-3,
                    'AWG_SampleMarkerAmplitude': 500e-3,
                    'AWG_TriggerLevel': 500e-3,
                    'DAQ_Device': 'Dev1',
                    'DAQ_SamplingRate': 1e3,
                    'DAQ_InputChannel_LockIn': 'ai0',
                    'DAQ_OutputChannel_TriggerAWG': 'ao0',
                    'DAQ_OutputAmplitude_TriggerAWG': 0.7,
                    'Data_Folder': 'data'
                    }

Pump = {'name': 'Pump', 'type': 'DC', 'cycle': 'A',
        'startTime': 3e-9, 'endTime': 50e-9, 'sweepTime': False,
        'startDuration': 0.4e-9, 'endDuration': 20e-9, 'sweepDuration': False,
        'startAmplitude': 50e-3, 'endAmplitude': 20e-3, 'sweepAmplitude': False,
        'startFreqRF': 0, 'endFreqRF': 1e-3, 'sweepFreqRF': False}

Probe = {'name': 'Probe', 'type': 'DC', 'cycle': 'A',
        'startTime': 2e-9, 'endTime': 10e-9, 'sweepTime': True,
        'startDuration': 0.4e-9, 'endDuration': 6e-9, 'sweepDuration': False,
        'startAmplitude': 20e-3, 'endAmplitude': 20e-3, 'sweepAmplitude': False,
        'startFreqRF': 0, 'endFreqRF': 1e-3, 'sweepFreqRF': False}

pulseScheme = {'pulses': [Pump, Probe], 'repetitions': 200000, 
                'resolution': 100e-12, 'modulationFreq': 90,
                'sweepSteps': 9}

#%%
# index starts from 0
showPumpProbeSegment(generalSettings, pulseScheme, 8)

#%%
sweepNumber, data = measurePumpProbe(generalSettings, pulseScheme, acquisitionTime=2, settlingTime=2)

# %%
t = np.linspace(Probe['startTime'], Probe['endTime'], pulseScheme['sweepSteps'])
t = t-Pump['startTime']
plt.figure()
plt.plot(t/1e-9, data, '.-')
plt.xlabel('Time (ns)')
plt.ylabel('Amplitude (arb.)')
plt.show()

# % Do measurement
# global stopMM;
# stopMM = 0;
# commentMM = struct('Atom', 'Fe', 'T_K', 1.2, 'B_T', 0.9, 'U_mV', 50, 'I_pA', 10);
# %measureQLA(GeneralSettings, commentMM, pulseScheme);
# %%
