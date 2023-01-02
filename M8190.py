# Copyright (c) 2022-2023 Taner Esat <t.esat@fz-juelich.de>

import pyvisa


class M8190A():
    def __init__(self, VisaResourceString):
        self.rm = pyvisa.ResourceManager()
        self.VisaResourceString = VisaResourceString
        self.connected = False

    def connect(self):
        """Connects to the Keysight Arbitrary Waveform Generator (AWG) M8190A.
        """        
        try:
            self.inst = self.rm.open_resource(self.VisaResourceString)
            self.inst.write_termination = '\n'
            self.inst.read_termination = '\n'
            self.inst.timeout = 5000
            self.connected = True
        except pyvisa.VisaIOError:
            resp = 'Could not connect to Keysight M8190A.\nPlease check the device settings.'
            print(resp)
    
    def disconnect(self):
        """Disconnects from AWG.
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
    
    def setCoupling(self, decouple=True):
        """Switch coupling between channels on/off.

        Args:
            decouple (bool, optional): True: Channels decoupled. False: Channels coupled. Defaults to True.
        """        
        if decouple:
            self.write(':INST:COUP:STAT 0')
        else:
            self.write(':INST:COUP:STAT 1')

    def setOutputRoute(self, channel, output):
        """Select the output path for channel.

        Args:
            channel (int): Channel number.
            output (str): 
            'DAC': Direct DAC output. 
            'DC': Amplified differential output.
            'AC': Single ended AC coupled output with up to 10 dBm output level
        """        
        if output == 'DC':
            self.write(':OUTP{}:ROUT DC'.format(channel))
        if output == 'AC':
            self.write(':OUTP{}:ROUT AC'.format(channel))
        if output == 'DAC':
            self.write(':OUTP{}:ROUT DAC'.format(channel))

    def setFormat(self, channel, format):
        """Set the DAC format mode for channel.

        Args:
            channel (int): Channel number.
            format (str): Available DAC formats: 'NRZ', 'DNRZ', 'DOUB', 'RZ'. For details see manual.
        """        
        err, resp = self.query(':OUTP:ROUT?')
        if err == False:
            route = resp
            if format == 'RZ':
                self.write(':{}{}:FORM RZ'.format(route, channel))
            if format == 'NRZ':
                self.write(':{}{}:FORM NRZ'.format(route, channel))
            if format == 'DNRZ':
                self.write(':{}{}:FORM DNRZ'.format(route, channel))
            if format == 'DOUB':
                self.write(':{}{}:FORM DOUB'.format(route, channel))
    
    def setAmplitude(self, channel, amplitude):
        """Set the output amplitude for channel.

        Args:
            channel (int): Channel number.
            amplitude (float): Amplitude for selected output path in Volts (V).
        """        
        err, resp = self.query(':OUTP:ROUT?')
        if err == False:
            route = resp
            self.write(':{}{}:VOLT:AMPL {}'.format(route, channel, amplitude))
    
    def setSamplingFrequency(self, frequency):
        """Set sampling frequency of AWG.

        Args:
            frequency (float): Sampling frequency in Hertz (Hz).
        """        
        self.write(':FREQ:RAST {}'.format(frequency))

    def playChannel(self, channel):
        """Start signal generation on channel.

        Args:
            channel (int): Channel number.
        """        
        self.write(':INIT:IMM{}'.format(channel))
    
    def stopChannel(self, channel):
        """Stops signal generation on channel. If channels are coupled, both channels are stopped.

        Args:
            channel (int): Channel number.
        """        
        self.write(':ABOR{}'.format(channel))
    
    def switchOutputOn(self, channel):
        """Switch output on for channel.

        Args:
            channel (int): Channel number.
        """        
        self.write(':OUTP{} ON'.format(channel))
    
    def switchOutputOff(self, channel):
        """Switch output off for channel.

        Args:
            channel (int): Channel number.
        """  
        self.write(':OUTP{} OFF'.format(channel))
    
    def setTriggerLevel(self, level):
        """Set the trigger input threshold level.

        Args:
            level (float): Threshold level voltage in Volts (V).
        """        
        self.write(':ARM:TRIG:LEV {}'.format(level))
    
    def setTriggerSource(self, source='EXT'):
        """Set or query the source for the trigger function.

        Args:
            source (str, optional): 'EXT': external trigger input. 'INT': internal trigger generator. Defaults to 'EXT'.
        """        
        if source == 'INT':
            self.write(':ARM:TRIG:SOUR INT')
        if source == 'EXT':
            self.write(':ARM:TRIG:SOUR EXT')

    def setTriggerPolarity(self, polarity='POS'):
        """Set the trigger input slope.

        Args:
            polarity (str, optional): 'POS': rising edge. 'NEG': falling edge. 'EITH': both. Defaults to 'POS'.
        """        
        if polarity == 'POS':
            self.write(':ARM:TRIG:SLOP POS')
        if polarity == 'NEG':
            self.write(':ARM:TRIG:SLOP NEG')
        if polarity == 'EITH':
            self.write(':ARM:TRIG:SLOP EITH')
    
    def setTriggerImpedance(self, impedance='LOW'):
        """Set the trigger input impedance.

        Args:
            impedance (str, optional): 'LOW': low impedance. 'HIGH': high impedance. Defaults to 'LOW'.
        """        
        if impedance == 'HIGH':
            self.write(':ARM:TRIG:IMP HIGH')
        if impedance == 'LOW':
            self.write(':ARM:TRIG:IMP LOW')
    
    def setMarkerAmplitude(self, channel, amplitude, marker='SAMP'):
        """Set the output amplitude for sync/sample marker for channel.

        Args:
            channel (int): Channel number.
            amplitude (float): Amplitude of sync/sample marker in Volts (V).
            marker (str, optional): 'SAMP': sample marker. 'SYNC': sync marker. Defaults to 'SAMP'.
        """        
        if marker == 'SAMP' or marker == 'SYNC':
            self.write(':SOUR:MARK{}:{}:VOLT:AMPL {}'.format(channel, marker, amplitude))
    
    def setMarkerOffset(self, channel, amplitude, marker='SAMP'):
        """Set the output offset for sync/sample marker for channel.

        Args:
            channel (int): Channel number.
            amplitude (float): Offset of sync/sample marker in Volts (V).
            marker (str, optional): 'SAMP': sample marker. 'SYNC': sync marker. Defaults to 'SAMP'.
        """   
        if marker == 'SAMP' or marker == 'SYNC':
            self.write(':SOUR:MARK{}:{}:VOLT:OFFS {}'.format(channel, marker, amplitude))
    
    def setSequencingMode(self, channel, mode='ARB'):
        """Set the type of waveform that will be generated for channel.

        Args:
            channel (int): Channel number.
            mode (str, optional): 'ARB': arbitrary waveform segment. 'STS': sequence. 'STSC': scenario. Defaults to 'ARB'.
        """        
        if mode == 'ARB' or mode == 'STS' or mode == 'STSC':
            self.write(':FUNC{}:MODE {}'.format(channel, mode))
    
    def setTriggerMode(self, channel, mode):
        """Set the trigger mode for channel.

        Args:
            channel (int): Channel number.
            mode (str): 'CONT': continuous. 'TRIG': triggered. 'GATE': gated.
        """        
        if mode == 'CONT':
            self.write(':INIT:CONT{} 1'.format(channel))
        if mode == 'TRIG':
            self.write(':INIT:GATE{} 0'.format(channel))
            self.write(':INIT:CONT{} 0'.format(channel))
        if mode == 'GATE':
            self.write(':INIT:GATE{} 1'.format(channel))
            self.write(':INIT:CONT{} 0'.format(channel))

    def loadSegmentFromBin(self, channel, segmentId, file):
        """Import segment data from a binary file for channel.

        Args:
            channel (int): Channel number.
            segmentId (int): Number of the segment, into which the data will be written.
            file (str): Path to file.
        """        
        self.write(':TRAC{}:IQIM {}, "{}", BIN, IONLY, ON, ALEN'.format(channel, segmentId, file))

    def defineSequence(self, channel, sequenceTable, mode):
        """Defines a new sequence made of arbitrary waveforms.

        Args:
            channel (int): Channel number.
            sequenceTable (list): List of dictionaries. Dictionary must contain the following keys: 'entryNumber': sequence table entry in the sequence. 'segmentID': id of the segment. 'loop': number of segment loop iterations.
            mode (str): 'COND': Advancement mode - Conditional
        """        
        err, resp = self.query(':SEQ{}:DEF:NEW? {}'.format(channel, len(sequenceTable)))
        sequenceId = int(resp)
        for row in sequenceTable:
            self.write(':SEQ{}:DATA {},{},{},{},0,1,0,#hFFFFFFFF'.format(channel, sequenceId, row['entryNumber'], row['segmentID'], row['loop']))
        if mode == 'COND':
            self.write(':SEQ{}:ADV {}, COND'.format(channel, sequenceId, mode))

    def deleteSequences(self, channel, sequenceId=None):
        """Delete (all) sequence(s) for channel.

        Args:
            channel (int): Channel number.
            sequenceId (int, optional): Number of the sequence which will be deleted. None means all sequences will be deleted. Defaults to None.
        """        
        if sequenceId == None:
            self.write(':SEQ{}:DEL:ALL'.format(channel))
        else:
            self.write(':SEQ{}:DEL {}'.format(channel, sequenceId))