# -*- coding: utf-8 -*-
"""
Created on Thu Mar  6 14:10:25 2025

@author: Asterisk
"""
import io
from dds import DDSHeader,texHeaderFromDDS
from tex import _convertFromTex,TEXHeader,_convertToTex
from gdeflate.gdeflate import GDeflate
from pathlib import Path

def forwardConversionTest(filename):
    #From Tex
    dds = _convertFromTex(filename)
    return dds

def conversionTest(filename):
    with open(filename,"rb") as inf:
        otex = inf.read()
    #From Tex
    dds = _convertFromTex(otex)
    prefix = "__S__" if "streaming" in str(filename).lower() else ""
    with open("TestFiles/"+prefix+filename.with_suffix(".dds").name,"wb") as outf:
        outf.write(dds)
    #To Tex
    ddsStream = io.BytesIO(dds)
    header = DDSHeader.parse_stream(ddsStream)
    texDDS = texHeaderFromDDS(header, ddsStream.read())
    tex = TEXHeader.build(texDDS)
    #pass
    #return len(otex) == len(tex) and \
    #        all(((l == r or (0x1c<=ix<=0x1d)) for ix,(l,r) in enumerate(zip(otex,tex))))
    with open("TestFiles/"+prefix+filename.with_suffix(".tex").name,"wb") as outf:
        outf.write(tex)
    ndds = _convertFromTex("TestFiles/"+prefix+filename.with_suffix(".tex").name)
    with open("TestFiles/"+"__"+prefix+filename.with_suffix(".dds").name,"wb") as outf:
        outf.write(ndds)
    return dds == ndds

def singleTest(filename):
    if ".dds" in str(filename):
        with open(filename,"rb") as inf:
            ddsStream = inf
            header = DDSHeader.parse_stream(ddsStream)
            texDDS = texHeaderFromDDS(header, ddsStream.read())
            tex = TEXHeader.build(texDDS)
            pass
    else:
        dds = _convertFromTex(filename)

def roundTripConversion(filename,compress=False):
    with open(filename,"rb") as inf:
        nibread = inf.read(0x1c+0x2)
        nibbles = int.from_bytes(bytearray(nibread)[0x1c:0x1c+0x2],'little')
        inf.seek(0)
        dds = _convertFromTex(inf)
    tex2 = _convertToTex(io.BytesIO(dds),compress=compress,nibbles=nibbles)
    return tex2

def globalDecompression(base,nbase,extension = "*.tex.*"):
    print("Starting Enumeration")
    op,ln = iter,lambda x: 60365
    #op,ln = list,len
    tot = op(base.rglob(extension))
    print("Starting Processing")
    for ix,file in enumerate(tot):
        bdata = roundTripConversion(file,compress=False)
        nfile = nbase / file.relative_to(base)
        nfile.parent.mkdir(parents=True, exist_ok=True)
        with open(nfile,"wb") as outf:
            outf.write(bdata)
        if ix%100 == 0:
            print("%d/%d"%(ix,ln(tot)))

#singleTest(r'C:/Users/Asterisk/Downloads/test.dds')
#raise
    
nbase = Path(r"TestFiles")
base = Path(r"D:\Wilds\re_chunk_000")

globalDecompression(base,nbase,"*.tex*")
raise

singleTest(r'C:/Users/Asterisk/Downloads/Atlas_00001.dds')
raise


fails = []

from collections import defaultdict
base = r"D:\Wilds\re_chunk_000\natives\STM\Art"
streaming = r"D:\Wilds\re_chunk_000\natives\STM\streaming\Art"
tot = list(Path(base).rglob("*.tex.*"))#list()
fails = []
error = []
s = 0 
for ix,file in enumerate(tot):
    equivalent = streaming/file.relative_to(base)
    try: 
        r = conversionTest(file)
        if not r:
            fails.append(file)
        else:
            s += 1
    except Exception as e:
        print(file)
        print(e)
        error.append(file)
    if equivalent.exists():
        try: 
            r = conversionTest(equivalent)
            if not r:
                fails.append(equivalent)
            else:
                s += 1
        except Exception as e:
            print(equivalent)
            print(e)
            error.append(equivalent)
    if ix%100 == 0:
        #print(file)
        lf,le = len(fails),len(error)
        print("%d(%d|%d|%d)/%d"%(ix,s,lf,le,len(tot)))