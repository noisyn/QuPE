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
Example code for a pump-probe measurement:
https://github.com/noisyn/QuPE/blob/a39a37582327a3f789fb0bd83a7e4308b8a8ec05/example_measurePP.py

Example code for a RF measurements:
https://github.com/noisyn/QuPE/blob/a39a37582327a3f789fb0bd83a7e4308b8a8ec05/example_measureRF.py

## License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.