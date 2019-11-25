#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ABOUT
# S7 support for Artisan

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2018

import time
import platform
import struct
import os
import sys

import artisanlib.util
from artisanlib.suppress_errors import suppress_stdout_stderr

from PyQt5.QtCore import QSemaphore
from PyQt5.QtWidgets import QApplication


class s7port(object):
    def __init__(self,sendmessage,adderror,addserial,aw):
        self.sendmessage = sendmessage # function to create an Artisan message to the user in the message line
        self.adderror = adderror # signal an error to the user
        self.addserial = addserial # add to serial log
        self.aw = aw
        
        self.readRetries = 1
        self.channels = 8 # maximal number of S7 channels
        self.host = '127.0.0.1' # the TCP host
        self.port = 102 # the TCP port
        self.rack = 0 # 0,..,7
        self.slot = 0 # 0,..,31
                
        self.lastReadResult = 0 # this is set by eventaction following some custom button/slider S/ actions with "read" command
        
        self.area = [0]*self.channels
        self.db_nr = [1]*self.channels
        self.start = [0]*self.channels
        self.type = [0]*self.channels
        self.mode = [0]*self.channels # temp mode is an int here, 0:__,1:C,2:F (this is different than other places)
        self.div = [0]*self.channels
        
        self.PID_area = 0
        self.PID_db_nr = 0
        self.PID_SV_register = 0
        self.PID_p_register = 0
        self.PID_i_register = 0
        self.PID_d_register = 0
        self.PID_ON_action = ""
        self.PID_OFF_action = ""
        self.SVmultiplier = 0
        self.PIDmultiplier = 0
        
        self.COMsemaphore = QSemaphore(1)
        
        self.areas = [
            0x81, # PE
            0x82, # PA
            0x83, # MK
            0x1C, # CT
            0x1D, # TM
            0x84, # DB
        ]
        
        self.plc = None
        self.commError = False # True after a communication error was detected and not yet cleared by receiving proper data
        self.libLoaded = False

################
# conversion methods copied from s7:util.py

    def set_int(self,_bytearray, byte_index, _int):
        """
        Set value in bytearray to int
        """
        # make sure were dealing with an int
        _int = int(_int)
        _bytes = struct.unpack('2B', struct.pack('>h', _int))
        _bytearray[byte_index:byte_index + 2] = _bytes
        
    def get_int(self,_bytearray, byte_index):
        """
        Get int value from bytearray.
    
        int are represented in two bytes
        """
        data = _bytearray[byte_index:byte_index + 2]
        data[1] = data[1] & 0xFF # added to fix a conversion problem: see https://github.com/gijzelaerr/python-snap7/issues/101
        value = struct.unpack('>h', struct.pack('2B', *data))[0]
        return value
        
    def set_real(self,_bytearray, byte_index, real):
        """
        Set Real value
    
        make 4 byte data from real
    
        """
        real = float(real)
        real = struct.pack('>f', real)
        _bytes = struct.unpack('4B', real)
        for i, b in enumerate(_bytes):
            _bytearray[byte_index + i] = b
        
    def get_real(self,_bytearray, byte_index):
        """
        Get real value. create float from 4 bytes
        """
        x = _bytearray[byte_index:byte_index + 4]
        real = struct.unpack('>f', struct.pack('4B', *x))[0]
        return real
        
################

        
    def setPID(self,p,i,d,PIDmultiplier):
        if self.PID_area and not (self.PID_p_register == self.PID_i_register == self.PID_d_register == 0):
            multiplier = 1.
            if PIDmultiplier == 1:
                PIDmultiplier = 10.
            elif PIDmultiplier == 2:
                multiplier = 100.
            self.writeInt(self.PID_area-1,self.PID_db_nr,self.PID_p_register,p*multiplier)
            self.writeInt(self.PID_area-1,self.PID_area,self.PID_db_nr,self.PID_i_register,i*multiplier)
            self.writeInt(self.PID_area-1,self.PID_area,self.PID_db_nr,self.PID_d_register,d*multiplier)
        
    def setTarget(self,sv,SVmultiplier):
        if self.PID_area:
            multiplier = 1.
            if SVmultiplier == 1:
                multiplier = 10.
            elif SVmultiplier == 2:
                multiplier = 100.
            self.writeInt(self.PID_area-1,self.PID_db_nr,self.PID_SV_register,int(round(sv*multiplier)))
                    
    def isConnected(self):
        # the check on the CPU state is needed as get_connected() still returns True if the connect got terminated from the peer due to a bug in snap7
        return self.plc is not None and self.plc.get_connected() and str(self.plc.get_cpu_state()) == "S7CpuStatusRun"
        
    def disconnect(self):
        try:
            self.plc.disconnect()
        except Exception:
            pass
        try:
            self.plc.destroy()
        except:
            pass
        self.plc = None
        
    def connect(self):
        if not self.libLoaded:
            #from artisanlib.s7client import S7Client
            from snap7.common import load_library as load_snap7_library
            # first load shared lib if needed
            platf = str(platform.system())
            if platf in ['Windows','Linux'] and artisanlib.util.appFrozen():
                libpath = os.path.dirname(sys.executable)
                if platf == 'Linux':
                    snap7dll = os.path.join(libpath,"libsnap7.so")
                else: # Windows:
                    snap7dll = os.path.join(libpath,"snap7.dll")                
                load_snap7_library(snap7dll) # will ensure to load it only once
            self.libLoaded = True
        
        if self.libLoaded and self.plc is None:
            # create a client instance
            from artisanlib.s7client import S7Client
            self.plc = S7Client()
            
        # next reset client instance if not yet connected to ensure a fresh start
        if self.plc is not None and not self.isConnected():
            try:
                self.plc.disconnect()
            except:
                pass
            with suppress_stdout_stderr():
                time.sleep(0.6)
                try:
                    self.plc.connect(self.host,self.rack,self.slot,self.port)
                    time.sleep(0.6)
                except Exception:
                    pass
            if self.isConnected():
                self.sendmessage(QApplication.translate("Message","S7 Connected", None))
                time.sleep(0.7)
            else:
                time.sleep(0.8)
                # we try a second time
                with suppress_stdout_stderr():
                    time.sleep(0.6)
                    self.plc.connect(self.host,self.rack,self.slot,self.port)
                    time.sleep(0.8)
                if self.isConnected():
                    self.sendmessage(QApplication.translate("Message","S7 Connected", None) + " (2)")
                    time.sleep(0.7)

    def writeFloat(self,area,dbnumber,start,value):
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.isConnected():
                with suppress_stdout_stderr():
                    ba = self.plc.read_area(self.areas[area],dbnumber,start,4)
                    self.set_real(ba, 0, float(value))
                    self.plc.write_area(self.areas[area],dbnumber,start,ba)
            else:
                self.adderror((QApplication.translate("Error Message","S7 Error:",None) + " connecting to PLC failed"))               
        except Exception as e:
            self.adderror(QApplication.translate("Error Message","S7 Communication Error",None) + " writeFloat: " + str(e))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                self.addserial("S7 writeFloat({},{},{},{})".format(area,dbnumber,start,value))

    def writeInt(self,area,dbnumber,start,value): 
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.isConnected():
                with suppress_stdout_stderr():
                    ba = self.plc.read_area(self.areas[area],dbnumber,start,2)
                    self.set_int(ba, 0, int(value))
                    self.plc.write_area(self.areas[area],dbnumber,start,ba)
            else:
                self.adderror((QApplication.translate("Error Message","S7 Error:",None) + " connecting to PLC failed"))               
        except Exception as e:
            self.adderror(QApplication.translate("Error Message","S7 Communication Error",None) + " writeInt: " + str(e))
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                self.addserial("S7 writeInt({},{},{},{})".format(area,dbnumber,start,value))
                    
    def readFloat(self,area,dbnumber,start):
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.isConnected():
                retry = self.readRetries   
                res = None             
                while True:
                    try:
                        with suppress_stdout_stderr():
                            res = self.plc.read_area(self.areas[area],dbnumber,start,4)
                    except:
                        res = None
                    if res is None:
                        if retry > 0:
                            retry = retry - 1
                        else:
                            raise Exception("Communication error")
                    else:
                        break
                if res is None:
                    return -1
                else:
                    if self.commError: # we clear the previous error and send a message
                        self.commError = False
                        self.adderror(QApplication.translate("Error Message","S7 Communication Resumed",None))
                    return self.get_real(res,0)
            else:
                self.commError = True  
                self.adderror((QApplication.translate("Error Message","S7 Error:",None) + " connecting to PLC failed"))                                 
                return -1
        except Exception as e:
            self.adderror(QApplication.translate("Error Message","S7 Communication Error",None) + " readFloat: " + str(e))
            self.commError = True
            return -1
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                self.addserial("S7 readFloat({},{},{})".format(area,dbnumber,start))
                
    def readInt(self,area,dbnumber,start):
        try:
            #### lock shared resources #####
            self.COMsemaphore.acquire(1)
            self.connect()
            if self.isConnected():
                retry = self.readRetries   
                res = None             
                while True:
                    try:
                        with suppress_stdout_stderr():
                            res = self.plc.read_area(self.areas[area],dbnumber,start,2)
                    except Exception:
                        res = None
                    if res is None:
                        if retry > 0:
                            retry = retry - 1
                        else:
                            raise Exception("Communication error")
                    else:
                        break
                if res is None:
                    return -1
                else:
                    if self.commError: # we clear the previous error and send a message
                        self.commError = False
                        self.adderror(QApplication.translate("Error Message","S7 Communication Resumed",None))
                    return self.get_int(res,0)
            else:
                self.commError = True  
                self.adderror((QApplication.translate("Error Message","S7 Error:",None) + " connecting to PLC failed"))
                return -1
        except Exception as e:
            self.adderror(QApplication.translate("Error Message","S7 Communication Error",None) + " readInt: " + str(e))
            self.commError = True
            return -1
        finally:
            if self.COMsemaphore.available() < 1:
                self.COMsemaphore.release(1)
            if self.aw.seriallogflag:
                self.addserial("S7 readInt({},{},{})".format(area,dbnumber,start))
