# RS FSUP
# Andre Schneider <andre.schneider@student.kit.edu> 2014
# modified: JB <jochen.braumueller@kit.edu> 11/2016
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
from qkit import visa
import types
import logging
from time import sleep
import numpy

class RS_FSUP(Instrument):
    '''
    This is the python driver for the Rhode&Schwarz FSUP Signal Source Analyzer.
    The command set is not complete.

    Usage:
    Initialise with
    <name> = instruments.create('<name>', address='<GPIB address>', reset=<bool>)
    
    '''

    def __init__(self, name, address, channel_index = 1):
        '''
        Initializes 

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
        '''
        
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address)

        # Implement parameters
        self.add_parameter('centerfreq', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=26.5e9,
            tags=['sweep'])

        self.add_parameter('nop', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=155, maxval=30001,
            tags=['sweep'])
        self.add_parameter('freqspan', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,tags=['sweep'])                    

        self.add_parameter('powerunit', type=types.StringType,
            flags=Instrument.FLAG_GETSET,tags=['sweep'])

        self.add_parameter('startfreq', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,tags=['sweep']) 

        self.add_parameter('stopfreq', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,tags=['sweep']) 

        self.add_parameter('sweeptime', type=types.FloatType,
            flags=Instrument.FLAG_GET,tags=['sweep'])

        self.add_parameter('resolutionBW', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,tags=['sweep'])

        self.add_parameter('videoBW', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,tags=['sweep'])        
            
        # Implement functions
        self.add_function('set_continuous_sweep_mode')
        #self.add_function('set_freq_center')
        #self.add_function('set_freq_span')
        self.add_function('set_marker')
        self.add_function('set_powerunit')
        self.add_function('get_marker_level')
        #self.add_function('avg_clear')
        #self.add_function('avg_status')
        
        self.get_all()
    
    def get_all(self):        
        self.get_marker_level(1)
        
        #self.get_zerospan()
    
    def do_set_resolutionBW(self, BW):
        '''
        sets the resolution bandwidth
        '''
        self._visainstrument.write('band %e'%(BW))

    def do_get_resolutionBW(self):
        '''
        gets the resolution bandwidth
        '''
        return float(self._visainstrument.ask('band?'))

    def do_set_videoBW(self, BW):
        '''
        sets the video bandwidth
        '''
        self._visainstrument.write('band:vid %e'%(BW))

    def do_get_videoBW(self):
        '''
        gets the video bandwidth
        '''
        return float(self._visainstrument.ask('band:vid?'))

    def do_set_sweeptime(self, sweeptime):
        '''
        sets the sweeptime
        sweeptime in seconds (e.g. 3s) or milliseconds (e.g. 50ms)
        '''
        return float(self._visainstrument.write('swe:time %s'%sweeptime))
        
    def do_get_sweeptime(self):
        '''
        gets the sweeptime
        '''
        return float(self._visainstrument.ask('swe:time?'))
    
    def do_set_centerfreq(self, centerfreq):
        '''
        sets the center frequency
        '''
        self._visainstrument.write('freq:cent %e'%(centerfreq))

    def do_get_centerfreq(self):
        '''
        gets the center frequency
        '''
        return float(self._visainstrument.ask('freq:cent?'))

    def do_set_freqspan(self, freqspan):
        '''
        sets the frequency span
        '''
        self._visainstrument.write('freq:span %e'%(freqspan))
    
    def do_get_freqspan(self):
        '''
        get the frequency span
        '''
        return float(self._visainstrument.ask('freq:span?'))

    def do_set_startfreq(self, freq):
        self._visainstrument.write('freq:start %e'%(freq))

    def do_get_startfreq(self):
        return float(self._visainstrument.ask('freq:start?'))

    def do_set_stopfreq(self, freq):
        self._visainstrument.write('freq:stop %e'%(freq))

    def do_get_stopfreq(self):
        return float(self._visainstrument.ask('freq:stop?'))        
        
    def do_set_nop(self, nop):
        self._visainstrument.write('swe:poin %i'%(nop))

    def do_get_nop(self):
        return int(self._visainstrument.ask('swe:poin?'))   
        
    def do_set_powerunit(self,unit):
        '''
        sets the unit for powers
        provide unit as a string! ("DBm")
        '''
        self._visainstrument.write('unit:pow %s'%(unit))
        
    def do_get_powerunit(self):
        '''
        gets the power unit for powers
        '''
        return self._visainstrument.ask('unit:pow')
    
    def set_marker(self,marker,frequency):
        '''
        sets marker number marker to frequency
        
        '''
        self._visainstrument.write('calc:mark%i:x %e'%(marker, frequency))
        self.enable_marker(marker)
        
    def get_marker(self,marker):
        '''
        gets frequency of marker
        
        '''
        return float(self._visainstrument.ask('calc:mark%i:x?'%(marker)))
    
    def get_marker_level(self,marker):
        '''
        gets power level of indicated marker
        
        '''
        return float(self._visainstrument.ask('calc:mark%i:y?'%(marker)))
        
    def set_continuous_sweep_mode(self,value):
        '''
        value='ON' Continuous sweep
        value='OFF' Single sweep
        '''
        self._visainstrument.write('INIT:CONT %s'%(value))  
    
    def get_frequencies(self):
        '''
        returns an array with the frequencies of the points returned by get_trace()
        ideally suitable as x-axis for plots
        '''
        return linspace(self.get_startfreq(),self.get_stopfreq(),self.get_nop())
    
    def enable_marker(self,marker,state='ON'):
        '''
        ON or OFF
        '''
        self._visainstrument.write('CALC:MARK%i %s'%(marker,state)) 
    
    def sweep(self):
        '''
        perform a sweep and wait for it to finish
        '''
        self._visainstrument.write('INIT; *WAI')    
    
    def get_trace(self, tracenumber=1):
        return self._visainstrument.query_ascii_values('trac:data? trace%i'%tracenumber)
        
    def get_tracedata(self,tracenumber=1):
        amp = self._visainstrument.query_ascii_values('trac:data? trace%i'%tracenumber)
        return [amp,numpy.zeros_like(amp)]    
    
    def get_frequencies(self):
        '''
        returns an array with the frequencies of the points returned by get_trace()
        ideally suitable as x-axis for plots
        '''
        return numpy.linspace(self.get_startfreq(),self.get_stopfreq(),self.get_nop())
    
    def write(self, command):
        self._visainstrument.write(command) 
    
    def ask(self,command):
        return self._visainstrument.ask(command)    
    
