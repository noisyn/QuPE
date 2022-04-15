# Copyright (c) 2022 Taner Esat <t.esat@fz-juelich.de>

from NIDAQ import NIDAQ
from SMB100B import SMB100B
from DataManagement import *
import numpy as np
import matplotlib.pyplot as plt
import time

def convertSignalValid(dataSignalValid, values):
    # Normalize to +1 and -1
    output = np.sign(dataSignalValid - np.max(dataSignalValid)/2)

    # plt.figure()
    # plt.plot(output, '.')
    # plt.show()

    stepNumber = 0
    for i in range(len(output)):
        if output[i] == 1:
            output[i] = values[stepNumber]
        elif output[i] == -1:
            if i < len(output):
                if output[i+1] != -1:
                    stepNumber += 1
                    if stepNumber >= len(values):
                        stepNumber = 0
            output[i] = values[stepNumber]

    return output

def outputContinuousWave(generalSettings, state, frequency, power, modulationFrequency=None):
    # Connect SG
    sg = SMB100B(generalSettings['SG_VisaResource'])
    sg.connect()
    sg.query('*IDN?')

    if state == 'ON':
        # Setup Pulse modulation
        if modulationFrequency is not None:
            pulsePeriod = 1/modulationFrequency
            sg.setPulseMode('SING')
            sg.setPulsePeriod(pulsePeriod)
            sg.setPulseWidth(pulsePeriod/2)
            sg.setPulseGeneratorSource('INT')
            sg.switchPulseGeneratorOutputSignalOn()
            sg.switchPulseGeneratorOn()
        else:
            sg.switchPulseGeneratorOutputSignalOff()
            sg.switchPulseGeneratorOff()
        # Define Frequency and Power
        sg.setRFFrequencyMode('CW')
        sg.setFrequency(frequency)
        sg.setPower(power)
        # Switch on RF
        sg.switchRFOutputOn()
    elif state == 'OFF':
        # Turn off all signals and switch to CW mode
        sg.switchRFOutputOff()
        sg.switchPulseGeneratorOutputSignalOff()
        sg.switchPulseGeneratorOff()
        sg.setRFFrequencyMode('CW')

    # Disconnect
    sg.disconnect()

def convertPowerToVoltage(power, resistance=50):
    # Convert Power (dBm) to Voltage (peak-to-zero)
    power_mW = np.power(10, power/10)
    voltageRMS = np.sqrt(power_mW * resistance / np.power(10, 3))
    voltagePeak = np.sqrt(2) * voltageRMS
    return voltagePeak

def convertVoltageToPower(voltage, resistance=50):
    # Convert Voltage (peak-to-zero) to Power (dBm)
    voltageRMS = voltage / np.sqrt(2)
    power_mW = np.power(voltageRMS, 2) * np.power(10, 3) / resistance
    power = 10 * np.log10(power_mW)
    return power

def calculatePowerConstantJunctionAmplitude(frequency, junctionVoltage, transferFunctionFrequency, transferFunctionTransmission):
    junctionVoltage = np.abs(junctionVoltage)
    transmission = np.interp(frequency, transferFunctionFrequency, transferFunctionTransmission)
    sourceVoltages = junctionVoltage / transmission
    sourcePower = convertVoltageToPower(sourceVoltages)

    plt.figure()
    plt.plot(frequency, sourcePower, '.')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Source Power (dBm)')
    plt.show()

    return sourcePower

def loadTransferFunction(generalSettings):
    # Load Transfer Function
    tfData = loadData(generalSettings['TF_Folder'], generalSettings['TF_Latest'])
    tfFrequency = np.array(tfData['Data']['Frequency (Hz)'])
    tfTransmission = np.array(tfData['Data']['Transmission (normalized)'])
    coeffPolyFit =np.array( tfData['additionalInformation']['coeffPolyFit'])

    return tfFrequency, tfTransmission, coeffPolyFit

def measureESRSweep(generalSettings, sweepScheme, junctionVoltage, comment={}, save=True):
    # Load Transfer Function
    tfFrequency, tfTransmission, coeffPolyFit = loadTransferFunction(generalSettings)
    polyConvLockInToJunctionAmplitude = np.poly1d(coeffPolyFit)

    # Measure frequency sweep at junction amplitude
    numberPoints = int((sweepScheme['endFrequency'] - sweepScheme['startFrequency'])/sweepScheme['frequencyStep']) + 1
    frequencyList = np.linspace(sweepScheme['startFrequency'], sweepScheme['endFrequency'], numberPoints)
    powerList = calculatePowerConstantJunctionAmplitude(frequencyList, junctionVoltage, tfFrequency, tfTransmission)
    # powerList = np.nan_to_num(powerList, nan=-30)
    frequency, lockinSignal = measureFrequencySweep(generalSettings, sweepScheme, mode='LIST', freqList=frequencyList, powList=powerList, save=False)

    # Convert LockIn Signal to Junction Voltage
    junctionVoltage = polyConvLockInToJunctionAmplitude(lockinSignal)

    # Save data
    if save == True:
        additionalInformation = {}
        data = {'Frequency (Hz)': frequency.tolist(), 'Junction Amplitude (V)': junctionVoltage.tolist()}
        saveData(generalSettings, sweepScheme, comment, additionalInformation, data)

    return frequency, junctionVoltage


def measureTransferFunction(generalSettings, sweepScheme, calibrationValues, comment={}, iterations=1, resistance=50, save=True):
    # Calculate voltage calibration factors for one fixed frequency
    sourceVoltage = convertPowerToVoltage(calibrationValues['SourcePower'], resistance)
    calFactorSourceToJunction = calibrationValues['JunctionAmplitude'] / sourceVoltage

    # Measure power sweep at fixed frequency
    power, lockinSignal = measurePowerSweep(generalSettings, sweepScheme, save=False)

    # Convert Source Power to Junction Voltage
    junctionVoltages = convertPowerToVoltage(power)*calFactorSourceToJunction
    idx = np.argsort(lockinSignal)
    lockinSignal = lockinSignal[idx]
    junctionVoltages = junctionVoltages[idx]

    # Fit 3rd order polynomial to Junction Voltage vs LockIn Signal
    coeffPolyFit = np.polyfit(lockinSignal, junctionVoltages, 3)
    polyConvLockInToJunctionAmplitude = np.poly1d(coeffPolyFit)

    plt.figure()
    plt.plot(lockinSignal, junctionVoltages, '.')
    plt.plot(lockinSignal, polyConvLockInToJunctionAmplitude(lockinSignal))
    plt.xlabel('LockIn Signal (V)')
    plt.ylabel('Junction Amplitude (V)')
    plt.show()

    if sweepScheme['UseLatestTF'] == True:
        # Load Transfer Function
        tfFrequency, tfTransmission, _ = loadTransferFunction(generalSettings)
    
    for i in range(iterations):
        if i == 0 and sweepScheme['UseLatestTF'] == False:
            # Measure frequency sweep at fixed power
            tfFrequency, lockinSignal = measureFrequencySweep(generalSettings, sweepScheme, save=False)
            # Convert LockIn Signal to Junction Voltage and Calculate transmission
            junctionVoltage = polyConvLockInToJunctionAmplitude(lockinSignal)
            tfTransmission = junctionVoltage / convertPowerToVoltage(sweepScheme['frequencySweepPower'])
        else:
            # Measure frequency sweep at constant junction amplitude
            junctionVoltage = sweepScheme['junctionAmplitudeForCompensation']
            powerList = calculatePowerConstantJunctionAmplitude(tfFrequency, junctionVoltage, tfFrequency, tfTransmission)
            # powerList = np.nan_to_num(powerList, nan=-30)
            tfFrequency, lockinSignal = measureFrequencySweep(generalSettings, sweepScheme, mode='LIST', freqList=tfFrequency, powList=powerList, save=False)
            # Convert LockIn Signal to Junction Voltage and Calculate transmission
            junctionVoltage = polyConvLockInToJunctionAmplitude(lockinSignal)
            devFactorTransmisson = junctionVoltage / convertPowerToVoltage(powerList)
            tfTransmission = tfTransmission * devFactorTransmisson

    plt.figure()
    plt.plot(tfFrequency, tfTransmission, '.')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Transmission (normalized)')
    plt.show()

    # Save data
    if save == True:
        additionalInformation = {'coeffPolyFit': coeffPolyFit.tolist(), 'iterations': iterations, 'resistance': resistance, 'calibrationValues': calibrationValues}
        data = {'Frequency (Hz)': tfFrequency.tolist(), 'Transmission (normalized)': tfTransmission.tolist()}
        saveData(generalSettings, sweepScheme, comment, additionalInformation, data, experimentType='TF')

    return tfFrequency, tfTransmission


def measurePowerSweep(generalSettings, sweepScheme, comment={}, save=True):
    # DAQ
    daq = NIDAQ(generalSettings['DAQ_Device'], samplingRate=generalSettings['DAQ_SamplingRate'])

    # Connect SG
    sg = SMB100B(generalSettings['SG_VisaResource'])
    sg.connect()
    sg.query('*IDN?')

    # Limit output powers
    sg.setPowerLimits(generalSettings['SG_PowerMin'], generalSettings['SG_PowerMax'])

    # Setup Pulse modulation
    pulsePeriod = 1/sweepScheme['modulationFrequency']
    sg.setPulseMode('SING')
    sg.setPulsePeriod(pulsePeriod)
    sg.setPulseWidth(pulsePeriod/2)
    sg.setPulseGeneratorSource('INT')
    sg.switchPulseGeneratorOutputSignalOn()
    sg.switchPulseGeneratorOn()

    # Define Frequency and Power
    sg.setRFFrequencyMode('CW')
    sg.setFrequency(sweepScheme['powerSweepFrequency'])
    sg.setPower(sweepScheme['startPower'])

    # Setup Power Sweep
    sg.setPowerSweepStart(sweepScheme['startPower'])
    sg.setPowerSweepStop(sweepScheme['endPower'])
    sg.setPowerSweepStepLog(sweepScheme['powerStep'])
    sg.setPowerSweepDwellTime(sweepScheme['dwellTime'])
    sg.setPowerSweepShape('SAWT')

    time.sleep(5)

    # Switch on RF
    sg.switchRFOutputOn()

    # Power Sweep mode
    sg.setRFPowerMode('SWE')

    # Acquire Data
    numberPoints = int((sweepScheme['endPower'] - sweepScheme['startPower'])/sweepScheme['powerStep']) + 1
    acquisitionTime = numberPoints * sweepScheme['dwellTime']
    daqData = daq.readAnalog([generalSettings['DAQ_InputChannel_LockIn'], generalSettings['DAQ_InputChannel_SignalValid']], acquisitionTime)
    powerList = np.linspace(sweepScheme['startPower'], sweepScheme['endPower'], numberPoints)

    # Convert to Power vs LockIn Signal
    lockinData = daqData[0,:]
    powerData = convertSignalValid(daqData[1,:], powerList)
    power = np.zeros(len(powerList))
    lockinSignal = np.zeros(len(powerList))
    for i in range(len(powerList)):
        idx = np.where(powerList[i] == powerData)
        if len(idx) > 0:
            power[i] = powerList[i]
            lockinSignal[i] = np.mean(lockinData[idx])

    # Turn off all signals and switch to CW mode
    sg.switchRFOutputOff()
    sg.switchPulseGeneratorOutputSignalOff()
    sg.switchPulseGeneratorOff()
    sg.setRFPowerMode('CW')

    # Disconnect
    sg.disconnect()

    # Save data
    if save == True:
        additionalInformation = {}
        data = {'Power (dBm)': power.tolist(), 'LockIn Signal (V)': lockinSignal.tolist()}
        saveData(generalSettings, sweepScheme, comment, additionalInformation, data)

    return power, lockinSignal


def measureFrequencySweep(generalSettings, sweepScheme, mode='SWE', freqList=None, powList=None, comment={}, save=True):
    # DAQ
    daq = NIDAQ(generalSettings['DAQ_Device'], samplingRate=generalSettings['DAQ_SamplingRate'])

    # Connect SG
    sg = SMB100B(generalSettings['SG_VisaResource'])
    sg.connect()
    sg.query('*IDN?')

    # Limit output powers
    sg.setPowerLimits(generalSettings['SG_PowerMin'], generalSettings['SG_PowerMax'])

    # Setup Pulse modulation
    pulsePeriod = 1/sweepScheme['modulationFrequency']
    sg.setPulseMode('SING')
    sg.setPulsePeriod(pulsePeriod)
    sg.setPulseWidth(pulsePeriod/2)
    sg.setPulseGeneratorSource('INT')
    sg.switchPulseGeneratorOutputSignalOn()
    sg.switchPulseGeneratorOn()

    # Define Frequency and Power
    sg.setRFFrequencyMode('CW')
    sg.setFrequency(sweepScheme['startFrequency'])
    sg.setPower(sweepScheme['frequencySweepPower'])

    if mode == 'SWE':
        # Number of points
        numberPoints = int((sweepScheme['endFrequency'] - sweepScheme['startFrequency'])/sweepScheme['frequencyStep']) + 1
        # Setup Frequency Sweep
        sg.setFrequencySweepStart(sweepScheme['startFrequency'])
        sg.setFrequencySweepStop(sweepScheme['endFrequency'])
        sg.setFrequencySweepStepLinear(sweepScheme['frequencyStep'])
        sg.setFrequencySweepDwellTime(sweepScheme['dwellTime'])
        sg.setFrequencySweepShape('SAWT')
    elif mode == 'LIST':
        # Setup List Sweep
        if freqList is not None and powList is not None:
            if len(freqList) == len(powList):
                numberPoints = len(freqList)
                sg.defineFrequencyPowerList('tf', freqList.tolist(), powList.tolist(), sweepScheme['dwellTime'])

    time.sleep(5)

    # Switch on RF
    sg.switchRFOutputOn()    

    if mode == 'SWE':
        # Frequency Sweep mode
        sg.setRFFrequencyMode('SWE')
    elif mode == 'LIST':
        # List Sweep mode
        sg.setRFFrequencyMode('LIST')

    # Acquire Data
    acquisitionTime = numberPoints * sweepScheme['dwellTime']
    daqData = daq.readAnalog([generalSettings['DAQ_InputChannel_LockIn'], generalSettings['DAQ_InputChannel_SignalValid']], acquisitionTime)
    if mode == 'SWE':
        frequencyList = np.linspace(sweepScheme['startFrequency'], sweepScheme['endFrequency'], numberPoints)
    elif mode == 'LIST':
        frequencyList = freqList
    
    # Convert to Frequency vs LockIn Signal
    lockinData = daqData[0,:]
    frequencyData = convertSignalValid(daqData[1,:], frequencyList)
    frequency = np.zeros(len(frequencyList))
    lockinSignal = np.zeros(len(frequencyList))
    for i in range(len(frequencyList)):
        idx = np.where(frequencyList[i] == frequencyData)
        if len(idx) > 0:
            frequency[i] = frequencyList[i]
            lockinSignal[i] = np.mean(lockinData[idx])

    # Turn off all signals and switch to CW mode
    sg.switchRFOutputOff()
    sg.switchPulseGeneratorOutputSignalOff()
    sg.switchPulseGeneratorOff()
    sg.setRFFrequencyMode('CW')

    # Disconnect
    sg.disconnect()

    # Save data
    if save == True:
        if freqList is None and powList is None:
            freqList = []
            powList = []
            additionalInformation = {'mode': mode, 'freqList': freqList, 'powList': powList}
        else:
            additionalInformation = {'mode': mode, 'freqList': freqList.tolist(), 'powList': powList.tolist()}
        data = {'Frequency (Hz)': frequency.tolist(), 'LockIn Signal (V)': lockinSignal.tolist()}
        saveData(generalSettings, sweepScheme, comment, additionalInformation, data)

    return frequency, lockinSignal