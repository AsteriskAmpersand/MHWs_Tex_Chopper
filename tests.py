# -*- coding: utf-8 -*-
"""
Created on Thu Mar  6 14:10:25 2025

@author: Asterisk
"""
import io
from dds import DDSHeader,texHeaderFromDDS
from tex import _convertFromTex,TEXHeader
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
    dds = _convertFromTex(filename)
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