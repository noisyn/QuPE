# Copyright (c) 2022 Taner Esat <t.esat@fz-juelich.de>

import pyvisa
import numpy as np

class SMB100B():
    def __init__(self, VisaResourceString):
        self.rm = pyvisa.ResourceManager()
        self.VisaResourceString = VisaResourceString
        self.connected = False
        self.maxOutputPower = None
        self.minOutputPower = None

    def connect(self):
        """Connects to the Rohde&Schwarz Signal Generator SMA100B.
        """        
        try:
            self.inst = self.rm.open_resource(self.VisaResourceString)
            self.inst.write_termination = '\n'
            self.inst.read_termination = '\n'
            self.inst.timeout = 5000
            self.connected = True
        except pyvisa.VisaIOError:
            resp = 'Could not connect to Rohde&Schwarz SMA100B.\nPlease check the device settings.'
            print(resp)
    
    def disconnect(self):
        """Disconnects from RF singal generator.
        """        
        self.inst.close()
        self.connected = False

    def query(self, cmd):
        resp = ''
        err = False
        if self.connected:
            try:
                resp = self.inst.query(cmd)
                print(resp)
            except pyvisa.Error:
                resp = 'Could not send query to instrument.'
                err = True
                print(resp)
        return err, resp
    
    def write(self, cmd):
        if self.connected:
            try:
                self.inst.write(cmd)
            except pyvisa.Error:
                resp = 'Could not write to instrument.'
                print(resp)
            
    def setPowerLimits(self, minPower, maxPower):
        """Sets an lower and upper limit for the RF output power.

        Args:
            minPower (float): Lower limit for the RF output in dBm.
            maxPower (float): Upper limit for the RF output in dBm.
        """        
        self.minOutputPower = minPower
        self.maxOutputPower = maxPower
    
    def setFrequency(self, frequency):
        """Sets the frequency in CW and sweep mode.

        Args:
            frequency (float): Frequency in Hertz (Hz).
        """        
        self.write(':FREQ:CW {}'.format(frequency))
    
    def setPower(self, power):
        """Sets the level at the RF output connector.

        Args:
            power (float): Level at the RF output in dBm.
        """ 
        # Clip/limit output power  
        if self.maxOutputPower is not None and self.minOutputPower is not None:
            if power > self.maxOutputPower:
                power = self.maxOutputPower
            elif power < self.minOutputPower:
                power = self.minOutputPower

        self.write('SOUR:POW:POW {}'.format(power))
    
    def switchRFOutputOn(self):
        """Activates the RF output signal.
        """        
        self.write(':OUTP ON')
    
    def switchRFOutputOff(self):
        """Deactivates the RF output signal.
        """        
        self.write(':OUTP OFF')
    
    def setPulseMode(self, mode='SING'):
        """Selects the mode for the pulse modulation.

        Args:
            mode (str, optional): 'SING': Generates a single pulse. 'DOUBl': Generates two pulses within one pulse period. 'PTR': Generates a user-defined pulse train.. Defaults to 'SING'.
        """        
        if mode == 'SING' or mode == 'DOUB' or mode == 'PTR':
            self.write(':PULM:MODE {}'.format(mode))
    
    def setPulsePeriod(self, period):
        """Sets the period of the generated pulse, that means the repetition frequency of the internally generated modulation signal.

        Args: (float): Period in seconds (s).
        """        
        self.write(':PULM:PER {}'.format(period))
    
    def setPulseWidth(self, width):
        """Sets the width of the generated pulse, that means the pulse length. It must be at least 20ns less than the set pulse period.

        Args:
            width (float): Pulse width in seconds (s).
        """        
        self.write(':PULM:WIDT {}'.format(width))
    
    def switchPulseGeneratorOn(self):
        """Activates pulse modulation.
        """        
        self.write(':PULM:STAT ON')
    
    def switchPulseGeneratorOff(self):
        """Deactivates pulse modulation.
        """        
        self.write(':PULM:STAT OFF')
    
    def setPulseGeneratorSource(self, source='INT'):
        """Selects between the internal (pulse generator) or an external pulse signal for the modulation.

        Args:
            source (str, optional): 'INT': Internal. 'EXT': External. Defaults to 'INT'.
        """        
        if source == 'INT' or source == 'EXT':
            self.write(':PULM:SOUR {}'.format(source))
    
    def switchPulseGeneratorOutputSignalOn(self):
        """Activates the output of the pulse modulation signal
        """        
        self.write('PGEN:OUTP ON')
    
    def switchPulseGeneratorOutputSignalOff(self):
        """Deactivates the output of the pulse modulation signal
        """        
        self.write('PGEN:OUTP OFF')
    
    def setFrequencySweepDwellTime(self, dwell):
        """Sets the dwell time for a frequency sweep step.

        Args:
            dwell (float): Dwell time in seconds (s).
        """        
        self.write('SWE:FREQ:DWEL {}'.format(dwell))
    
    def setFrequencySweepSpacing(self, spacing):
        """Selects the mode for the calculation of the frequency intervals, with which the current frequency at each step is increased or decreased.

        Args:
            spacing (str): 'LIN': Linear.'LOG': Logarithmic.
        """        
        if spacing == 'LIN' or spacing == 'LOG':
            self.write(':SWE:FREQ:SPAC {}'.format(spacing))
    
    def setFrequencySweepPoints(self, points):
        """Sets the number of steps within the RF frequency sweep range.

        Args:
            points (inter): Number of points.
        """        
        self.write(':SWE:FREQ:POIN {}'.format(points))
    
    def setFrequencySweepStepLinear(self, step):
        """Sets the step width for linear sweeps.

        Args:
            step (float): Step width in Hertz (Hz).
        """        
        self.write(':SOUR:SWE:FREQ:STEP:LIN {}'.format(step))
    
    def setFrequencySweepShape(self, shape):
        """Determines the waveform shape for a frequency sweep sequence.

        Args:
            shape (str): 'SAWT': Sawtooth. 'TRI': Triangle.
        """        
        if shape == 'SAWT' or shape == 'TRI':
            self.write(':SWE:FREQ:SHAP {}'.format(shape))

    def setFrequencySweepStart(self, start):
        """Sets the start frequency for the RF sweep.

        Args:
            start (float): Frequency in Hertz (Hz).
        """        
        self.write(':SOUR:FREQ:STAR {}'.format(start))
    
    def setFrequencySweepStop(self, stop):
        """Sets the stop frequency range for the RF sweep.

        Args:
            stop (float): Frequency in Hertz (Hz).
        """        
        self.write(':SOUR:FREQ:STOP {}'.format(stop))
        
    def setRFFrequencyMode(self, mode):
        """Sets the frequency mode for generating the RF output signal.

        Args:
            mode (str): 'CW' or 'FIX': fixed frequency mode. 'SWE': sweep mode. 'LIST': list mode. 'COMB': combined RF frequency / level sweep mode.
        """   
        if mode == 'CW' or mode == 'FIX' or mode == 'SWE' or mode == 'LIST' or mode == 'COMB':
            self.write(':SOUR:FREQ:MODE {}'.format(mode))
    
    def setRFPowerMode(self, mode):  
        """Selects the operating mode of the instrument to set the output level.

        Args:
            mode (str): 'CW' or 'FIX': Constant level. 'SWE': Sweep mode.
        """
        if mode == 'CW' or mode == 'FIX' or mode == 'SWE':
            self.write(':SOUR:POW:MODE {}'.format(mode))

    def setPowerSweepDwellTime(self, dwell):
        """Sets the dwell time for a level sweep step.

        Args:
            dwell (float): Dwell time in seconds (s).
        """        
        self.write(':SWE:POW:DWEL {}'.format(dwell))
    
    def setPowerSweepShape(self, shape):
        """Determines the waveform shape for a power level sweep sequence.

        Args:
            shape (str): 'SAWT': Sawtooth. 'TRI': Triangle.
        """        
        if shape == 'SAWT' or shape == 'TRI':
            self.write(':SWE:POW:SHAP {}'.format(shape))
    
    def setPowerSweepStart(self, start):
        """Sets the RF start level in sweep mode.

        Args:
            start (float): Power level in dBm.
        """    
        self.write(':SOUR:POW:STAR {}'.format(start))
    
    def setPowerSweepStop(self, stop):
        """Sets the RF stop level in sweep mode.

        Args:
            start (float): Power level in dBm.
        """ 
        self.write(':SOUR:POW:STOP {}'.format(stop))

    def setPowerSweepPoints(self, points):
        """Sets the number of steps within the RF level sweep range.

        Args:
            points (int): Number of steps.
        """        
        self.write(':SWE:POW:POIN {}'.format(points))
    
    def setPowerSweepStepLog(self, step):
        """Sets a logarithmically determined step size for the RF level sweep. The level is increased by a logarithmically calculated fraction of the current level.

        Args:
            step (float): Step size in dB.
        """        
        self.write(':SOUR:SWE:POW:STEP:LOG {}'.format(step))
    
    def defineFrequencyPowerList(self, filename, frequency, power, dwell):
        """Write the frequency and level values in the selected list file. Existing data is overwritten.

        Args:
            filename (str): Name of the list file.
            frequency (list[float]): List of frequencies in Hertz (Hz).
            power (list[float]): List of power levels in dBm.
            dwell (float): Global list dwell time in seconds (s).
        """ 
        # Clip/limit output power
        if self.maxOutputPower is not None and self.minOutputPower is not None:
            power = np.clip(np.array(power), self.minOutputPower, self.maxOutputPower).tolist()
        # Generate sweep list
        freqs = ', '.join([str(f) for f in frequency])
        pows = ', '.join([str(p) for p in power])
        self.write('SOUR:LIST:SEL "/var/user/{}.lsw"'.format(filename))
        self.write(':SOUR:LIST:FREQ {}'.format(freqs))
        self.write(':SOUR:LIST:POW {}'.format(pows))
        self.write(':SOUR:LIST:DWEL {}'.format(dwell))