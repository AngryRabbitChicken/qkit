# Agilent_VNA_E5071C driver, P. Macha, modified by M. Weides July 2013, J. Braumueller 2015
# Adapted to Keysight VNA by A. Schneider and L. Gurenhaupt 2016
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
import logging
from time import sleep
import numpy
import math

class Keysight_VNA_E5071C(Instrument):
    '''
    This is the python driver for the Anritsu MS4642A Vector Network Analyzer

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
        self._zerospan = False
        self._freqpoints = 0
        self._ci = channel_index 
        self._pi = 2 # port_index, similar to self._ci
        self._start = 0
        self._stop = 0
        self._nop = 0

        # Implement parameters
        self.add_parameter('nop', type=types.IntType,
            flags=Instrument.FLAG_GETSET,
            minval=2, maxval=1601,
            tags=['sweep'])
            
        self.add_parameter('bandwidth', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=1e9,
            units='Hz', tags=['sweep']) 

        self.add_parameter('averages', type=types.IntType,
            flags=Instrument.FLAG_GETSET,
            minval=1, maxval=1024, tags=['sweep'])                    

        self.add_parameter('Average', type=types.BooleanType,
            flags=Instrument.FLAG_GETSET)   
                    
        self.add_parameter('centerfreq', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=20e9,
            units='Hz', tags=['sweep'])
            
        self.add_parameter('startfreq', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=20e9,
            units='Hz', tags=['sweep'])            
            
        self.add_parameter('stopfreq', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=20e9,
            units='Hz', tags=['sweep'])                        
            
        self.add_parameter('span', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=20e9,
            units='Hz', tags=['sweep'])        
            
        self.add_parameter('power', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=-85, maxval=10,
            units='dBm', tags=['sweep'])

        self.add_parameter('zerospan', type=types.BooleanType,
            flags=Instrument.FLAG_GETSET)
            
        self.add_parameter('channel_index', type=types.IntType,
            flags=Instrument.FLAG_GETSET)

        self.add_parameter('sweeptime', type=types.FloatType,   #added by MW
            flags=Instrument.FLAG_GET,
            minval=0, maxval=1e3,
            units='s', tags=['sweep'])
            
        self.add_parameter('sweeptime_averages', type=types.FloatType,   #JB
            flags=Instrument.FLAG_GET,
            minval=0, maxval=1e3,
            units='s', tags=['sweep'])
    
        self.add_parameter('edel', type=types.FloatType, # legacy name for parameter. This corresponds to the VNA's port extension values.
            flags=Instrument.FLAG_GETSET, 
            minval=-10, maxval=10,
            units='s', tags=['sweep'],
            channels=(1, self._pi), channel_prefix = 'port%d_') # the channel option for qtlab's Instument class is used here to easily address the two VNA ports
  
        self.add_parameter('edel_status', type=types.BooleanType, # legacy name for parameter. This corresponds to the VNA's port extension values.
            flags=Instrument.FLAG_GETSET)
                    
                    
        #Triggering Stuff
        self.add_parameter('trigger_source', type=types.StringType,
            flags=Instrument.FLAG_GETSET)
        
        # Implement functions
        self.add_function('get_freqpoints')
        self.add_function('get_tracedata')
        self.add_function('init')
        self.add_function('avg_clear')
        self.add_function('avg_status')
        self.add_function('def_trig')
        self.add_function('get_hold')
        self.add_function('hold')
        self.add_function('get_sweeptime')
        self.add_function('get_sweeptime_averages')
        self.add_function('pre_measurement')
        self.add_function('start_measurement')
        self.add_function('ready')
        self.add_function('post_measurement')

        self.get_all()
    
    def get_all(self):        
        self.get_nop()
        self.get_power()
        self.get_centerfreq()
        self.get_startfreq()
        self.get_stopfreq()
        self.get_span()
        self.get_bandwidth()
        self.get_trigger_source()
        self.get_Average()
        self.get_averages()
        self.get_freqpoints()   
        self.get_channel_index()
        self.get_zerospan()
        self.get_sweeptime()
        self.get_sweeptime_averages()
        self.get_edel_status()
        for port in range(self._pi):
            self.get('port%d_edel' % (port+1))
        
    ###
    #Communication with device
    ###
    
    def init(self):
        if self._zerospan:
          self._visainstrument.write('INIT1;*wai')
        else:
          if self.get_Average():
            for i in range(self.get_averages()):            
              self._visainstrument.write('INIT1;*wai')
          else:
              self._visainstrument.write('INIT1;*wai')
              
    def hold(self, status):     # added MW July 13
        self._visainstrument.write(":TRIG:SOUR INT")
        if status:
            self._visainstrument.write(':INIT%i:CONT OFF'%(self._ci))
            #print 'continuous off'
        else:
            self._visainstrument.write(':INIT%i:CONT ON'%(self._ci))
            #print 'continuous on'

    def get_hold(self):     # added MW July 13
        #self._visainstrument.read(':INIT%i:CONT?'%(self._ci))
        self._hold=self._visainstrument.ask(':INIT%i:CONT?'%(self._ci))
        return self._hold     

    def def_trig(self):
        self._visainstrument.write(':TRIG:AVER ON')
        self._visainstrument.write(':TRIG:SOUR bus')
        
    def avg_clear(self):
        #self._visainstrument.write(':TRIG:SING')
        #self._visainstrument.write(':SENSe%i:AVERage:CLEar'%(self._ci))
        self._visainstrument.write(':SENS%i:AVER:CLE' %(self._ci))

    def avg_status(self):
        return 0 == (int(self._visainstrument.ask('STAT:OPER:COND?')) & (1<<4))
        #return int(self._visainstrument.ask(':SENS%i:AVER:COUNT?' %(self._ci)))    
        
    def get_tracedata(self, format = 'AmpPha', single=False, averages=1.):
        
        
        '''
        Get the data of the current trace

        Input:
            format (string) : 'AmpPha': Amp in dB and Phase, 'RealImag',

        Output:
            'AmpPha':_ Amplitude and Phase
        '''
        
        
        if single==True:        #added MW July. 
            #print 'single shot readout'
            self._visainstrument.write('TRIG:SOUR INT') #added MW July 2013. start single sweep.
            self._visainstrument.write('INIT%i:CONT ON'%(self._ci)) #added MW July 2013. start single sweep.
            self.hold(True)
            sleep(float(self._visainstrument.ask('SENS1:SWE:TIME?'))) 
        
        sleep(0.1) # required to avoid timing issues    MW August 2013   ???
            
        #self._visainstrument.write(':FORMAT REALform; FORMat:BORDer SWAP;')
        #data = self._visainstrument.ask_for_values( "CALCulate:DATA? SDATA",format = visa.single)
        #data = self._visainstrument.ask_for_values(':FORMAT REAL,32;*CLS;CALC1:DATA:NSW? SDAT,1;*OPC',format=1)      
        #data = self._visainstrument.ask_for_values('FORM:DATA REAL; FORM:BORD SWAPPED; CALC%i:SEL:DATA:SDAT?'%(self._ci), format = visa.double)  
        self._visainstrument.write('FORM:DATA REAL')
        self._visainstrument.write('FORM:BORD SWAPPED') #SWAPPED
        #data = self._visainstrument.ask_for_values('CALC%d:SEL:DATA:SDAT?'%(self._ci), format = visa.double)              
        data = self._visainstrument.ask_for_values('CALC%i:SEL:DATA:SDAT?'%(self._ci), format = 3)
        data_size = numpy.size(data)
        datareal = numpy.array(data[0:data_size:2])
        dataimag = numpy.array(data[1:data_size:2])
          
        if format == 'RealImag':
          if self._zerospan:
            return numpy.mean(datareal), numpy.mean(dataimag)
          else:
            return datareal, dataimag
        elif format == 'AmpPha':
          if self._zerospan:
            datareal = numpy.mean(datareal)
            dataimag = numpy.mean(dataimag)
            dataamp = numpy.sqrt(datareal*datareal+dataimag*dataimag)
            for i in arange(len(datareal)):    #added MW July 2013
                if datareal[i]>=0 and dataimag[i] >=0:   #1. quadrant
                    datapha.append(arctan(dataimag[i]/datareal[i]))
                elif  datareal[i] <0 and dataimag[i] >=0:  #2. quadrant
                    data.pha.append(arctan(dataimag[i]/datareal[i])+ pi)
                elif  datareal[i] <0 and dataimag[i] <0:  #3. quadrant
                    datapha.append(arctan(dataimag[i]/datareal[i])- pi)
                elif  datareal[i] >=0 and dataimag[i]<0:   #4. quadrant
                    datapha.append(arctan(dataimag[i]/datareal[i]))   

            return dataamp, datapha
          else:
            dataamp = numpy.sqrt(datareal*datareal+dataimag*dataimag)
            datapha = numpy.arctan2(dataimag,datareal)
            return dataamp, datapha
        else:
          raise ValueError('get_tracedata(): Format must be AmpPha or RealImag') 
      
    def get_freqpoints(self, query = False):      
      if query == True:        
        self._freqpoints = self._visainstrument.ask_for_values('FORM:DATA REAL; FORM:BORD SWAPPED; :SENS%i:FREQ:DATA?'%(self._ci), format = visa.double)
      
        #self._freqpoints = numpy.array(self._visainstrument.ask_for_values('SENS%i:FREQ:DATA:SDAT?'%self._ci,format=1)) / 1e9
        #self._freqpoints = numpy.array(self._visainstrument.ask_for_values(':FORMAT REAL,32;*CLS;CALC1:DATA:STIM?;*OPC',format=1)) / 1e9
      else:
        self._freqpoints = numpy.linspace(self._start,self._stop,self._nop)
      return self._freqpoints

    ###
    # SET and GET functions
    ###
    
    def do_set_nop(self, nop):
        '''
        Set Number of Points (nop) for sweep

        Input:
            nop (int) : Number of Points

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting Number of Points to %s ' % (nop))
        if self._zerospan:
          print 'in zerospan mode, nop is 1'
        else:
          self._visainstrument.write(':SENS%i:SWE:POIN %i' %(self._ci,nop))
          self._nop = nop
          self.get_freqpoints() #Update List of frequency points  
        
    def do_get_nop(self):
        '''
        Get Number of Points (nop) for sweep

        Input:
            None
        Output:
            nop (int)
        '''
        logging.debug(__name__ + ' : getting Number of Points')
        if self._zerospan:
          return 1
        else:
          self._nop = int(self._visainstrument.ask(':SENS%i:SWE:POIN?' %(self._ci)))    
        return self._nop 
    
    def do_set_Average(self, status):
        '''
        Set status of Average

        Input:
            status (boolean)

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting Average to "%s"' % (status))
        if status:
            status = 'ON'
            self._visainstrument.write('SENS%i:AVER:STAT %s' % (self._ci,status))
        elif status == False:
            status = 'OFF'
            self._visainstrument.write('SENS%i:AVER:STAT %s' % (self._ci,status))
        else:
            raise ValueError('set_Average(): can only set True or False')               
    def do_get_Average(self):
        '''
        Get status of Average

        Input:
            None

        Output:
            Status of Averaging (boolean)
        '''
        logging.debug(__name__ + ' : getting average status')
        return bool(int(self._visainstrument.ask('SENS%i:AVER:STAT?' %(self._ci))))
                    
    def do_set_averages(self, av):
        '''
        Set number of averages

        Input:
            av (int) : Number of averages

        Output:
            None
        '''
        if self._zerospan == False:
            logging.debug(__name__ + ' : setting Number of averages to %i ' % (av))
            self._visainstrument.write('SENS%i:AVER:COUN %i' % (self._ci,av))
        else:
            self._visainstrument.write('SWE:POIN %.1f' % (self._ci,av))
            
    def do_get_averages(self):
        '''
        Get number of averages

        Input:
            None
        Output:
            number of averages
        '''
        logging.debug(__name__ + ' : getting Number of Averages')
        if self._zerospan:
          return int(self._visainstrument.ask('SWE%i:POIN?' % self._ci))
        else:
          return int(self._visainstrument.ask('SENS%i:AVER:COUN?' % self._ci))
                
    def do_set_power(self,pow):
        '''
        Set probe power

        Input:
            pow (float) : Power in dBm

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting power to %s dBm' % pow)
        self._visainstrument.write('SOUR%i:POW:PORT1:LEV:IMM:AMPL %.1f' % (self._ci,pow))    
    def do_get_power(self):
        '''
        Get probe power

        Input:
            None

        Output:
            pow (float) : Power in dBm
        '''
        logging.debug(__name__ + ' : getting power')
        return float(self._visainstrument.ask('SOUR%i:POW:PORT1:LEV:IMM:AMPL?' % (self._ci)))
                
    def do_set_centerfreq(self,cf):
        '''
        Set the center frequency

        Input:
            cf (float) :Center Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting center frequency to %s' % cf)
        self._visainstrument.write('SENS%i:FREQ:CENT %f' % (self._ci,cf))
        self.get_startfreq();
        self.get_stopfreq();
        self.get_span();
    def do_get_centerfreq(self):
        '''
        Get the center frequency

        Input:
            None

        Output:
            cf (float) :Center Frequency in Hz
        '''
        logging.debug(__name__ + ' : getting center frequency')
        return  float(self._visainstrument.ask('SENS%i:FREQ:CENT?'%(self._ci)))
        
    def do_set_span(self,span):
        '''
        Set Span

        Input:
            span (float) : Span in KHz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting span to %s Hz' % span)
        self._visainstrument.write('SENS%i:FREQ:SPAN %i' % (self._ci,span))   
        self.get_startfreq();
        self.get_stopfreq();
        self.get_centerfreq();   
        
    def do_get_span(self):
        '''
        Get Span
        
        Input:
            None

        Output:
            span (float) : Span in Hz
        '''
        #logging.debug(__name__ + ' : getting center frequency')
        span = self._visainstrument.ask('SENS%i:FREQ:SPAN?' % (self._ci) ) #float( self.ask('SENS1:FREQ:SPAN?'))
        return span

    def do_get_sweeptime_averages(self):###JB
        '''
        Get sweeptime
        
        Input:
            None

        Output:
            sweep time (float) times number of averages: sec
        '''
        return self.get_sweeptime() * self.get_averages()
        
    def do_get_sweeptime(self):  #added MW July 2013
        '''
        Get sweeptime
        
        Input:
            None

        Output:
            sweep time (float) : sec
        '''
        logging.debug(__name__ + ' : getting sweep time')
        self._sweep=float(self._visainstrument.ask('SENS1:SWE:TIME?'))
        return self._sweep


    def do_set_edel(self, val,channel):  # MP 04/2017

        '''
        Set electrical delay

        '''
        logging.debug(__name__ + ' : setting port %s extension to %s sec' % (channel, val))
        self._visainstrument.write('SENS1:CORR:EXT:PORT%i:TIME %.12f' % (channel, val))
            
    
    def do_get_edel(self, channel):   # MP 04/2017

        '''
        Get electrical delay

        '''
        logging.debug(__name__ + ' : getting port %s extension' % channel)
        self._edel = float(self._visainstrument.ask('SENS1:CORR:EXT:PORT%i:TIME?'% channel))
        return  self._edel   
        
    def do_set_edel_status(self, status):   # MP 04/2017

        '''
        Set electrical delay

        '''
        logging.debug(__name__ + ' : setting port extension status to %s' % (status))
        self._visainstrument.write('SENS.CORR.EXT.STAT %i' % (status))
            
    
    def do_get_edel_status(self):   # MP 04/2017

        '''
        Get electrical delay

        '''
        logging.debug(__name__ + ' :  port extension status')
        return  self._visainstrument.ask('SENS:CORR:EXT:STAT?')
        
        
    def do_set_startfreq(self,val):
        '''
        Set Start frequency

        Input:
            span (float) : Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting start freq to %s Hz' % val)
        self._visainstrument.write('SENS%i:FREQ:STAR %f' % (self._ci,val))   
        self._start = val
        self.get_centerfreq();
        self.get_stopfreq();
        self.get_span();
        
    def do_get_startfreq(self):
        '''
        Get Start frequency
        
        Input:
            None

        Output:
            span (float) : Start Frequency in Hz
        '''
        logging.debug(__name__ + ' : getting start frequency')
        self._start = float(self._visainstrument.ask('SENS%i:FREQ:STAR?' % (self._ci)))
        return  self._start

    def do_set_stopfreq(self,val):
        '''
        Set STop frequency

        Input:
            val (float) : Stop Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting stop freq to %s Hz' % val)
        self._visainstrument.write('SENS%i:FREQ:STOP %f' % (self._ci,val))  
        self._stop = val
        self.get_startfreq();
        self.get_centerfreq();
        self.get_span();
    def do_get_stopfreq(self):
        '''
        Get Stop frequency
        
        Input:
            None

        Output:
            val (float) : Start Frequency in Hz
        '''
        logging.debug(__name__ + ' : getting stop frequency')
        self._stop = float(self._visainstrument.ask('SENS%i:FREQ:STOP?' %(self._ci) ))
        return  self._stop

    def do_set_bandwidth(self,band):
        '''
        Set Bandwidth

        Input:
            band (float) : Bandwidth in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting bandwidth to %s Hz' % (band))
        self._visainstrument.write('SENS%i:BWID:RES %i' % (self._ci,band))
    def do_get_bandwidth(self):
        '''
        Get Bandwidth

        Input:
            None

        Output:
            band (float) : Bandwidth in Hz
        '''
        logging.debug(__name__ + ' : getting bandwidth')
        # getting value from instrument
        return  float(self._visainstrument.ask('SENS%i:BWID:RES?'%self._ci))                

    def do_set_zerospan(self,val):
        '''
        Zerospan is a virtual "zerospan" mode. In Zerospan physical span is set to
        the minimal possible value (2Hz) and "averages" number of points is set.

        Input:
            val (bool) : True or False

        Output:
            None
        '''
        #logging.debug(__name__ + ' : setting status to "%s"' % status)
        if val not in [True, False]:
            raise ValueError('set_zerospan(): can only set True or False')        
        if val:
          self._oldnop = self.get_nop()
          self._oldspan = self.get_span()
          if self.get_span() > 0.002:
            Warning('Setting ZVL span to 2Hz for zerospan mode')            
            self.set_span(0.002)
            
        av = self.get_averages()
        self._zerospan = val
        if val:
            self.set_Average(False)
            self.set_averages(av)
            if av<2:
              av = 2
        else: 
          self.set_Average(True)
          self.set_span(self._oldspan)
          self.set_nop(self._oldnop)
          self.get_averages()
        self.get_nop()
               
    def do_get_zerospan(self):
        '''
        Check weather the virtual zerospan mode is turned on

        Input:
            None

        Output:
            val (bool) : True or False
        '''
        return self._zerospan


    def do_set_trigger_source(self,source):
        '''
        Set Trigger Mode

        Input:
            source (string) : AUTO | MANual | EXTernal | REMote

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting trigger source to "%s"' % source)
        if source.upper() in [AUTO, MAN, EXT, REM]:
            self._visainstrument.write('TRIG:SOUR %s' % source.upper())        
        else:
            raise ValueError('set_trigger_source(): must be AUTO | MANual | EXTernal | REMote')
    def do_get_trigger_source(self):
        '''
        Get Trigger Mode

        Input:
            None

        Output:
            source (string) : AUTO | MANual | EXTernal | REMote
        '''
        logging.debug(__name__ + ' : getting trigger source')
        return self._visainstrument.ask('TRIG:SOUR?')        
        

    def do_set_channel_index(self,val):
        '''
        Set the index of the channel to address.

        Input:
            val (int) : 1 .. number of active channels (max 16)

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting channel index to "%i"' % int)
        nop = self._visainstrument.read('DISP:COUN?')
        if val < nop:
            self._ci = val 
        else:
            raise ValueError('set_channel_index(): index must be < nop channels')
    def do_get_channel_index(self):
        '''
        Get active channel

        Input:
            None

        Output:
            channel_index (int) : 1-16
        '''
        logging.debug(__name__ + ' : getting channel index')
        return self._ci
          
    def write(self,msg):
      return self._visainstrument.write(msg)    
    def ask(self,msg):
      return self._visainstrument.ask(msg)
     
    def pre_measurement(self):
        '''
        Set everything needed for the measurement
        '''
        self._visainstrument.write(":TRIG:SOUR BUS")#Only wait for software triggers
        self._visainstrument.write(":TRIG:AVER ON")# Tell the instrument to do the specific number of averages on every trigger.
        
        
    def post_measurement(self):
        '''
        After a measurement, the VNA is in hold mode, and it can be difficult to start a measurement again from front panel.
        This function brings the VNA back to normal measuring operation.
        '''
        self._visainstrument.write(":TRIG:SOUR INT") #Only wait for software triggers
        self._visainstrument.write(":TRIG:AVER OFF")# Tell the instrument to do the specific number of averages on every trigger.
        self.hold(False)
        
      
    def start_measurement(self):
        '''
        This function is called at the beginning of each single measurement in the spectroscopy script.
        Here, it resets the averaging
        '''
        self.avg_clear()
        self._visainstrument.write('*TRG') #go

    
    def ready(self):
        '''
        This is a proxy function, returning True when the VNA has finished the required number of averages.
        '''
        return (int(self._visainstrument.ask(':STAT:OPER:COND?')) & 32)==32