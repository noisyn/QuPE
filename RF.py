# Copyright (c) 2022-2023 Taner Esat <t.esat@fz-juelich.de>

import time

import matplotlib.pyplot as plt
import numpy as np

from .DataManagement import *
from .NIDAQ import NIDAQ
from .SMB100B import SMB100B


def convertSignalValid(dataSignalValid, values):
    """Assigns the corresponding power or frequency values to the valid signal.

    Args:
        dataSignalValid (ndarray): Output signal that determines the valid signal times (valid level and frequency) for all analog modulations.
        values (ndarray): Frequency or power values.

    Returns:
        ndarray: Assigned frequency or power values.
    """    
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
    """Outputs an RF signal with specified frequency and power.

    Args:
        generalSettings (dict): General settings of the SG.
        state (str): 'ON': Turns on the RF output. 'OFF': Turns off the RF output.
        frequency (float): Frequency of RF signal in Hz.
        power (float): Power of RF signal in dBm.
        modulationFrequency (float, optional): Modulates the RF output with the specified frequency. Defaults to None: No modulation.
    """    
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
    """Converts Power (dBm) to Voltage (peak-to-zero).

    Args:
        power (float): Power in dBm.
        resistance (float, optional): Resistance in Ohm. Defaults to 50.

    Returns:
        float: Voltage (peak-to-zero)
    """    
    power_mW = np.power(10, power/10)
    voltageRMS = np.sqrt(power_mW * resistance / np.power(10, 3))
    voltagePeak = np.sqrt(2) * voltageRMS
    return voltagePeak

def convertVoltageToPower(voltage, resistance=50):
    """Converts Voltage (peak-to-zero) to Power.

    Args:
        voltage (float): Voltage (peak-to-zero) in V.
        resistance (float, optional): Resistance in Ohm. Defaults to 50.

    Returns:
        float: Power (dBm)
    """    
    voltageRMS = voltage / np.sqrt(2)
    power_mW = np.power(voltageRMS, 2) * np.power(10, 3) / resistance
    power = 10 * np.log10(power_mW)
    return power

def calculatePowerConstantJunctionAmplitude(frequency, junctionVoltage, transferFunctionFrequency, transferFunctionTransmission):
    """Calculates the output powers to apply a constant junction amplitude based on the transfer function.

    Args:
        frequency (ndarray): Frequencies at which a constant junction amplitude is to be applied.
        junctionVoltage (float): Junction amplitude in V.
        transferFunctionFrequency (ndarray): Frequencies from the transfer function.
        transferFunctionTransmission (ndarray): Tranmission values from the transfer function.

    Returns:
        ndarray: Output powers to generate a constant amplitude..
    """    
    junctionVoltage = np.abs(junctionVoltage)
    transmission = np.interp(frequency, transferFunctionFrequency, transferFunctionTransmission)
    sourceVoltages = junctionVoltage / transmission
    sourcePower = convertVoltageToPower(sourceVoltages)

    # plt.figure()
    # plt.plot(frequency, sourcePower, '.')
    # plt.xlabel('Frequency (Hz)')
    # plt.ylabel('Source Power (dBm)')
    # plt.show()

    return sourcePower

def loadTransferFunction(generalSettings):
    """Loads the transfer function data.

    Args:
        generalSettings (dict): General settings of the SG.

    Returns:
        ndarray, ndarray, ndarray, float: Frequencies, Transmissionvalues, Coefficients for polynomial fit (lock-in voltage to junction amplitude), Calibration factor lock-in to current.
    """    
    # Load Transfer Function
    tfData = loadData(generalSettings['TF_Folder'], generalSettings['TF_File'])
    tfFrequency = np.array(tfData['Data']['Frequency (Hz)'])
    tfTransmission = np.array(tfData['Data']['Transmission (normalized)'])
    coeffPolyFit = np.array(tfData['additionalInformation']['coeffPolyFit'])
    calFactorLockInToCurrent = np.float64(tfData['additionalInformation']['calFactorLockInToCurrent'])

    return tfFrequency, tfTransmission, coeffPolyFit, calFactorLockInToCurrent

def loadCrosstalkSignal(generalSettings):
    """Loads the crosstalk data.

    Args:
        generalSettings (dict): General settings of the SG.

    Returns:
        ndarray, ndarray, ndarray: Frequencies, Frequency dependent scaling factors for crosstalk, Coefficients for polynomial fit (source voltage to lock-in voltage).
    """    
    # Load Crosstalk Signal
    ctData = loadData(generalSettings['CT_Folder'], generalSettings['CT_File'])
    ctFrequency = np.array(ctData['Data']['Frequency (Hz)'])
    ctScalingFactorsPowerFunction = np.array(ctData['Data']['Scaling (relative)'])
    coeffPolyFit = np.array(ctData['additionalInformation']['coeffPolyFit'])

    return ctFrequency, ctScalingFactorsPowerFunction, coeffPolyFit

def measureConstantAmplitudeSweep(generalSettings, sweepScheme, comment={}, save=True):
    """Performs a frequency sweep with constant amplitude in the junction using the lock-in detection technique.

    Args:
        generalSettings (dict): General settings of the SG.
        sweepScheme (dict): Definition of the sweep scheme.
        comment (dict, optional): Comments. Defaults to {}.
        save (bool, optional): True: Save measurement data. False: Data is not saved. Defaults to True.

    Returns:
        ndarrays: Frequency, Lock-In signal, Change in junction current, Voltage in junction
    """    
    # Load Transfer Function
    tfFrequency, tfTransmission, coeffPolyFit, calFactorLockInToCurrent = loadTransferFunction(generalSettings)
    polyConvLockInToJunctionAmplitude = np.poly1d(coeffPolyFit)

    # Load Crosstalk Signal
    if generalSettings['UseCT'] == True:
        ctFrequency, ctScalingFactorsPowerFunction, coeffPolyFitCrosstalk = loadCrosstalkSignal(generalSettings)
        polyConvVoltageToLockIn = np.poly1d(coeffPolyFitCrosstalk)

    # Measure frequency sweep at junction amplitude
    numberPoints = int((sweepScheme['endFrequency (Hz)'] - sweepScheme['startFrequency (Hz)'])/sweepScheme['frequencyStep (Hz)']) + 1
    frequencyList = np.linspace(sweepScheme['startFrequency (Hz)'], sweepScheme['endFrequency (Hz)'], numberPoints)
    powerList = calculatePowerConstantJunctionAmplitude(frequencyList, sweepScheme['junctionAmplitude (V)'], tfFrequency, tfTransmission)
    
    plt.figure()
    plt.plot(frequencyList, powerList, '.')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Source Power (dBm)')
    plt.axhline(y = generalSettings['SG_PowerMin (dBm)'], color = 'black', linestyle = '--')
    plt.axhline(y = generalSettings['SG_PowerMax (dBm)'], color = 'black', linestyle = '--')
    plt.show()
    
    frequency, lockinSignal = measureFrequencySweep(generalSettings, sweepScheme, mode='LIST', freqList=frequencyList, powList=powerList, save=False)

    # Correct for Crosstalk
    if generalSettings['UseCT'] == True:         
        sourceVoltageList = convertPowerToVoltage(powerList)
        ctScalingFactors = np.interp(frequency, ctFrequency, ctScalingFactorsPowerFunction)
        calcLockinSignalCrosstalk = polyConvVoltageToLockIn(sourceVoltageList) * ctScalingFactors
        lockinSignal = lockinSignal - calcLockinSignalCrosstalk

    # Convert LockIn Signal to Junction Voltage
    junctionVoltageMeasured = polyConvLockInToJunctionAmplitude(lockinSignal)

    # Convert LockIn Signal to Junction Current Change
    junctionCurrentChange = lockinSignal * calFactorLockInToCurrent

    plt.figure()
    plt.plot(frequency, lockinSignal + calcLockinSignalCrosstalk, '.')
    plt.plot(tfFrequency, lockinSignal, '.')
    plt.plot(frequency, calcLockinSignalCrosstalk, '.', c='black')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Lockin Signal (V)')
    plt.show()

    # Save data
    if save == True:
        additionalInformation = {}
        data = {'Frequency (Hz)': frequency.tolist(), 'LockIn Signal (V)': lockinSignal.tolist(), 'Junction Current Change (A)': junctionCurrentChange.tolist(), 'Junction Amplitude (V)': junctionVoltageMeasured.tolist()}
        saveData(generalSettings, sweepScheme, comment, additionalInformation, data)

    return frequency, lockinSignal, junctionCurrentChange, junctionVoltageMeasured

def measureCrosstalkSignal(generalSettings, sweepScheme, comment={}, resistance=50, save=True):
    """Measures the frequency-dependent crosstalk in the junction using lock-in detection technique.

    Args:
        generalSettings (dict): General settings of the SG.
        sweepScheme (dict): Definition of the sweep scheme.
        comment (dict, optional): Comments. Defaults to {}.
        resistance (float, optional): Resistance in Ohm.. Defaults to 50.
        save (bool, optional): True: Save measurement data. False: Data is not saved. Defaults to True.

    Returns:
        ndarrays: Frequencies, Frequency dependent scaling factors for crosstalk.
    """    
    # Measure power sweep at fixed frequency
    power, lockinSignal = measurePowerSweep(generalSettings, sweepScheme, save=False)
    sourceVoltage = convertPowerToVoltage(power, resistance)

    # Fit 3rd order polynomial to RF Voltage vs LockIn Signal
    coeffPolyFit = np.polyfit(sourceVoltage, lockinSignal, 3)
    polyVoltageToLockIn = np.poly1d(coeffPolyFit)

    plt.figure()
    plt.plot(sourceVoltage / 1e-3, lockinSignal, '.')
    plt.plot(sourceVoltage / 1e-3, polyVoltageToLockIn(sourceVoltage))
    plt.xlabel('RF Amplitude (mV)')
    plt.ylabel('LockIn Signal (V)')
    plt.show()

    # Measure frequency sweep at fixed power
    frequency, lockinSignal = measureFrequencySweep(generalSettings, sweepScheme, save=False)

    # Calculate scaling factors for Power function
    scalingFactorsPowerFunction = np.zeros(len(lockinSignal))
    frequencySweepVoltage = convertPowerToVoltage(sweepScheme['frequencySweepPower (dBm)'], resistance)
    refLockinSignalPowerSweep = polyVoltageToLockIn(frequencySweepVoltage)
    scalingFactorsPowerFunction = lockinSignal / refLockinSignalPowerSweep
    
    # Save data
    if save == True:
        additionalInformation = {'coeffPolyFit': coeffPolyFit.tolist(), 'resistance': resistance}
        data = {'Frequency (Hz)': frequency.tolist(), 'LockIn Signal (V)': lockinSignal.tolist(), 'Scaling (relative)': scalingFactorsPowerFunction.tolist()}
        saveData(generalSettings, sweepScheme, comment, additionalInformation, data, experimentType='CT')

    return frequency, scalingFactorsPowerFunction

def measureTransferFunction(generalSettings, sweepScheme, calibrationValues, comment={}, iterations=1, resistance=50, save=True):
    """Measures the frequency-dependent transfer function using lock-in detection technique.

    Args:
        generalSettings (dict): General settings of the SG.
        sweepScheme (dict): Definition of the sweep scheme.
        calibrationValues (dict): Calibrations values.
        comment (dict, optional): Comments. Defaults to {}.
        iterations (int, optional): Number of iterations for measuring the transfer function. Defaults to 1.
        resistance (float, optional): Resistance in Ohm. Defaults to 50.
        save (bool, optional): True: Save measurement data. False: Data is not saved. Defaults to True.

    Returns:
        ndarrays: Frequencies, Transmission values.
    """    
    # Calculate voltage calibration factors for one fixed frequency
    sourceVoltage = convertPowerToVoltage(calibrationValues['SourcePower'], resistance)
    calFactorSourceToJunction = calibrationValues['junctionAmplitude (V)'] / sourceVoltage

    # Measure power sweep at fixed frequency
    power, lockinSignal = measurePowerSweep(generalSettings, sweepScheme, save=False)

    # Load Crosstalk Signal
    if generalSettings['UseCT'] == True:
        ctFrequency, ctScalingFactorsPowerFunction, coeffPolyFitCrosstalk = loadCrosstalkSignal(generalSettings)
        polyConvVoltageToLockIn = np.poly1d(coeffPolyFitCrosstalk)
        # Correct for Crosstalk
        # ctScalingFactor = np.interp(sweepScheme['frequencySweepPower (dBm)'], ctFrequency, ctScalingFactorsPowerFunction)
        ctScalingFactor = np.interp(sweepScheme['powerSweepFrequency (Hz)'], ctFrequency, ctScalingFactorsPowerFunction)
        sourceVoltageList = convertPowerToVoltage(power)
        calcLockinSignalCrosstalk = polyConvVoltageToLockIn(sourceVoltageList) * ctScalingFactor
        lockinSignal = lockinSignal - calcLockinSignalCrosstalk

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

    # Calculcate calibration factor LockIn to Current change
    lockinSignalCalibrationPower = np.interp(calibrationValues['SourcePower'], power, lockinSignal)
    calFactorLockInToCurrent =  calibrationValues['CurrentChange'] / lockinSignalCalibrationPower 

    if generalSettings['UseTF'] == True:
        # Load Transfer Function
        tfFrequency, tfTransmission, _, _ = loadTransferFunction(generalSettings)
    
    for i in range(iterations):
        if i == 0 and generalSettings['UseTF'] == False:
            # Measure frequency sweep at fixed power
            tfFrequency, lockinSignal = measureFrequencySweep(generalSettings, sweepScheme, save=False)
            # Correct for Crosstalk
            if generalSettings['UseCT'] == True:           
                sourceVoltage = convertPowerToVoltage(sweepScheme['frequencySweepPower (dBm)'])
                ctScalingFactors = np.interp(tfFrequency, ctFrequency, ctScalingFactorsPowerFunction)
                calcLockinSignalCrosstalk = polyConvVoltageToLockIn(sourceVoltage) * ctScalingFactors
                lockinSignal = lockinSignal - calcLockinSignalCrosstalk
            # Convert LockIn Signal to Junction Voltage and Calculate transmission
            junctionVoltageMeasured = polyConvLockInToJunctionAmplitude(lockinSignal)
            tfTransmission = junctionVoltageMeasured / convertPowerToVoltage(sweepScheme['frequencySweepPower (dBm)'])
        else:
            # Measure frequency sweep at constant junction amplitude
            powerList = calculatePowerConstantJunctionAmplitude(tfFrequency, sweepScheme['junctionAmplitude (V)'], tfFrequency, tfTransmission)
            plt.figure()
            plt.plot(tfFrequency, powerList, '.')
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Source Power (dBm)')
            plt.axhline(y = generalSettings['SG_PowerMin (dBm)'], color = 'black', linestyle = '--')
            plt.axhline(y = generalSettings['SG_PowerMax (dBm)'], color = 'black', linestyle = '--')
            plt.show()
            
            tfFrequency, lockinSignal = measureFrequencySweep(generalSettings, sweepScheme, mode='LIST', freqList=tfFrequency, powList=powerList, save=False)
            # Correct for Crosstalk
            if generalSettings['UseCT'] == True:         
                sourceVoltageList = convertPowerToVoltage(powerList)
                ctScalingFactors = np.interp(tfFrequency, ctFrequency, ctScalingFactorsPowerFunction)
                calcLockinSignalCrosstalk = polyConvVoltageToLockIn(sourceVoltageList) * ctScalingFactors
                lockinSignal = lockinSignal - calcLockinSignalCrosstalk         
            # Convert LockIn Signal to Junction Voltage and Calculate transmission
            junctionVoltageMeasured = polyConvLockInToJunctionAmplitude(lockinSignal)
            tfTransmission = junctionVoltageMeasured / convertPowerToVoltage(powerList)
    
    # Clip tranmission values between [0,1]
    tfTransmission = np.clip(tfTransmission, 0.0001, 1)

    plt.figure()
    plt.plot(tfFrequency, lockinSignal + calcLockinSignalCrosstalk, '.')
    plt.plot(tfFrequency, lockinSignal, '.')
    plt.plot(tfFrequency, calcLockinSignalCrosstalk, '.', c='black')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Lockin Signal (V)')
    plt.show()

    # plt.figure()
    # plt.plot(tfFrequency, tfTransmission, '.')
    # plt.xlabel('Frequency (Hz)')
    # plt.ylabel('Transmission (normalized)')
    # plt.show()

    # Save data
    if save == True:
        additionalInformation = {'coeffPolyFit': coeffPolyFit.tolist(), 'calFactorLockInToCurrent': calFactorLockInToCurrent, 'iterations': iterations, 'resistance': resistance, 'calibrationValues': calibrationValues}
        data = {'Frequency (Hz)': tfFrequency.tolist(), 'Transmission (normalized)': tfTransmission.tolist()}
        saveData(generalSettings, sweepScheme, comment, additionalInformation, data, experimentType='TF')

    return tfFrequency, tfTransmission


def measurePowerSweep(generalSettings, sweepScheme, comment={}, save=True):
    """Performs a power sweep at a fixed frequency using lock-in detection technique.

    Args:
        generalSettings (dict): General settings of the SG.
        sweepScheme (dict): Definition of the sweep scheme.
        comment (dict, optional): Comments. Defaults to {}.
        save (bool, optional): True: Save measurement data. False: Data is not saved. Defaults to True.

    Returns:
        ndarrays: Power values, Lock-In signal.
    """    
    # DAQ
    daq = NIDAQ(generalSettings['DAQ_Device'], samplingRate=generalSettings['DAQ_SamplingRate (1/s)'])

    # Connect SG
    sg = SMB100B(generalSettings['SG_VisaResource'])
    sg.connect()
    sg.query('*IDN?')

    # Limit output powers
    sg.setPowerLimits(generalSettings['SG_PowerMin (dBm)'], generalSettings['SG_PowerMax (dBm)'])

    # Setup Pulse modulation
    pulsePeriod = 1/sweepScheme['modulationFrequency (Hz)']
    sg.setPulseMode('SING')
    sg.setPulseTransitionMode('SMO')
    sg.setPulsePeriod(pulsePeriod)
    sg.setPulseWidth(pulsePeriod/2)
    sg.setPulseGeneratorSource('INT')
    sg.switchPulseGeneratorOutputSignalOn()
    sg.switchPulseGeneratorOn()

    # Define Frequency and Power
    sg.setRFFrequencyMode('CW')
    sg.setFrequency(sweepScheme['powerSweepFrequency (Hz)'])
    sg.setPower(sweepScheme['startPower (dBm)'])

    # Setup Power Sweep
    sg.setPowerSweepStart(sweepScheme['startPower (dBm)'])
    sg.setPowerSweepStop(sweepScheme['endPower (dBm)'])
    sg.setPowerSweepStepLog(sweepScheme['powerStep (dBm)'])
    sg.setPowerSweepDwellTime(sweepScheme['acquisitionTime (s)'])
    sg.setPowerSweepShape('SAWT')

    time.sleep(5)

    # Switch on RF
    sg.switchRFOutputOn()

    # Power Sweep mode
    sg.setRFPowerMode('SWE')

    # Acquire Data
    numberPoints = int((sweepScheme['endPower (dBm)'] - sweepScheme['startPower (dBm)'])/sweepScheme['powerStep (dBm)']) + 1
    acquisitionTime = numberPoints * sweepScheme['acquisitionTime (s)']
    daqData = daq.readAnalog([generalSettings['DAQ_InputChannel_LockIn'], generalSettings['DAQ_InputChannel_SignalValid']], acquisitionTime)
    powerList = np.linspace(sweepScheme['startPower (dBm)'], sweepScheme['endPower (dBm)'], numberPoints)

    # Convert to Power vs LockIn Signal
    lockinData = daqData[0,:]
    powerData = convertSignalValid(daqData[1,:], powerList)
    power = np.zeros(len(powerList))
    lockinSignal = np.zeros(len(powerList))
    for i in range(len(powerList)):
        idx = np.where(powerList[i] == powerData)[0]
        if len(idx) > 0:
            power[i] = powerList[i]
            # Drop some percentage of LockIn Data at beginning
            if generalSettings['LockIn_DataDropOff'] > 0 and generalSettings['LockIn_DataDropOff'] < 1:
                stardIdxDrop = int(len(idx) * generalSettings['LockIn_DataDropOff'])
                idx = idx[stardIdxDrop:-1]
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
    """Performs a frequency sweep using lock-in detection technique.

    Args:
        generalSettings (dict): Definition of the sweep scheme.
        sweepScheme (dict): Definition of the sweep scheme.
        mode (str, optional): 'SWE': Frequency sweep at a fixed power. 'LIST': Frequency sweep based on the specified list values. Defaults to 'SWE'.
        freqList (ndarray, optional): List of frequencies. Defaults to None.
        powList (ndarray, optional): List of powers. Defaults to None.
        comment (dict, optional): Comments. Defaults to {}.
        save (bool, optional): True: Save measurement data. False: Data is not saved. Defaults to True.

    Returns:
        ndarrays: Frequency values, Lock-In signal.
    """    
    # DAQ
    daq = NIDAQ(generalSettings['DAQ_Device'], samplingRate=generalSettings['DAQ_SamplingRate (1/s)'])

    # Connect SG
    sg = SMB100B(generalSettings['SG_VisaResource'])
    sg.connect()
    sg.query('*IDN?')

    # Limit output powers
    sg.setPowerLimits(generalSettings['SG_PowerMin (dBm)'], generalSettings['SG_PowerMax (dBm)'])

    # Setup Pulse modulation
    pulsePeriod = 1/sweepScheme['modulationFrequency (Hz)']
    sg.setPulseMode('SING')
    sg.setPulseTransitionMode('SMO')
    sg.setPulsePeriod(pulsePeriod)
    sg.setPulseWidth(pulsePeriod/2)
    sg.setPulseGeneratorSource('INT')
    sg.switchPulseGeneratorOutputSignalOn()
    sg.switchPulseGeneratorOn()

    # Define Frequency and Power
    sg.setRFFrequencyMode('CW')
    sg.setFrequency(sweepScheme['startFrequency (Hz)'])
    if 'frequencySweepPower (dBm)' in sweepScheme:
        sg.setPower(sweepScheme['frequencySweepPower (dBm)'])
    else:
        sg.setPower(generalSettings['SG_PowerMin (dBm)'])

    if mode == 'SWE':
        # Number of points
        numberPoints = int((sweepScheme['endFrequency (Hz)'] - sweepScheme['startFrequency (Hz)'])/sweepScheme['frequencyStep (Hz)']) + 1
        # Setup Frequency Sweep
        sg.setFrequencySweepStart(sweepScheme['startFrequency (Hz)'])
        sg.setFrequencySweepStop(sweepScheme['endFrequency (Hz)'])
        sg.setFrequencySweepStepLinear(sweepScheme['frequencyStep (Hz)'])
        sg.setFrequencySweepDwellTime(sweepScheme['acquisitionTime (s)'])
        sg.setFrequencySweepShape('SAWT')
    elif mode == 'LIST':
        # Setup List Sweep
        if freqList is not None and powList is not None:
            if len(freqList) == len(powList):
                numberPoints = len(freqList)
                sg.defineFrequencyPowerList('tf', freqList.tolist(), powList.tolist(), sweepScheme['acquisitionTime (s)'])

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
    acquisitionTime = numberPoints * sweepScheme['acquisitionTime (s)']
    daqData = daq.readAnalog([generalSettings['DAQ_InputChannel_LockIn'], generalSettings['DAQ_InputChannel_SignalValid']], acquisitionTime)
    if mode == 'SWE':
        frequencyList = np.linspace(sweepScheme['startFrequency (Hz)'], sweepScheme['endFrequency (Hz)'], numberPoints)
    elif mode == 'LIST':
        frequencyList = freqList
    
    # Convert to Frequency vs LockIn Signal
    lockinData = daqData[0,:]
    frequencyData = convertSignalValid(daqData[1,:], frequencyList)
    frequency = np.zeros(len(frequencyList))
    lockinSignal = np.zeros(len(frequencyList))
    for i in range(len(frequencyList)):
        idx = np.where(frequencyList[i] == frequencyData)[0]
        if len(idx) > 0:
            frequency[i] = frequencyList[i]
            # Drop some percentage of LockIn Data at beginning
            if generalSettings['LockIn_DataDropOff'] > 0 and generalSettings['LockIn_DataDropOff'] < 1:
                stardIdxDrop = int(len(idx) * generalSettings['LockIn_DataDropOff'])
                idx = idx[stardIdxDrop:-1]
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