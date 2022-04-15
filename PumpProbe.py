# Copyright (c) 2022 Taner Esat <t.esat@fz-juelich.de>

from M8190 import  M8190A
from NIDAQ import NIDAQ
from DataManagement import *
import numpy as np
import matplotlib.pyplot as plt
import os
import time

def calculateSegmentParameter(generalSettings, pulseScheme):
    # Calculate duration of one cycle and one segment
    cycle_duration = (1/pulseScheme['modulationFreq'])/2
    segment_duration = cycle_duration / pulseScheme['repetitions']

    # Calculate sampling frequency
    sampling_frequency = round(1 / pulseScheme['resolution'])    
    if sampling_frequency < generalSettings['AWG_SamplingFrequencyMin']:
        sampling_frequency = generalSettings['AWG_SamplingFrequencyMin']
    elif sampling_frequency > generalSettings['AWG_SamplingFrequencyMax']:
        sampling_frequency = generalSettings['AWG_SamplingFrequencyMax']

    # Estimate adjusted/new time resolution and number of points per segment
    dt = 1 / sampling_frequency
    points_per_segment = round(segment_duration / dt)

    if points_per_segment < generalSettings['AWG_MinimumSegmentSize']:
        points_per_segment = generalSettings['AWG_MinimumSegmentSize']
    points_per_segment = generalSettings['AWG_VectorSize'] * round(points_per_segment / generalSettings['AWG_VectorSize'])
    dt = segment_duration / points_per_segment
    sampling_frequency = round(1/dt)

    # Check Sampling frequency 
    if sampling_frequency < generalSettings['AWG_SamplingFrequencyMin'] or sampling_frequency > generalSettings['AWG_SamplingFrequencyMax']:
        errorMessage = 'Invalid parameters set:\nSampling frequency: {} Hz\nPoints per Segment: {}'.format(sampling_frequency, points_per_segment)
        raise Exception(errorMessage)

    return points_per_segment, sampling_frequency

def showPumpProbeSegment(generalSettings, pulseScheme, sweepStep):
    # Calculate duration of one cycle and one segment
    cycle_duration = (1/pulseScheme['modulationFreq'])/2
    segment_duration = cycle_duration / pulseScheme['repetitions']
    points_per_segment, sampling_frequency = calculateSegmentParameter(generalSettings, pulseScheme)   

    t = np.linspace(0, segment_duration, points_per_segment)
    segment_cycleA, segment_cycleB = genPumpProbeSegments(generalSettings, pulseScheme, sweepStep, displayingMode=True)

    plt.figure()
    plt.plot(t, segment_cycleA, label='A')
    plt.plot(t, segment_cycleB, label='B')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude (V)')
    plt.legend()
    plt.show()

    print('Sampling frequency: {} Hz'.format(sampling_frequency))
    print('Points per segment: {}'.format(points_per_segment))
    print('Time resolution: {} s'.format(1/sampling_frequency))
    print('Calculated modulation frequency: {} Hz'.format(1/(2*points_per_segment/sampling_frequency*pulseScheme['repetitions'])))


def genPumpProbeSegments(generalSettings, pulseScheme, sweepStep, displayingMode=False):
    # Calculate duration of one cycle and one segment
    cycle_duration = (1/pulseScheme['modulationFreq'])/2
    segment_duration = cycle_duration / pulseScheme['repetitions']

    points_per_segment, sampling_frequency = calculateSegmentParameter(generalSettings, pulseScheme)

    # Scaling factor for DAC values of Amplitude
    scalingAmplitude =  2**(generalSettings['AWG_ModeBit']-1) / generalSettings['AWG_Amplitude']

    if displayingMode == True:
        segment_cycleA = np.zeros(points_per_segment)
        segment_cycleB = np.zeros(points_per_segment)
    elif displayingMode == False:   
        segment_cycleA = np.zeros(points_per_segment, dtype=np.int16)
        segment_cycleB = np.zeros(points_per_segment, dtype=np.int16)

    ppt = points_per_segment / segment_duration
    for pulse in pulseScheme['pulses']:
        if pulse['type'] == 'DC':
            if pulse['sweepTime']:
                time_offset = (pulse['endTime'] - pulse['startTime'])/(pulseScheme['sweepSteps']-1) * sweepStep
                start_time = pulse['startTime'] + time_offset
            else:
                start_time = pulse['startTime']

            if pulse['sweepDuration']:
                additional_duration = (pulse['endDuration'] - pulse['startDuration'])/(pulseScheme['sweepSteps']-1) * sweepStep
                duration = pulse['startDuration'] + additional_duration
            else:
                duration = pulse['startDuration']

            if pulse['sweepAmplitude']:
                additional_amplitude = (pulse['endAmplitude'] - pulse['startAmplitude'])/(pulseScheme['sweepSteps']-1) * sweepStep
                amplitude = pulse['startAmplitude'] + additional_amplitude
            else:
                amplitude = pulse['startAmplitude']

            if displayingMode == False:
                # Amplitude in DAC values
                amplitude = round(2 * amplitude * scalingAmplitude)

                if amplitude >= (2**(generalSettings['AWG_ModeBit']-1)):
                    amplitude = 2**(generalSettings['AWG_ModeBit']-1) - 1
                elif amplitude <= (-1)*(2**(generalSettings['AWG_ModeBit']-1)):
                    amplitude = (-1)*(2**(generalSettings['AWG_ModeBit']-1))

                amplitude = np.int16(amplitude)

            start_index = round(ppt * start_time)
            end_index = round(ppt * (start_time + duration))
            if pulse['cycle'] == 'A':
                segment_cycleA[start_index:end_index] += amplitude
            elif pulse['cycle'] == 'B':
                segment_cycleB[start_index:end_index] += amplitude

    if displayingMode == True:
        return segment_cycleA, segment_cycleB
    elif displayingMode == False:    
        # Waveform Data Format
        segment_cycleA = np.bitwise_or(np.left_shift(segment_cycleA, 4),np.int16(1))
        segment_cycleB = np.bitwise_or(np.left_shift(segment_cycleB, 4),np.int16(0))

        cwd = os.getcwd()
        fileCycleA = os.path.join(cwd, 'tmp', 'cycleA.bin')
        fileCycleB = os.path.join(cwd, 'tmp', 'cycleB.bin')

        segment_cycleA.transpose().tofile(fileCycleA)
        segment_cycleB.transpose().tofile(fileCycleB)

        return fileCycleA, fileCycleB, sampling_frequency

def measurePumpProbe(generalSettings, pulseScheme, acquisitionTime, settlingTime, comment={}, save=True):
    # DAQ
    daq = NIDAQ(generalSettings['DAQ_Device'], samplingRate=generalSettings['DAQ_SamplingRate'])

    # Connect AWG
    awg = M8190A(generalSettings['AWG_VisaResource'])
    awg.connect()
    awg.query('*IDN?')
    # Initialize / General
    awg.setCoupling(decouple=True)
    awg.setFormat(generalSettings['AWG_Channel'], generalSettings['AWG_Format'])
    # Route 
    awg.setOutputRoute(generalSettings['AWG_Channel'], generalSettings['AWG_Route'])
    # Trigger
    awg.setTriggerSource(source='EXT')
    awg.setTriggerImpedance(impedance='HIGH')
    awg.setTriggerPolarity(polarity='POS')
    awg.setTriggerLevel(level=generalSettings['AWG_TriggerLevel'])
    awg.setTriggerMode(generalSettings['AWG_Channel'], 'TRIG')
    # Amplitudes
    awg.setAmplitude(generalSettings['AWG_Channel'], generalSettings['AWG_Amplitude'])
    awg.setMarkerAmplitude(generalSettings['AWG_Channel'], generalSettings['AWG_SampleMarkerAmplitude'], marker='SAMP')
    awg.setMarkerOffset(generalSettings['AWG_Channel'], 0, marker='SAMP')
    # Set Sampling Frequency
    _, sampling_frequency = calculateSegmentParameter(generalSettings, pulseScheme)
    awg.setSamplingFrequency(sampling_frequency)
    
    # Check if ready
    print(awg.query('*OPC?'))
    time.sleep(5)

    # Delete all Sequences
    awg.deleteSequences(generalSettings['AWG_Channel'])
    # Define Sequence Table
    sequenceTable = [{'entryNumber': '0', 'segmentID': '1', 'loop': pulseScheme['repetitions']}, 
                    {'entryNumber': '1', 'segmentID': '2', 'loop': pulseScheme['repetitions']}]
    awg.defineSequence(generalSettings['AWG_Channel'], sequenceTable, 'COND')
    # Sequence Mode
    awg.setSequencingMode(generalSettings['AWG_Channel'], mode='STS')
    # Switch Output On
    awg.switchOutputOn(generalSettings['AWG_Channel'])

    # Check if ready
    print(awg.query('*OPC?'))
    time.sleep(5)

    sweepNumber = np.zeros(pulseScheme['sweepSteps'])
    lockinSignal = np.zeros(pulseScheme['sweepSteps'])
    for i in range(pulseScheme['sweepSteps']):
        # Reset DAQ Trigger
        daq.writeAnalog(generalSettings['DAQ_OutputChannel_TriggerAWG'],[0])
        # Generate Segments A and B
        fileCycleA, fileCycleB, sampling_frequency = genPumpProbeSegments(generalSettings, pulseScheme, sweepStep=i)
        awg.loadSegmentFromBin(generalSettings['AWG_Channel'], 1, fileCycleA)
        awg.loadSegmentFromBin(generalSettings['AWG_Channel'], 2, fileCycleB)
        # Start Channel
        awg.playChannel(generalSettings['AWG_Channel'])
        time.sleep(1)
        # Trigger AWG using DAQ
        triggerPulse = np.linspace(0, generalSettings['DAQ_OutputAmplitude_TriggerAWG'], 50)
        daq.writeAnalog(generalSettings['DAQ_OutputChannel_TriggerAWG'], triggerPulse)
        # Wait settling time
        time.sleep(settlingTime)
        # Acquire Data
        daqData = daq.readAnalog(generalSettings['DAQ_InputChannel_LockIn'], acquisitionTime)
        sweepNumber[i] = i
        lockinSignal[i] = np.mean(daqData)
        # Stop Channel
        awg.stopChannel(generalSettings['AWG_Channel'])

    # Reset
    daq.writeAnalog(generalSettings['DAQ_OutputChannel_TriggerAWG'],[0])
    awg.switchOutputOff(generalSettings['AWG_Channel'])
    # Disconnect
    awg.disconnect()

    # Save data
    if save == True:
        additionalInformation = {'sampling_frequency': sampling_frequency, 'acquisitionTime': acquisitionTime, 'settlingTime': settlingTime}
        lockinSignal = {'Sweep number (1)': sweepNumber.tolist(), 'LockIn Signal (a.u.)': lockinSignal.tolist()}
        saveData(generalSettings, pulseScheme, comment, additionalInformation, lockinSignal)

    return sweepNumber, lockinSignal