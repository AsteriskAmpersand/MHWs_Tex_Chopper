# -*- coding: utf-8 -*-
"""
Created on Sun Apr  4 19:24:12 2021

@author: AsteriskAmpersand
"""

import construct as C
from pathlib import Path
import sys
import io

from formatEnum import reverseFormatEnum, packetSizeData, \
                        swizzableFormats,swizzledFormats, \
                        scanlineMinima
from dds import ddsFromTexData,ddsMHRTypeEnum,getBCBPP
#from astc import astcToPureRGBA
from dds import texHeaderFromDDSFile
from streaming import convertStreaming
#from tex_math import (ruD,ulog2,bitCount,linearize,dotDivide,hypersize,#deswizzle,
#                    squareWidth,squareHeight,blockWidth,blockHeight,packetSize,
#                    capSuperBlock)
from tex_math import deswizzle,ruD,ruNX,packetSize,ulog2
from gdeflate.gdeflate import GDeflate
from debugging import DEBUG

mipData = C.Struct(
        "mipOffset" / C.Int64ul,
        "pitch" / C.Int32ul,
        "uncompressedSize" / C.Int32ul,
    )

compressionData = C.Struct(
        "compressedSize" / C.Int32ul,
        "compressedOffset" / C.Int32ul,
    )

swizzleData = C.Struct(
        "swizzleHeightDepth" / C.Int8ul,
        "swizzleHeight" / C.Computed(C.this.swizzleHeightDepth&0xF),
        "swizzleDepth" / C.Computed(C.this.swizzleHeightDepth&0xF0>>4),
        "swizzleWidth" / C.Int8ul,
        "NULL1" / C.Int16ul,
        "SEVEN" / C.Const(7,C.Int16ul),
        "ONE_1" / C.Const(1,C.Int16ul),
    )

swizzleNull = C.Struct(
        "swizzleHeightDepth" / C.Int8ul,
        "swizzleHeight" / C.Computed(C.this.swizzleHeightDepth&0xF),
        "swizzleDepth" / C.Computed(C.this.swizzleHeightDepth&0xF0>>4),
        "swizzleWidth" / C.Int8ul,
        "NULL1" / C.Int16ul,
        "SEVEN" / C.Const(0,C.Int16ul),
        "ONE_1" / C.Const(0,C.Int16ul),
    )

_TEXHeader = C.Struct(
        "magic" / C.CString("utf-8"),
        "version" / C.Int32ul,
        "width" / C.Int16ul,
        "height" / C.Int16ul,
        "depth" / C.Int16ul,
        "imageCount" / C.Int8ul,
        "mipSize" / C.Int8ul,#4
        "mipCount" / C.Computed(lambda this: this.mipSize >> 4),
        "format" / C.Int32ul,
        "swizzleControl" / C.Int32sl,#C.Const(1,C.Int32ul),
        "cubemapMarker" / C.Int32ul,
        "_controlNibbles" / C.Int16ul,
        "controlNibbles" / C.Computed(lambda this: [((this._controlNibbles & 0xf<<(i*4))>>(i*4)) for i in range(4)]),
        #1/0 low/final, 0/8 srgb (but no), 
        #nib[1/2] is copied on streaming, nib[3] is always 0 on final textures
        "NULL0" / C.Int16ul,
        "swizzleData" / swizzleNull,#C.If(lambda ctx: ctx.version in swizzableFormats,C.IfThenElse(lambda ctx: ctx.version in swizzledFormats,swizzleData,swizzleNull)),
        "textureHeaders" / mipData[C.this.mipCount][C.this.imageCount],
        "compressionHeaders" / compressionData[C.this.mipCount][C.this.imageCount],
        "start" /C.Tell,
        "data" / C.GreedyBytes,
    )
TEXHeader = _TEXHeader#.compile()


#Analysis Code Goes Here
    
#End Analysis Code



def expandBlockData(texhead,swizzle):
    texs = []
    for mips,compression in zip(texhead.textureHeaders,texhead.compressionHeaders):
        mipmaps = []
        for mipsTex,compressionTex in zip(mips,compression):
            start = compressionTex.compressedOffset
            end = start + compressionTex.compressedSize
            padding = (mipsTex.uncompressedSize - mipsTex.pitch) if swizzle else 0
            if DEBUG:
                pass
                #print("Tx2: Input Packet Count: %d | Input Length: %d"%(mipsTex.uncompressedSize/packetSize,mipsTex.uncompressedSize))
            #assert len(data) == end-start
            mipmaps.append(texhead.data[start:end]+b"\x00"*padding)
            if DEBUG: print("Tx2: %X %X"%(start,end))
        texs.append(mipmaps)
    return texs

def trim(dimensions,data,blockData,scanline):
    x,y,z = dimensions
    tx,ty,bptx = blockData.tx,blockData.ty,blockData.bytelen
    bytelen = ruD(x,tx)*bptx
    ycount = ruD(y,ty)
    result = b''.join((data[(j+ycount*k)*scanline:bytelen+(j+ycount*k)*scanline] 
                       for k in range(z) for j in range(ycount)))
    #print("_____")
    return result

def BCtoDDS(filename,texhead,blockSize,datablocks):
    width,height,depth = texhead.width,texhead.height,texhead.depth
    mipLevel = lambda x,i: max(1,x>>i)
    #if texhead.swizzleControl == 1:
    
    trimmedBlocks = [trim(tuple(map(lambda x: mipLevel(x,mix),(width,height,depth))),miplevel,blockSize,mipHeader.pitch) 
                         for textureHeader,texture in zip(texhead.textureHeaders,datablocks)
                         for mix,(mipHeader,miplevel) in enumerate(zip(textureHeader,texture))]
    #else:
    #    trimmedBlocks = [mip for texture in datablocks for mip in texture]
    targetFormat = ddsMHRTypeEnum[reverseFormatEnum[texhead.format].upper()]
    mipCount,imageCount = texhead.mipCount, texhead.imageCount
    cubemap = texhead.cubemapMarker!=0
    #cubemap = 0
    if DEBUG: print("Tx2: "+ str(list(map(len,trimmedBlocks))))
    result = ddsFromTexData(height, width, depth, mipCount, imageCount, targetFormat, cubemap, b''.join(trimmedBlocks))
    return result

def toR8G8B8_UNORM(pixelData):
    return b''.join(map(lambda row: b''.join(map(bytes,row)),pixelData))

def ASTCtoDDS(filename,texhead,blockSize,data,f):
    bindata = b""
    for tex in data:
        for targetSize,currentSize,texture,packetTexelSize in tex:
            raise ValueError("ASTC is not supported, use a better image format like DDS")
            #rgba = astcToPureRGBA(texture, *currentSize, *blockSize, "Srgb" in f)
            rgba = None
            binImg = toR8G8B8_UNORM([[column for column in row[:targetSize[0]]] for row in rgba[:targetSize[1]]])
            bindata += binImg
    mipCount,imageCount = texhead.mipCount, texhead.imageCount
    cubemap = texhead.cubemapMarker!=0
    result = ddsFromTexData(texhead.height, texhead.width, texhead.depth, mipCount, imageCount, "R8G8B8A8UNORM", cubemap,bindata)
    return result

def exportBlocks(filename,texhead,blockSize,t,f,data):
    rfilename = filename
    if "ASTC" in t:
        f = ASTCtoDDS(rfilename,texhead,blockSize,data,f)
    elif "BC" in t:
        f = BCtoDDS(rfilename,texhead,blockSize,data)
    else:
        f = BCtoDDS(rfilename,texhead,blockSize,data)
    return f

def convertFromTex(filename):
    filename = Path(filename)
    if not filename.exists():
        filename = filename.with_suffix(".tex.28")
    filedata = _convertFromTex(filename)
    output = Path('.'.join(str(filename).split(".")[:2])).with_suffix(".dds")
    with open(output,"wb") as outf:
        outf.write(filedata)
    return output

#from tex_math import swizzle
#def testDeswizzle(block,*args):
#    return deswizzle(swizzle(deswizzle(block,*args),*args),*args)
decompressor = GDeflate()
def decompress(mipData):
    if len(mipData)<2:
        return mipData
    if mipData[0] == 0x04 and mipData[1] == 0xFB:
        mipData = decompressor.decompress(mipData, num_workers=4)
    #print("Deflation in process")
    return mipData

def _convertFromTex(filename):
    header = TEXHeader.parse_file(filename)
    if DEBUG:
        print("Tx2: "+ str("%d x %d x %d | %d/%d"%(header.width,header.height,header.depth,header.mipCount,header.imageCount)))
    filename = str(filename).replace(".19","").replace(".28","")
    formatString = reverseFormatEnum[header.format]
    datablocks = expandBlockData(header,header.swizzleControl == 1)
    fData = packetSizeData(formatString)
    typing,formatting = fData.formatBase,fData.formatColor
    typing,formatting 
    plainBlocks = [[decompress(mip) for mip in block] for block in datablocks]
    assert(all((all((len(mip) == mipHeader.uncompressedSize*max(1,(header.depth>>ix)) for ix,(mip,mipHeader) in enumerate(zip(image,imgHeader)))) for image,imgHeader in zip(plainBlocks,header.textureHeaders))))
    file = exportBlocks(filename,header,packetSizeData(formatString),typing,formatting,plainBlocks)
    return file

convert = convertFromTex

def _convertToTex(filename,salt = 241106027):
    texHeader = texHeaderFromDDSFile(filename,salt)
    binaryFile = TEXHeader.build(texHeader)
    return binaryFile

def convertToTex(filename,outf = None,salt = 241106027):
    binaryFile = _convertToTex(filename)
    if outf is None:
        outf = str(filename).replace(".dds",".tex.%d"%salt)
    with open(outf,"wb") as tex:
        tex.write(binaryFile)
    return outf



    