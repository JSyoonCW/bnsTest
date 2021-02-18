# -*- coding: utf-8 -*-
"""
Created on Wed Feb 17 09:55:51 2021

@author: NB26
"""
from io import BytesIO
import easygui
import struct 

class BinDecoding:

    def __init__(self,binpath, is64=False):
        #class
        self.content = Content()
        self.headlist = HeadList()
        self.lists = []
        
        self.is64 = is64
        self.savepath = self.save_path(binpath)
        self.bf = open(binpath,'rb')
        
        #class byte
        self.content_bytes = None
        self.headlist_bytes = None
        
    def save_path(self,path):
        
        filename = path.split('\\')
        name = filename[-1].split('.')
        name[0] = name[0] + '-'
        rename = ''.join(name)
        filename[-1] = rename
        
        return ''.join(filename)
    
    def load(self):
        if not self.is64:
            #content read
            self.content_bytes = self.bf.read(25) 
            listcount = struct.unpack('i',self.content.dec_content(self.content_bytes))[0]
            
            #headlist read
            self.headlist_bytes = self.bf.read(74)
            if(listcount < 20):
                self.headlist.complement = True
            self.headlist.dec_headlist(self.headlist_bytes,self.bf)
            
            #lists read
            for i in range(listcount):
                self.lists.append(Lists())
                self.lists[i].dec_lists(self.bf.read(11), self.bf)
                

        
class Content:
    def __init__(self):
        self.signature = None
        self.version = None
        self.unknown = None
        self.listcount = None
        
    def dec_content(self,bytes_):
        self.signature = bytes_[0:7] #8byte
        self.version = bytes_[8:11] #4byte
        self.unknown = bytes_[12:20] #9byte
        self.listcount = bytes_[21:] #4byte
        
        return self.listcount

class HeadList:
    def __init__(self):
        self.size1 = None
        self.size2 = None
        self.size3 = None
        self.padding = None
        self.data = None
        
        self.complement = False
        
    def set_complement(self, comp):
        self.complement = comp
        
    def dec_headlist (self,bytes_, bf):
        self.size1 = bytes_[0:3]
        self.size2 = bytes_[4:7]
        self.size1 = bytes_[8:11]
        self.padding = bytes_[12:]
        if self.complement == False:
            self.data = bf.read(struct.unpack('i',self.size)[0])
            #print(len(self.data))
            #print(self.size1)
        
        return self.data
        
class Lists:
    def __init__(self):
        self.unknown1 = None #1byte
        self.ID = None #int 2byte
        self.unknown2 = None #int 2byte
        self.unknown3 = None #int 2byte
        self.size = None #4byte
        
        self.collection = Collection()
        
    def dec_lists(self,bytes_,bf):
        self.unknown1 = bytes_[0] #1byte
        self.ID = bytes_[1:2] #int 2byte
        self.unknown2 = bytes_[3:4] #int 2byte
        self.unknown3 = bytes_[5:6] #int 2byte
        self.size = bytes_[7:] #4byte
        
        startpos = bf.tell()
        
        self.collection.dec_collection(bf)
        
        endpos = bf.tell()
        
        if (startpos + struct.unpack('i', self.size)[0] != endpos):
            bf.seek(startpos + struct.unpack('i', self.size)[0])
        #write 시 size 재계산
    
    def get_bytes(self):
        return_bytes = self.unknown1
        return_bytes = return_bytes + self.ID
        return_bytes = return_bytes + self.unknown2
        return_bytes = return_bytes + self.unknown3
        col_bytes = self.collection.get_bytes()
        size = len(col_bytes)
        return_bytes = return_bytes + struct.pack('i',size)
        return_bytes = return_bytes + col_bytes
        
class Collection:
    def __init__(self):
        self.bytes_list = [] # 0 compressed
        self.compressed = None
        self.deprecated = None
        
        self.archive = Archive()
        self.loose = Loose()
    def dec_collection(self, bf):
        self.compressed = bf.read(1)
        
        if struct.unpack('?',self.compressed)[0]:
            if self.compressed>struct.pack('b',1):
                bf.seek(bf.tell() - 1)
            #archive read
            self.archive.dec_archive(bf)
            self.loose = None
            if self.compressed>1:
                self.deprecated = bf.read(1)
        else:
            self.loose.dec_loose(bf)
            self.archive = None
            
    def get_bytes(self):
        returenbyte = self.compressed
        if struct.unpack('?',self.compressed)[0]:
            if self.compressed>1:
                returenbyte = []
            #archive read
            returenbyte = returenbyte + self.archive.get_bytes()
            if self.compressed>1:
                returenbyte = returenbyte + self.deprecated
        else:
            returenbyte = returenbyte + self.loose.get_bytes()
            
        return returenbyte
        
class Archive:
    def __init__(self):
        self.archive_count = None
        self.unknown = None
        self.archlist = []       
        
    def dec_archive(self,bf):
        self.archive_count = bf.read(4)
        self.unknown = bf.read(2)

        for i in range(struct.unpack('i',self.archive_count)[0]):
            self.archlist.append(SubArch())
            self.archlist[i].dec_subarch(bf)
            
        return
    def get_bytes(self):
        returnbytes = self.archive_count
        returnbytes = returnbytes + self.unknown
        for i in range(len(self.archlist)):
            returnbytes = returnbytes + self.archlist[i].get_bytes()
        return
class Loose:
    def __init__(self):
        self.FieldCountUnfixed = None
        self.FieldCount = None
        self.SizeFields = None
        self.SizeLookup = None
        self.Unknown = None
        self.Fields = []
        self.sizePadding = None
        self.padding = None
        self.Lookup = None
        
        self.Is64 = False
        
        return
    def dec_loose(self,bf):
        self.FieldCount = bf.read(4) #int 4 byte
        self.FieldCountUnfixed = struct.unpack('i',self.FieldCount)[0]
        self.SizeFields = bf.read(4) #int
        self.SizeLookup = bf.read(4) #int
        self.Unknown = bf.read(1)
        
        if (struct.unpack('i',self.FieldCount)[0] > 0 and struct.unpack('i',self.SizeFields)[0] <= 0):
            curpos = bf.tell()
            bf.seek(curpos-13)
            self.FieldCount = bf.read(8)
            self.FieldCountUnfixed = struct.unpack('i',self.FieldCount)[0]
            self.SizeFields = bf.read(4)
            self.SizeLookup = bf.read(4)
            self.Unknown = bf.read(1)
            self.Is64 = True
            
        startpos = bf.tell()
        expectedpos = startpos + struct.unpack('i',self.SizeFields)[0]
        
        for i in range(self.FieldCountUnfixed):
            curpos = bf.tell()
            if curpos >= expectedpos:
                self.FieldCount = struct.pack('i',i)
                bf.seek(expectedpos)
                break
            self.Fields.append(FieldTable())
            self.Fields[i].dec_FieldTable(bf)
        
        curpos = bf.tell()
        self.sizePadding = expectedpos - curpos
        
        if self.sizePadding < 0:
            return
        if self.sizePadding > 0:
            self.padding = bf.read(self.sizePadding)
        
        self.Lookup = Lookup(struct.unpack('i',self.SizeLookup)[0])
        self.Lookup.dec_Lookup(bf)

        return
    def get_bytes(self):
        return

class SubArch:
    def __init__(self):
        self.StartAndEndFileID = None #16 byte
        self.SizeCompressed = None # 2byte
        self.DataCompressed = None
        self.SizeDecompressed = None #2byte
        self.DataDecompressed = None
        self.FieldLookupCount = None #4byte
        self.DataOffset = None
        
        #class list
        self.Field = []
        self.Lookup = []
        
    def dec_subarch(self, bf):
        self.StartAndEndFileID = bf.read(16)
        self.SizeCompressed = bf.read(2)
        self.DataCompressed = bf.read(struct.unpack('h',self.SizeCompressed)[0])  
        self.SizeDecompressed = bf.read(2)
        
        if struct.unpack('h',self.SizeCompressed)[0] < 0:
            print('sub archaive sizcompressed check')
            
        self.DataDecompressed = bf.read(struct.unpack('h',self.SizeDecompressed)[0])
        self.FieldLookupCount = bf.read(4)
        self.Field = FieldTable()
        self.Lookup = Lookup()
        
        mbf = BytesIO(self.DataDecompressed)
        self.DataOffset = bf.read(2)
        for i in range(1,struct.unpack('i',self.FieldLookupCount)[0]):
            mbf.seek(struct.unpack('h',self.DataOffset)[0])
            
            self.Field.append(FieldTable())
            self.Field.dec_FieldTable(mbf)
            #Todo
        return
    def get_bytes(self):
        return
    
class FieldTable:
    def __init__(self):
        return
    def dec_FieldTable(self,br):
        return
class Lookup:
    def __init__(self,Size=0):
        return
    def dec_Lookup(self,bf):
        return
if __name__ == '__main__':
    binpath = easygui.fileopenbox(msg='select localfile.bin or localfile64.bin', default=r"C:\*")
    filename = binpath.split('\\')[-1]
    
    is64 = False
    
    if '64' in filename:
        is64 = True
    
    bd = BinDecoding(binpath,is64)
    bd.load()
        
    