import qkit

import os
import threading
import logging
import time
import json
import numpy as np
import h5py

class UUID_base(object):
    _alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def get_uuid(self,time):
        """
        
        returns a UUID from a given time, e.g. returned by time.time()
        The UUID is returned with a precision of (integer) seconds 
        and has a fixed length of six characters.
        
        Derived from encode_uuid(), orginally located in hdf_DateTimeGenerator.py (AS/MP/HR)
        """
        # if not value: value = self._unix_timestamp
        output = ''
        time = int(time)
        la = len(self._alphabet)
        while time:
            output += self._alphabet[time % la]
            time = time / la
        return output[::-1]
    
    def get_time(self,uuid):
        """
        returns a integer time value from a given UUID timestamp (reverse of get_UUID())
        orginally located in hdf_DateTimeGenerator.py (AS/MP/HR)
        """
        # if not string: string = self._uuid
        output = 0
        multiplier = 1
        uuid = uuid[::-1].upper()
        la = len(self._alphabet)
        while uuid != '':
            f = self._alphabet.find(uuid[0])
            if f == -1:
                raise ValueError("fid.get_time: Can not decode this: {}<--".format(uuid[::-1]))
            output += f * multiplier
            multiplier *= la
            uuid = uuid[1:]
        return output
        
    def get_date(self,uuid):
        """
        Returns a date string from a given UUID timestamp (reverse of get_uuid())
        """
        return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(self.get_time(uuid)))


class file_system_service(UUID_base):
    h5_db = {}
    set_db = {}
    measure_db = {}
    h5_info_db = {}
    
    lock = threading.Lock()

    def update_file_db(self):
        with self.lock:
            if qkit.cfg.get('fid_scan_datadir',True):
                qkit.cfg['fid_scan_datadir'] = True
                logging.debug("file info database: Start to update database.")
                for root, _ , files in os.walk(qkit.cfg['datadir']): # root, dirs, files
                    for f in files:
                        self._inspect_and_add_Leaf(f,root)
                logging.debug("file info database: Updating database done.")

    def _collect_info(self,uuid,path):
            tm = ""
            dt = ""
            j_split = (path.replace('/', '\\')).split('\\')
            name = j_split[-1][7:-3]
            if ord(uuid[0]) > ord('L'):
                try:
                    tm = self.get_time(uuid)
                    dt = self.get_date(uuid)
                except ValueError as e:
                    logging.info(e)
                user = j_split[-3]
                run = j_split[-4]
            else:
                tm = uuid
                if j_split[-3][0:3] is not 201:  # not really a measurement file then
                    dt = None
                else:
                    dt = '{}-{}-{} {}:{}:{}'.format(j_split[-3][:4], j_split[-3][4:6], j_split[-3][6:], tm[:2], tm[2:4], tm[4:])
                user = None
                run = None
            h5_info_db = {'time': tm, 'datetime': dt, 'run': run, 'name': name, 'user': user}

            if qkit.cfg.get('fid_scan_hdf', False):
                h5_info_db.update({'rating':-1})
                try:
                    h5f=h5py.File(path,'r')
                    h5_info_db.update({'comment': h5f['/entry/data0'].attrs.get('comment', '')})
                    try:
                        # this is legacy and should be removed at some point
                        # please use the entry/analysis0 attributes instead.
                        fit_comment = h5f['/entry/analysis0/dr_values'].attrs.get('comment',"").split(', ')
                        comm_begin = [i[0] for i in fit_comment]
                        try:
                            h5_info_db.update({'fit_freq': float(h5f['/entry/analysis0/dr_values'][comm_begin.index('f')])})
                        except (ValueError, IndexError):
                            pass
                        try:
                            h5_info_db.update({'fit_time': float(h5f['/entry/analysis0/dr_values'][comm_begin.index('T')])})
                        except (ValueError, IndexError):
                            pass
                    except (KeyError, AttributeError):
                        pass
                    try:
                        h5_info_db.update(dict(h5f['/entry/analysis0'].attrs))
                    except(AttributeError, KeyError):
                        pass
                    try:
                        mmt = json.loads(h5f['/entry/data0/measurement'][0])
                        h5_info_db.update(
                                {arg: mmt[arg] for arg in ['run_id', 'user', 'rating', 'smt'] if mmt.has_key(arg)}
                        )
                    except(AttributeError, KeyError):
                        pass
                    finally:
                        h5f.close()
                except IOError as e:
                    logging.error("fid %s:%s"%(path,e))

            self.h5_info_db[uuid] = h5_info_db

    def _inspect_and_add_Leaf(self,fname,root):
        uuid = fname[:6]
        fqpath = os.path.join(root, fname)
        if fqpath[-3:] == '.h5':            
            self.h5_db[uuid] = fqpath
            self._collect_info(uuid, fqpath)
        elif fqpath[-3:] == 'set':
            self.set_db[uuid] = fqpath
        elif fqpath[-3:] == 'ent':
            self.measure_db[uuid] = fqpath


    def add(self, h5_filename):
        uuid = h5_filename[:6]
        basename = h5_filename[:-2]
        if h5_filename[-3:] != '.h5':
            raise ValueError("Your filename '{:s}' is not a .h5 filename.".format(h5_filename))
        with self.lock:
            if os.path.isfile(basename + 'h5'):
                self.h5_db[uuid] = basename + 'h5'
                logging.debug("Store_db: Adding manually h5: " + basename + 'h5')
            else:
                raise ValueError("File '{:s}' does not exist.".format(basename + 'h5'))
            if os.path.isfile(basename + 'set'):
                self.set_db[uuid] = basename + 'set'
                logging.debug("Store_db: Adding manually set: " + basename + 'set')
            if os.path.isfile(basename + 'measurement'):
                self.h5_db[uuid] = basename + 'measurement'
                logging.debug("Store_db: Adding manually measurement: " + basename + 'measurement')


    def _set_hdf_attribute(self,UUID,attribute,value):
        h5_filepath = self.h5_db[UUID]
        h = h5py.File(h5_filepath,'r+')['entry']
        try:
            if not 'analysis0' in h:
                h.create_group('analysis0')
            h['analysis0'].attrs[attribute] = value
        finally:
            h.file.close()
        self.h5_info_db[UUID].update({attribute:value})