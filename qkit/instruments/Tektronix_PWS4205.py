# Tektronix PWS4205 class, to perform the communication between the Wrapper and the device
# Sebastian Probst, sebastian.probst@kit.edu 2013
#
# based on the work on the Keithley_2636A driver by
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
# Hannes Rotzinger, hannes.rotzinger@kit.edu 2010
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from instrument import Instrument
import visa
import types
import time
import logging
import numpy

class Tektronix_PWS4205(Instrument):
    '''
    This is the driver for the Tektronix_PWS4205 Power Supply

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Tektronix_PWS4205', address='<USB address>, reset=<bool>')
    USB address e.g. USB0::0x0699::0x0390::C010427::INSTR
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Tektronix_PWS4205, and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : GPIB or USB address
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Tektronix_PWS4205')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        
        self.add_parameter('voltage',
            flags=Instrument.FLAG_GETSET, units='V', minval=-200, maxval=200, type=types.FloatType)
            
        self.add_parameter('setvoltage',
            flags=Instrument.FLAG_GET, units='V', minval=-200, maxval=200, type=types.FloatType)
 
        self.add_parameter('current',
            flags=Instrument.FLAG_GETSET, units='A', minval=-10, maxval=10, type=types.FloatType)
            
        self.add_parameter('setcurrent',
            flags=Instrument.FLAG_GET, units='A', minval=-10, maxval=10, type=types.FloatType)

        self.add_parameter('status',
            flags=Instrument.FLAG_GETSET, type=types.StringType)

        self.add_function('reset')
        self.add_function('on')
        self.add_function('off')
 
#        self.add_function('exec_tsl_script')
#        self.add_function('exec_tsl_script_with_return')
#        self.add_function('get_tsl_script_return')
        
        #self.add_function ('get_all')

        #self._visainstrument.write('beeper.beep(0.5,1000)')
        if (reset):
            self.reset()
        else:
            self.get_all()

    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : resetting instrument')
        self._visainstrument.write("*RST")
        self.get_all()

    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : get all')
        #self.do_get_voltageA()
        #self.get_voltageB()
        #self.get_currentA()
        #self.get_currentB()
    
#    def exec_tsl_script(self,script):
#        '''
#        Writes the script to the device
#        Input:
#            TSL script (basically lua)
#        Output:
#            None
#        '''
#        logging.debug(__name__ + ' : execute TSL script on device')
#        self._visainstrument.write(script)
        
#    def exec_tsl_script_with_return(self,script):
#        '''
#        Writes the script to the device
#        Input:
#            TSL script (basically lua)
#        Output:
#            None
#        '''
#        logging.debug(__name__ + ' : execute TSL script on device and return data')
#        return self._visainstrument.ask(script).strip()

 
#    def get_tsl_script_return(self):
#        '''
#        Writes the script to the device
#        Input:
#            None
#        Output:
#            data, can be anything
#        '''
#        logging.debug(__name__ + ' : return data from executed TSL script')
#        return self._visainstrument.read().strip()

 
    def do_get_voltage(self):
        '''
        Reads the voltage signal from the instrument

        Input:
            None

        Output:
            volt (float) : Voltage in Volts
        '''
        logging.debug(__name__ + ' : get voltage')
        return float(self._visainstrument.ask('MEAS:VOLT?'))
        
    def do_get_setvoltage(self):
        '''
        Reads the setvoltage signal from the instrument

        Input:
            None

        Output:
            volt (float) : Voltage in Volts
        '''
        logging.debug(__name__ + ' : get setvoltage')
        return float(self._visainstrument.ask('VOLT?'))

    def do_set_voltage(self, volt):
        '''
        Set the Amplitude of the signal

        Input:
            volt (float) : voltage in volt

        Output:
            None
        '''
        logging.debug(__name__ + ' : set voltage to %f' % volt)
        self._visainstrument.write('VOLT %s' % volt)

    def do_get_current(self):
        '''
        Reads the current signal from the instrument

        Input:
            None

        Output:
            current (float) : current in amps
        '''
        logging.debug(__name__ + ' : get current')
        return float(self._visainstrument.ask('MEAS:CURR?'))
        
    def do_get_setcurrent(self):
        '''
        Reads the setcurrent signal from the instrument

        Input:
            None

        Output:
            current (float) : current in amps
        '''
        logging.debug(__name__ + ' : get setcurrent')
        return float(self._visainstrument.ask('CURR?'))

    def do_set_current(self, curr):
        '''
        Set the Amplitude of the signal

        Input:
            curr (float) : current in amps

        Output:
            None
        '''
        logging.debug(__name__ + ' : set current to %f' % curr)
        self._visainstrument.write('CURR %s' % curr)

    def do_get_status(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (string) : 'On' or 'Off'
        '''
        logging.debug(__name__ + ' : get status')
        stat = int(float(self._visainstrument.ask('OUTPUT?')))

        if (stat==1):
          return 'on'
        elif (stat==0):
          return 'off'
        else:
          raise ValueError('Output status not specified : %s' % stat)
        return

    def do_set_status(self, status):
        '''
        Set the output status of the instrument

        Input:
            status (string) : 'On' or 'Off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        if status.upper() in ('ON', 'OFF'):
            status = status.upper()
        else:
            raise ValueError('set_status(): can only set on or off')
            
        if status == 'ON':
            self._visainstrument.write('OUTPUT 1')
        else:
            self._visainstrument.write('OUTPUT 0')


    # shortcuts
    def off(self):
        '''
        Set status to 'off'

        Input:
            None

        Output:
            None
        '''
        self.set_status('off')

    def on(self):
        '''
        Set status to 'on'

        Input:
            None

        Output:
            None
        '''
        self.set_status('on')