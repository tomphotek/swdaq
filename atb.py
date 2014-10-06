# -*- coding: utf-8 -*-
import crcmod
import serial
from math import log, ceil
from bitarray import bitarray
from time import sleep, time
from random import randrange
from sys import stderr
import socket
import struct
from time import time
from posix_ipc import SharedMemory
import mmap
import os
import struct
from subprocess import Popen, PIPE
from sys import maxint

class AsicGlobalConfig(bitarray):
  def __init__(self, initial=None, endian="big"):
	super(AsicGlobalConfig, self).__init__()

	if initial is not None:
		self[0:110] = bitarray(initial)
		return None

	self.__fields = {
	  'tdc_comp'			: [ 26 + 83 - x for x in range(6) ],
	  'comp_vcas'			: [ 26 + 77 - x for x in range(6) ],
	  'tdc_iref'			: [ 26 + 71 - x for x in range(6) ],
	  'tdc_tac'			: [ 26 + 65 - x for x in range(6) ],
	  'lvlshft'			: [ 26 + 54 + x for x in range(6) ],
	  'vib2'			: [ 26 + 48 + x for x in range(6) ],
	  'vib1' 			: [ 26 + 42 + x for x in range(6) ],
	  'sipm_idac_range' 		: [ 26 + 36 + x for x in range(6) ],
	  'sipm_idac_dcstart'		: [ 26 + 30 + x for x in range(6) ],
	  'disc_idac_range'		: [ 26 + 29 - x for x in range(6) ],
	  'disc_idac_dcstart'		: [ 26 + 23 - x for x in range(6) ],
	  'postamp'			: [ 26 + 17 - x for x in range(6) ],
	  'fe_disc_ibias'		: [ 26 + 11 - x for x in range(6) ],
	  'fe_disc_vcas'		: [ 26 + 05 - x for x in range(6) ],
	  'clk_o_en'			: [ 25 ],
	  'test_pattern' 		: [ 24 ],
	  'veto_en'			: [ 23 ],
	  'data_mode'			: [ 22 ],
	  'count_intv'			: [ 21, 20, 19, 18 ],
	  'count_trig_err'		: [ 17 ],
	  'fc_kf'			: [ 16 - x for x in range(8) ],
	  'fc_saturate'			: [ 8 ],
	  'tac_refresh'			: [ 7, 6, 5, 4 ],
	  'test_pulse_en'		: [ 3 ],
	  'ddr_mode' 			: [ 2 ],
	  'tx_mode'			: [ 1, 0 ]
	}



	self[0:110] = bitarray(110)

	# Reset values
	self.setValue('tdc_comp', 32)
	self.setValue('comp_vcas', 32)
	self.setValue('tdc_iref', 32)
	self.setValue('tdc_tac', 32)
	self.setValue('lvlshft', 44)
	self.setValue('vib1', 48)
	self.setValue('vib2', 48)
	self.setValue('sipm_idac_range', 40)
	self.setValue('sipm_idac_dcstart', 45)
	self.setValue('disc_idac_range', 48)
	self.setValue('disc_idac_dcstart', 35)
	self.setValue('postamp', 44)
	self.setValue('fe_disc_ibias', 43)
	self.setValue('fe_disc_vcas', 42)
	self.setValue('clk_o_en', 1)
	self.setValue('test_pattern', 0)
	self.setValue('veto_en', 0)
	self.setValue('data_mode', 1)
	self.setValue('count_intv', 0)
	self.setValue('count_trig_err', 0)
	self.setValue('fc_kf', 0)
	self.setValue('fc_saturate', 0)
	self.setValue('tac_refresh', 3)
	self.setValue('test_pulse_en', 1)
	self.setValue('ddr_mode', 0)
	self.setValue('tx_mode', 1)
	
	# Sane defaults
	self.setValue('sipm_idac_dcstart', 52)
	self.setValue('tac_refresh', 0)
	self.setValue('disc_idac_dcstart', 45);
	self.setValue('test_pulse_en', 0);
	self.setValue('tx_mode', 0)
	self.setValue("fe_disc_ibias", 20)
	self.setValue("count_intv", 15)
	
	# Old slihgtly insane settings
	#self[0:110] = bitarray(\
	  #'100000' + \
	  #'100000' + \
	  #'100000' + \
	  #'100000' + \
	  #'001101'[::-1] + \
	  #'000011'[::-1] + \
	  #'000011'[::-1] + \
	  #'000101'[::-1] + \
	  #'101101'[::-1] + \
	  #'110000' + \
	  #'100011' + \
	  #'101100' + \
	  #'101011' + \
	  #'100000' + \
	  #'10010000000000000000000000')

	# From testing
	self.setValue("tdc_iref", 42)		# was calibration with 48 ???
	self.setValue("tdc_iref", 32)		# 160 MHz
	self.setValue("disc_idac_dcstart", 45);
	self.setValue("disc_idac_dcstart", 50);
	self.setValue("disc_idac_range", 32);	#tryout
	self.setValue("vib1", 0)
	self.setValue("vib2", 20)
	self.setValue("sipm_idac_range", 32)
#	self.setValue("sipm_idac_dcstart", 46) # ATB
	self.setValue("sipm_idac_dcstart", 38) # TTB 
	self.setValue("tac_refresh", 0)
	self.setValue("lvlshft", 10)
#	self.setValue("sipm_idac_dcstart", 48) # TTB? Xtreme - preamp estrangulado!!! (strangled)
#	self.setValue("sipm_idac_dcstart", 42) # TTB? - começa a estrangular - starts to strangle!
#	self.setValue("sipm_idac_dcstart", 40) # TTB? OK: Vin = 435mV @vbl=63
	self.setValue("postamp", 50)
	#self.setValue("postamp", 40)

	# Introduced after oscillation problems were found
	self.setValue("vib2", 20)
	self.setValue("vib1", 24)
	self.setValue("sipm_idac_dcstart", 48)

	

  def setValue(self, key, value):
	b = intToBin(value, len(self.__fields[key]))
	self.setBits(key, b)
	
  def setBits(self, key, value):
	index = self.__fields[key]
	assert len(value) == len(index)
	for a,b in enumerate(index):
	  self[109 - b] = value[a]
	
  def getBits(self, key):
	index = self.__fields[key]
	value = bitarray(len(index))
	for a,b in enumerate(index):
	  value[a] = self[109 - b]
	return value
	
  def getValue(self, key):
	return binToInt(self.getBits(key))
	
  def printAllBits(self):
	for key in self.__fields.keys():
	  print key, " : ", self.getBits(key)

  def printAllValues(self):
	for key in self.__fields.keys():
	  print key, " : ", self.getValue(key)

  def getKeys(self):
	return self.__fields.keys()


class AsicChannelConfig(bitarray):
  def __init__(self, initial=None, endian="big"):
	super(AsicChannelConfig, self).__init__()

	self.__baseline = 0

	if initial is not None:
		self[0:53] = bitarray(initial)
		return None
	
	self.__fields = {
	  'd_E'	: [48 + x for x in range(5) ],
	  'test' : [ 47, 46, 45, 44, 42 ],
	  'sync' : [ 43 ],
	  'deadtime' : [ 41, 40 ],
	  'meta_cfg' : [ 39, 38 ],
	  'latch_cfg' : [ 37, 36, 30 ],
	  'cgate_cfg' : [29, 28, 27 ],
	  'd_T' : [ 35 - x for x in range(5) ],
	  'g0' : [26, 25], 
	  'sh' : [ 24, 23 ],
	  'vth_E' : [17 + x for x in range(6) ],
	  'vth_T' : [11 + x for x in range(6) ],
	  'vbl' : [ 3, 2, 7, 8, 9, 10 ],
	  'inpol' : [ 6 ],
	  'fe_test_mode' : [ 5 ],
	  'fe_tmjitter' :  [ 4 ],
	  'praedictio' : [ 1 ],
	  'praedictio_delay' : [ 30, 29, 28, 27 ],
	  'enable' : [ 0 ]
	}
	
	self[0:53] = bitarray(53)
	
	# Reset Value
	self.setValue('d_E', 28)
	self.setBits('test', bitarray("00000"))
	self.setValue('sync', 1)
	self.setBits('deadtime', bitarray("00"))
	self.setBits('meta_cfg', bitarray("01"))
	self.setValue('latch_cfg', 1)
	self.setValue('cgate_cfg', 7)
	self.setValue('d_T', 7)
	self.setValue('g0', 3)
	self.setValue('sh', 3)
	self.setValue('vth_E', 3)
	self.setValue('vth_T', 59)
	self.setValue('vbl', 31)
	self.setValue('inpol', 1)
	self.setValue('fe_test_mode', 0)
	self.setValue('fe_tmjitter', 0)
	self.setValue('praedictio', 1)
	self.setValue('enable', 1)
	
	# Sane defaults
	self.setValue('d_E', 7)
	self.setValue('vbl', 48)
	self.setValue('sh', 3)
	self.setValue('latch_cfg', 0)
	self.setValue('cgate_cfg', 0)

	# Old slihgtly insane settings
	#self[0:53] = bitarray('11100000010000100001111111110111000011011111111000111')

	# From testing
	self.setValue("inpol", 0)
	self.setValue("d_T", 7) # x128 interpolation
	self.setValue("d_E", 7)
	#channelConfig.setValue("d_T", 7+16) # x256 interpolation
	#channelConfig.setValue("d_E", 7+16)
	#channelConfig.setValue("sh", 0)
	self.setValue("g0", 3)
	self.setValue("vbl", 52)
	self.setValue("vth_T", 5);
	self.setValue("vth_E", 5);

	# Introduced after oscillation problems were found
	self.setValue("vbl", 44)

	
  def setValue(self, key, value):
	b = intToBin(value, len(self.__fields[key]))
	self.setBits(key, b)
	
  def setBits(self, key, value):
	index = self.__fields[key]
	assert len(value) == len(index)
	for a,b in enumerate(index):
	  self[52 - b] = value[a]
	
  def getBits(self, key):
	index = self.__fields[key]
	value = bitarray(len(index))
	for a,b in enumerate(index):
	  value[a] = self[52 - b]
	return value
	
  def getValue(self, key):
	return binToInt(self.getBits(key))
	
  def printAllBits(self):
	for key in self.__fields.keys():
	  print key, " : ", self.getBits(key)

  def printAllValues(self):
	for key in self.__fields.keys():
	  print key, " : ", self.getValue(key)

  def setBaseline(self, v):
	self.__baseline = v

  def getBaseline(self):
	return self.__baseline

  def getKeys(self):
	return self.__fields.keys()

class AsicConfig:
	def __init__(self):
		self.channelConfig = [ AsicChannelConfig() for x in range(64) ]
		self.channelTConfig = [ bitarray('0') for x in range(64) ]
		self.globalConfig = AsicGlobalConfig()
		self.globalTConfig = bitarray('1111110')	
		return None
	

class BoardConfig:
	def __init__(self, nASIC=2, nDAC=1):
		
                self.asicConfigFile = [ "Default Configuration" for x in range(nASIC) ]
                self.asicBaselineFile = [ "None" for x in range(nASIC) ]
                self.HVDACParamsFile = "None"
                self.asicConfig = [ AsicConfig() for x in range(nASIC) ]
		self.hvBias = [ 0.0 for x in range(32*nDAC) ]
		self.hvParam = [ (1.0, 0.0) for x in range(32*nDAC) ]
		return None

        def writeParams(self, prefix):
    
          defaultAsicConfig = AsicConfig()
          
          global_params= self.asicConfig[0].globalConfig.getKeys()
          channel_params= self.asicConfig[0].channelConfig[0].getKeys()
          

          f = open(prefix+'.params', 'w')
          f.write("--------------------\n")
          f.write("-- DEFAULT PARAMS --\n")
          f.write("--------------------\n\n")
          f.write("Global{\n")    
 
        
          for i,key in enumerate(global_params):
            for ac in self.asicConfig:
              value= ac.globalConfig.getValue( key)
              value_d= defaultAsicConfig.globalConfig.getValue(key)
              if(value_d==value):
                check=True
              else:
                check=False
                break    
            if check:
               f.write('\t"%s" : %d\n' % (key, value))         
   
          f.write("\t}\n")    
          f.write("\n") 
          f.write("Channel{\n")    
    
          check=True
          for i,key in enumerate(channel_params):
            for ac in self.asicConfig:
              if not check:
                break 
              for ch in range(64):
                value= ac.channelConfig[ch].getValue(key)
                value_d= defaultAsicConfig.channelConfig[ch].getValue(key)
                if(value_d==value):
                  check=True 
                else:
                  check=False
                  break    
            if check:
              f.write('\t"%s" : %d\n' % (key, value))
            
          f.write("\t}\n\n")  
          f.write("------------------------\n")
          f.write("-- NON-DEFAULT PARAMS --\n")    
          f.write("------------------------\n")
          ac_ind=0
          for ac in self.asicConfig:
        
            f.write("\nASIC%d.Global{\n"%ac_ind)  
            for i,key in enumerate(global_params):
              value= ac.globalConfig.getValue(key)
              value_d= defaultAsicConfig.globalConfig.getValue(key)
              if(value_d!=value):
                f.write('\t"%s" : %d\n' % (key, value)) 
            f.write("\t}\n\n")
        
            f.write("ASIC%d.ChAll{\n"%ac_ind)  
            key_list = []
            for i,key in enumerate(channel_params):
              prev_value=ac.channelConfig[0].getValue(key)
              for ch in range(64):
                value= ac.channelConfig[ch].getValue(key)   
                value_d= defaultAsicConfig.channelConfig[ch].getValue(key)
                if((value_d!=value) and (value==prev_value)):
                  check=True 
                  prev_value=value
                else:
                  check=False
                  if(value_d!=value):
                    key_list.append(key)
                  break    
              if check:
		f.write('\t"%s" : %d\n' % (key, value))
                
            prev_baseline=ac.channelConfig[0].getBaseline()
            for ch in range(64):
              baseline= ac.channelConfig[ch].getBaseline()  
              if(baseline==prev_baseline):
                check=True 
              else:
                check=False
            if check:
              f.write("\tBASELINE : %d\n" %  baseline)

            f.write("\t}\n\n")
            
            if not check:
              for ch in range(64):
                f.write("ASIC%d.Ch%d{\n"%(ac_ind,ch))
                for key in key_list:
                  value= ac.channelConfig[ch].getValue(key)
                  f.write('\t"%s" : %d\n' % (key, value))
                baseline= ac.channelConfig[ch].getBaseline()
                f.write("\tBASELINE : %d\n"%baseline)
                f.write("\t}\n")
            ac_ind+=1


          f.write("\n") 
          f.write("--------------------------------------\n")
          f.write("-- CONFIGURATION and BASELINE FILES --\n")
          f.write("--------------------------------------\n\n")
          f.write("HVDAC File: %s\n"%self.HVDACParamsFile)
          asic_id=0
          for filename in self.asicConfigFile:
            f.write("ASIC%d Configuration File: %s\n"%(asic_id,filename)) 
            asic_id+=1
          asic_id=0
          for filename in self.asicBaselineFile:
            f.write("ASIC%d Baseline File: %s\n"%(asic_id,filename))
            asic_id+=1
          f.write("\n")
          f.write("-------------\n")
          f.write("-- HV BIAS --\n")
          f.write("-------------\n\n")
          for entry in self.hvBias:
            f.write("%f"%entry)
            f.write("\n")
          f.close()



def intToBin(v, n, reverse=False):
	v = int(v)
	if v < 0: 
		v = 0

	if v > 2**n-1:
		v = 2**n-1

	s = bitarray(n, endian="big")
	for i in range(n):
		s[n-i-1] = (v >> i) & 1 != 0
	if reverse:
		s.reverse();
	return s 
	
def binToInt(s, reverse=False):
	if reverse:
		s.reverse()
	r = 0
	n = len(s)
	for i in range(n):
		r += s[i] * 2**(n-i-1)
	return r
	
def grayToBin(g):
	b = bitarray(len(g))
	b[0] = g[0]
	for i in range(1, len(g)):
		b[i] = b[i-1] != g[i]
	return b
	
def grayToInt(v):
	return binToInt(grayToBin(v))
	
	
class ATB:
	def __init__(self, socketPath, debug=False, F=160E6):
		self.__socketPath = socketPath
		self.__socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		self.__socket.connect(self.__socketPath)
		self.__crcFunc = crcmod.mkCrcFun(0x104C11DB7, rev=False, initCrc=0x0A1CB27F)
		self.__lastSN = randrange(0, 2**16-1)
		self.__pendingReplies = 0
		self.__recvBuffer = bytearray([]);
		self.__debug = debug
		self.__dataFramesIndexes = []
		self.__sync0 = 0
		self.__lastSync = 0
		self.__frameLength = 1024.0 / F
		shmName, s0, p1, s1 = self.__getSharedMemoryInfo()
		self.__shmParams = (s0, p1, s1)
		self.__shm = SharedMemory(shmName)
		self.__shmmap = mmap.mmap(self.__shm.fd, self.__shm.size)
		#os.close(self.__shm.fd)
		self.config = None
		return None

	def start(self, mode=2):
		template1 = "@HH"
		template2 = "@H"
		n = struct.calcsize(template1) + struct.calcsize(template2);
		data = struct.pack(template1, 0x01, n) + struct.pack(template2, mode)
		self.__socket.send(data)
		return None

	def stop(self):
		template1 = "@HH"
		template2 = "@H"
		n = struct.calcsize(template1) + struct.calcsize(template2);
		data = struct.pack(template1, 0x01, n) + struct.pack(template2, 0)
		self.__socket.send(data)
		return None

	def __getSharedMemorySize(self):
		return self.__shm.size

	def __getSharedMemoryName(self):
		name, s0, p1, s1 =  self.__getSharedMemoryInfo()
		return name

	def __getSharedMemoryInfo(self):
		template = "@HH"
		n = struct.calcsize(template)
		data = struct.pack(template, 0x02, n)
		self.__socket.send(data);

		template = "@HQQQ"
		n = struct.calcsize(template)
		data = self.__socket.recv(n);
		length, s0, p1, s1 = struct.unpack(template, data)
		name = self.__socket.recv(length - n);
		return (name, s0, p1, s1)

	def getDataFrame(self, waitForDataFrame = True):
		
		index = None
		while index is None and waitForDataFrame:
			index = self.getDataFrameByIndex()

		if index is None:
			return None

		s0, p1, s1 = self.__shmParams

		p0 = index*s0
		template = "@Q?H"
		n = struct.calcsize(template)
		frameID, frameLost, nEvents = struct.unpack(template, self.__shmmap[p0:p0+n])
		reply = { "id" : frameID, "lost" : frameLost }

		events = []
		template = "@HHHHHHHqq"
		n = struct.calcsize(template)
		for i in range(nEvents):
			p = p0 + p1 + s1*i
			event = struct.unpack(template, self.__shmmap[p:p+n])
			events.append(event)

		reply['events'] = events

		self.returnDataFrameByIndex(index)
		return reply

	def getDataFrameByIndex(self):
		rawIndexes = self.getDataFramesByRawIndex(1);
		if len(rawIndexes) == 0:
			return None
		template = "@i"
		index, = struct.unpack(template, rawIndexes)
		return index
	
	def returnDataFrameByIndex(self, index):
		template = "@i"
		rawIndexes = struct.pack(template, index)
		self.returnDataFramesByRawIndex(rawIndexes)


	def returnDataFramesByRawIndex(self, rawIndexes):
		template = "@i"
		n0 = struct.calcsize(template)
		nFrames = len(rawIndexes)/n0
		template1 = "@HH";
		template2 = "@H";
		template3 = "@i"
		n1 = struct.calcsize(template1)
		n2 = struct.calcsize(template2)
		n3 = struct.calcsize(template3) * nFrames
		data = struct.pack(template1, 0x04, n1+n2+n3) + struct.pack(template2, nFrames) + rawIndexes[0:n3]
		self.__socket.send(data)

		  
	def getDataFramesByRawIndex(self, nFrames):
		template1 = "@HH";
		template2 = "@H";
		n1 = struct.calcsize(template1)
		n2 = struct.calcsize(template2)
		data = struct.pack(template1, 0x03, n1+n2) + struct.pack(template2, nFrames)
		self.__socket.send(data)

		template = "@HH"
		n = struct.calcsize(template)
		data = self.__socket.recv(n)
		length, nFrames = struct.unpack(template, data)

		if nFrames == 0:
			return ""

		template = "@i"
		n = struct.calcsize(template)
		return self.__socket.recv(n * nFrames)
	

	
		
	def sendCommand(self, commandType, payload, getReply=True, maxTries=10):
		assert self.config is not None

		nTries = 0;
		reply = None
		while reply == None and nTries < maxTries:
			nTries = nTries + 1

			sn = self.__lastSN
			self.__lastSN = (sn + 1) & 0xFFFF
			rawFrame = bytearray([(sn >> 8) & 0xFF, (sn >> 0) & 0xFF, commandType]) + payload
			rawFrame = str(rawFrame)

			#print [ hex(ord(x)) for x in rawFrame ]

			template1 = "@HH"
			n = struct.calcsize(template1) + len(rawFrame)
			data = struct.pack(template1, 0x05, n)
			self.__socket.send(data)
			self.__socket.send(rawFrame);

			template2 = "@H"
			n = struct.calcsize(template2)
			data = self.__socket.recv(n)
			nn, = struct.unpack(template2, data)

			if nn < 4:
				continue

			#print "Trying to read %d bytes" % nn
			data = self.__socket.recv(nn)

			data = data[3:]
			reply = bytearray(data)
			#print [ "%02X" % x for x in reply ]
			

		return reply
	
		
		

	def setSI53xxRegister(self, regNum, regValue):
		reply = self.sendCommand(0x02, bytearray([0b00000000, regNum]))	
		reply = self.sendCommand(0x02, bytearray([0b01000000, regValue]))
		reply = self.sendCommand(0x02, bytearray([0b10000000]))
		return None
	
	

	  
	
	def doAsicCommand(self, asicID, command, value=None, channel=None):

		commandInfo = {
		#	commandID 		: (code,   ch,   read, data length)
			"wrChCfg"		: (0b0000, True, False, 53),
			"rdChCfg"		: (0b0001, True, True, 53),
			"wrChTCfg"		: (0b0010, True, False, 1),
			"rdChTCfg"		: (0b0011, True, True, 1),
			"rdChDark"		: (0b0100, True, True, 10),
			
			"wrGlobalCfg" 	: (0b1000, False, False, 26+14*6),
			"rdGlobalCfg" 	: (0b1001, False, True, 26+14*6),
			"wrGlobalTCfg"	: (0b1100, False, False, 7),
			"rdGlobalTCfg"	: (0b1101, False, True, 7),
			"wrTestPulse"	: (0b1010, False, False, 10+8+8)
		}
		
	
		commandCode, isChannel, isRead, dataLength = commandInfo[command]
		byte0 = [ (commandCode << 4) + (asicID & 0xFF) ]
		if isChannel:
				
			byte1 = [ (channel) & 0xFF ]
			
		else:
			byte1 = []
			
		
		if not isRead:
			assert len(value) == dataLength
			nBytes = int(ceil(dataLength / 8.0))
			paddedValue = value + bitarray([ False for x in range((nBytes * 8) - dataLength) ])
			byteX = [ ord(x) for x in paddedValue.tobytes() ]
		else:
			byteX = []
		
		cmd = bytearray(byte0 + byte1 + byteX)
		#print asicID, channel, command, value
		#print "ASIC COMMAND ", (", ").join(['x"%02X"' % x for x in cmd])
		
		# TODO: detect ASIC is present
		#nTries = 0
		#status = 0xEF
		#while status != 0x00 and nTries < 10:
			#nTries += 1
			#reply = self.sendCommand(0x00, cmd)
			#status = reply[0]		
		#assert status == 0x00

		reply = self.sendCommand(0x00, cmd)
		status = reply[0]		

		if isRead:
			#print [ "%02X" % x for x in reply ]
			reply = str(reply[2:])
			data = bitarray()
			data.frombytes(reply)
			#print data
			return (status, data[0:dataLength])
		else:
			return (status, None)

	def initialize(self, maxTries = 10):
		assert self.config is not None

		for c in range(len(self.config.hvParam)):
			self.setHVDAC(c, 0)
	
		receivedFrame = None
		attempt = 1
		pause = 0.2
		while receivedFrame is None and attempt <= maxTries:
			print "Reseting and configuring board (attempt %d)" % attempt
			attempt += 1

			# Reset ASIC & ASIC readout
			self.stop()	
			self.sendCommand(0x03, bytearray([0x00, 0x00, 0x00, 0xFF, 0xFF]))
			sleep(pause)
			self.setTestPulseNone()

			# TX calibration
			#txCalibrateAsicGlobalConfig = AsicGlobalConfig()
			#txCalibrateAsicGlobalConfig.setValue("tx_mode", 3)
                        #for asic in range(2):
			#	 status, _ = self.doAsicCommand(asic, "wrGlobalCfg", value=txCalibrateAsicGlobalConfig);

			#self.sendCommand(0x03, bytearray([0x04, 0xFF, 0x0]))
			#sleep(1.0)
			#self.sendCommand(0x03, bytearray([0x04, 0x00, 0x00, 0x00, 0x00]))

			defaultAsicChannelConfig = AsicChannelConfig()
			defaultAsicGlobalConfig = AsicGlobalConfig()
			for asic in range(16):
				for channel in range(64):
					status, _ = self.doAsicCommand(asic, "wrChCfg", value=defaultAsicChannelConfig, channel=channel)
					status, _ = self.doAsicCommand(asic, "wrChTCfg", value=bitarray('0'), channel=channel)
				
				status, _ = self.doAsicCommand(asic, "wrGlobalCfg", value=defaultAsicGlobalConfig);
				status, _ = self.doAsicCommand(asic, "wrGlobalTCfg", value=bitarray("1111110"))
			
			# Set normal RX mode and sync to start
			self.sendCommand(0x03, bytearray([0x04, 0x00, 0x0F]))
			self.sendCommand(0x03, bytearray([0x00, 0x00, 0x00, 0x00, 0x00]))
			sleep(pause)
			self.start()			
			sleep(pause)
			receivedFrame = self.getDataFrame()
			if pause < 1.5: pause += 0.1

		self.doSync()

	def getCurrentFrameID(self):
		reply = self.sendCommand(0x03, bytearray([0x02]))
		status = reply[0]
		data = reply[2:6]

		data = sum([ data[i] * 2**(24 - 8*i) for i in range(len(data)) ])
		return status, data

	def doSync(self, clearFrames=True):
		_, targetFrameID = self.getCurrentFrameID()
		#print "Waiting for frame %d" % frameID
		while True:
			df = self.getDataFrame()
			if df == None:
				continue;

			if  df['id'] > targetFrameID:
				break

			indexes = self.getDataFramesByRawIndex(128)
			self.returnDataFramesByRawIndex(indexes)
		

		return
	  
		
	def setHVDAC(self, channel, voltage):
		assert self.config is not None

		m, b = self.config.hvParam[channel]
		voltage = voltage * m + b

		voltage = int(voltage * 2**14 / (50 * 2.048))
		if voltage > 2**14-1:
			voltage = 2**14-1

		if voltage < 0:
			voltage = 0


		whichDAC = 1
		channelMap = [	30, 18, 24, 28, 31, 22, 23, 27, \
				 3,  7,  1,  5,  0,  2,  6,  4, \
				15, 10, 20, 21, 13, 11, 14, 26, \
				16,  9, 17, 19, 12,  8, 25, 29  \
				]
		channel = channelMap [channel]

		dacBits = intToBin(whichDAC, 1) + intToBin(channel, 5) + intToBin(voltage, 14) + bitarray('0000')
		dacBytes = bytearray(dacBits.tobytes())
		return self.sendCommand(0x01, dacBytes)
	
	def setTestPulseNone(self):
		cmd =  bytearray([0x01] + [0x00 for x in range(8)])
		return self.sendCommand(0x03,cmd)

	def setTestPulseArb(self, invert):
		if not invert:
			tpMode = 0b11000000
		else:
			tpMode = 0b11100000

		cmd =  bytearray([0x01] + [tpMode] + [0x00 for x in range(7)])
		return self.sendCommand(0x03,cmd)
		
	def setTestPulsePLL(self, length, interval, finePhase, invert):
		if not invert:
			tpMode = 0b10000000
		else:
			tpMode = 0b10100000

		finePhase0 = finePhase & 255
		finePhase1 = (finePhase >> 8) & 255
		finePhase2 = (finePhase >> 16) & 255
		interval0 = interval & 255
		interval1 = (interval >> 8) & 255
		length0 = length & 255
		length1 = (length >> 8) & 255
		
		cmd =  bytearray([0x01, tpMode, finePhase2, finePhase1, finePhase0, interval1, interval0, length1, length0])
		return self.sendCommand(0x03,cmd)

	def loadArbTestPulse(self, address, isPulse, delay, length):
		if isPulse:
			isPulseBit = bitarray('1')
		else:
			isPulseBit = bitarray('0')

		delayBits = intToBin(delay, 21)
		lengthBits = intToBin(length, 10)

		addressBits = intToBin(address,32)
		
		bits =  isPulseBit + delayBits + lengthBits + addressBits
		cmd = bytearray([0x03]) + bytearray(bits.tobytes())
		#print [ hex(x) for x in cmd ]
		return self.sendCommand(0x03,cmd)

	  
	def openAcquisition(self, fileName, cWindow):
		from os import environ
		if not environ.has_key('ADAQ_CRYSTAL_MAP'):
			print 'Error: ADAQ_CRYSTAL_MAP environment variable is not set'
			exit(1)

		cmd = [ "aDAQ/writeRaw", self.__getSharedMemoryName(), "%d" % self.__getSharedMemorySize(), \
				"%e" % cWindow, \
				fileName ]
		self.__acquisitionPipe = Popen(cmd, bufsize=1, stdin=PIPE, stdout=PIPE, close_fds=True)

	def acquire(self, step1, step2, acquisitionTime):
		#print "Python:: acquiring %f %f"  % (step1, step2)
		(pin, pout) = (self.__acquisitionPipe.stdin, self.__acquisitionPipe.stdout)
		nFrames = 0

		template1 = "@ffii"
		template2 = "@i"
		n1 = struct.calcsize(template1)
		n2 = struct.calcsize(template2)
		rawIndexes = self.getDataFramesByRawIndex(1024)

                nRequiredFrames = acquisitionTime / self.__frameLength
		t0 = time()
		while nFrames < nRequiredFrames:
			nFramesInBlock = len(rawIndexes)/n2
			if nFramesInBlock <= 0:
				print "Python:: Could not read any data frame indexes"
				break
			#print "Python:: About to push %d frames" % nFramesInBlock
			
			header = struct.pack(template1, step1, step2, nFramesInBlock, 0)
			pin.write(header)
			pin.write(rawIndexes[0:n2*nFramesInBlock])
			pin.flush()

			nFrames += nFramesInBlock
			newRawIndexes = self.getDataFramesByRawIndex(1024)

			tmp = pout.read(n2*nFramesInBlock)
			#print "Python:: got back %d frames" % (len(tmp)/n2)
			
			self.returnDataFramesByRawIndex(rawIndexes)
			rawIndexes = newRawIndexes

		#print "Python:: Returning last frames"
		self.returnDataFramesByRawIndex(rawIndexes)


		#t0 = time()
		#while time() - t0 < acquisitionTime:
			#print "Asking for indexes..."
			#rawIndexes = self.getDataFramesByRawIndex(1024)
			
			#self.returnDataFramesByRawIndex(rawIndexes)

		# Close the deal by sending a block with a -1 index and endOfStep set to 1
		header = struct.pack(template1, step1, step2, 1, 1)
		rawIndexes = struct.pack(template2, -1)		
		#print "Python:: closing step with ",[hex(ord(c)) for c in rawIndexes ]
		pin.write(header)
		pin.write(rawIndexes)
		pin.flush()
		rawIndexes = pout.read(n2)
		index, = struct.unpack(template2, rawIndexes)
		assert index == -1
		#print "Python:: got back %ld\n" % (long(index)), [hex(ord(c)) for c in rawIndexes ]
		#self.returnDataFramesByRawIndex(rawIndexes)
	

		print "Python:: Acquired %d frames in %f seconds, corresponding to %f seconds of data" % (nFrames, time()-t0, nFrames * self.__frameLength)
		return None

	def uploadConfig(self):
		# Force parameters!
		for ac in self.config.asicConfig:
			for cc in ac.channelConfig:
				cc.setValue("deadtime", 3);

		#for dacChannel, hvValue in enumerate(self.config.hvBias):
			#self.setHVDAC(dacChannel, 0)
		#self.stop()
		#self.sendCommand(0x03, bytearray([0x00, 0x00, 0x00, 0xFF, 0xFF]))

		for asic in range(len(self.config.asicConfig)):
			for channel in range(64):
				status, _ = self.doAsicCommand(asic, "wrChCfg", channel=channel, value=self.config.asicConfig[asic].channelConfig[channel])
				status, _ = self.doAsicCommand(asic, "wrChTCfg", channel=channel, value=self.config.asicConfig[asic].channelTConfig[channel])

			status, _ = self.doAsicCommand(asic, "wrGlobalCfg", value=self.config.asicConfig[asic].globalConfig)
			status, _ = self.doAsicCommand(asic, "wrGlobalTCfg", value=self.config.asicConfig[asic].globalTConfig)

		for dacChannel, hvValue in enumerate(self.config.hvBias):			
			self.setHVDAC(dacChannel, hvValue)

		#self.sendCommand(0x03, bytearray([0x00, 0x00, 0x00, 0x00, 0x00]))
		#self.start()	
		#self.doSync()
		
