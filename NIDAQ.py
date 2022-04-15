# Copyright (c) 2022 Taner Esat <t.esat@fz-juelich.de>

import nidaqmx
import numpy as np
import time

class NIDAQ():
    def __init__(self, device, samplingRate=1e3):
        self.device = device
        self.setSamplingRate(samplingRate)

    def setSamplingRate(self, samplingRate):
        self.samplingRate = samplingRate
    
    def getSamplingRate(self):
        return self.samplingRate
    
    def readAnalog(self, channel, duration=None):
        with nidaqmx.Task() as task:
            if type(channel) is str:
                task.ai_channels.add_ai_voltage_chan('{}/{}'.format(self.device, channel))
            if type(channel) is list:
                for ch in channel:
                    task.ai_channels.add_ai_voltage_chan('{}/{}'.format(self.device, ch))
            task.timing.cfg_samp_clk_timing(self.samplingRate, samps_per_chan=1)
            if duration == None:
                data = task.read()
            else:
                data = np.zeros(int(self.samplingRate * duration))
                task.timing.cfg_samp_clk_timing(self.samplingRate, samps_per_chan=len(data))
                data = task.read(len(data), duration)
        return np.array(data)
    
    def writeAnalog(self, channel, data):
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan('{}/{}'.format(self.device, channel))
            if len(data) > 1:
                for i in range(len(data)):
                    task.write(data[i], auto_start=True)
                    time.sleep(1/self.getSamplingRate())
            else:
                task.write(data, auto_start=True)