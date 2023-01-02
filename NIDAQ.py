# Copyright (c) 2022-2023 Taner Esat <t.esat@fz-juelich.de>

import time

import nidaqmx
import numpy as np


class NIDAQ():
    def __init__(self, device, samplingRate=1e3):
        self.device = device
        self.setSamplingRate(samplingRate)

    def setSamplingRate(self, samplingRate):
        """Sets the sampling rate of the DAQ box.

        Args:
            samplingRate (float): Sampling rate in samples per channel per second.
        """        
        self.samplingRate = samplingRate
    
    def getSamplingRate(self):
        """Returns the sampling rate of the DAQ box.

        Returns:
            float: Sampling rate in samples per channel per second.
        """        
        return self.samplingRate
    
    def readAnalog(self, channel, duration=None):
        """Reads sample(s) from channel(s).

        Args:
            channel (str, list): Name of channel or list of channel names.
            duration (float, optional): Measurement time in seconds. Defaults to None: Single sample is measured.

        Returns:
            ndarray: Samples requested in the form of a scalar, a list, or a list of lists.
        """
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
        """Writes sample(s) to a channel.

        Args:
            channel (str): Name of channel.
            data (float, list): Single sample or a list of samples.
        """
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan('{}/{}'.format(self.device, channel))
            if len(data) > 1:
                for i in range(len(data)):
                    task.write(data[i], auto_start=True)
                    time.sleep(1/self.getSamplingRate())
            else:
                task.write(data, auto_start=True)