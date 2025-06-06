# -*- coding: utf-8 -*-
"""
Created on Wed Mar 31 03:23:06 2021

@author: AsteriskAmpersand
"""
import math
import construct as C
from formatEnum import formatEnum, reverseFormatEnum, \
                        packetSizeData, scanlineMinima, \
                        swizzableFormats, swizzledFormats
from tex_math import (CoordinateMapping, getSwizzleSizes, product,
                      bitCount, ulog2, ruD, ruNX, packetSize, dotDivide)
from gdeflate.gdeflate import GDeflate, GDeflateFlags, GDeflateCompressionLevel, GDeflateError
# dwPixelFlags
# {
DDPF_ALPHAPIXELS = 0x1
DDPF_ALPHA = 0x2
DDPF_FOURCC = 0x4
DDPF_RGB = 0x40
DDPF_YUV = 0x200
DDPF_LUMINANCE = 0x20000
# }

# dwHeaderFlags
# {
DDSD_CAPS = 0x00000001
DDSD_HEIGHT = 0x00000002
DDSD_WIDTH = 0x00000004
DDSD_PITCH = 0x00000008
DDSD_PIXELFORMAT = 0x00001000
DDSD_MIPMAPCOUNT = 0x00020000
DDSD_LINEARSIZE = 0x00080000
DDSD_DEPTH = 0x00800000
# }

# dwFourCC = {
DDPF_ALPHAPIXELS = 0x00000001
DDPF_FOURCC = 0x00000004
DDPF_RGB = 0x00000040
#            }

# dwCaps1 = {
DDSCAPS_COMPLEX = 0x00000008  # multiple surfaces - Cubemaps
DDSCAPS_TEXTURE = 0x00001000  # mipmaps are usedd
DDSCAPS_MIPMAP = 0x00400000
#    }

# dwCaps2 = {
DDSCAPS2_CUBEMAP = 0x00000200
DDSCAPS2_CUBEMAP_POSITIVEX = 0x00000400
DDSCAPS2_CUBEMAP_NEGATIVEX = 0x00000800
DDSCAPS2_CUBEMAP_POSITIVEY = 0x00001000
DDSCAPS2_CUBEMAP_NEGATIVEY = 0x00002000
DDSCAPS2_CUBEMAP_POSITIVEZ = 0x00004000
DDSCAPS2_CUBEMAP_NEGATIVEZ = 0x00008000
DDSCAPS2_VOLUME = 0x00200000
#    }
DDS_CUBEMAP_ALLFACES = DDSCAPS2_CUBEMAP | DDSCAPS2_CUBEMAP_POSITIVEX | DDSCAPS2_CUBEMAP_NEGATIVEX | +\
    DDSCAPS2_CUBEMAP_POSITIVEY | DDSCAPS2_CUBEMAP_NEGATIVEY | +\
    DDSCAPS2_CUBEMAP_POSITIVEZ | DDSCAPS2_CUBEMAP_NEGATIVEZ

# dwFourCC
DXT1 = "DXT1"  # 0x31545844
DXT2 = "DXT2"  # 0x32545844
DXT3 = "DXT3"  # 0x33545844
DXT4 = "DXT4"  # 0x34545844
DXT5 = "DXT5"  # 0x35545844
ATI1 = "ATI1"
ATI2 = "ATI2"
BC4U = "BC4U"
BC4S = "BC4S"
BC5U = "BC5U"
BC5S = "BC5S"
DX10 = "DX10"  # 0x30315844
CCCC = "CCCC"
NULL = "\x00\x00\x00\x00"
# Int version of "DXT1", ..., "DX10"

# dwResourceDimension
D3D10_RESOURCE_DIMENSION_UNKNOWN = 0
D3D10_RESOURCE_DIMENSION_BUFFER = 1
D3D10_RESOURCE_DIMENSION_TEXTURE1D = 2
D3D10_RESOURCE_DIMENSION_TEXTURE2D = 3
D3D10_RESOURCE_DIMENSION_TEXTURE3D = 4

DDS_PIXELFORMAT = C.Struct(
    "dwSize" / C.Const(32, C.Int32ul),
    "dwFlags" / C.Int32ul,  # RGB #PixelFlags
    # CCCC if compressed, DXT1 to DXT5 for DXTn Compression
    "dwFourCC" / C.PascalString(C.Computed(4), "utf-8"),
    "dwRGBBitCount" / C.Int32ul,
    "dwRBitMask" / C.Int32ul,
    "dwGBitMask" / C.Int32ul,
    "dwBBitMask" / C.Int32ul,
    "dwABitMask" / C.Int32ul,
)

DX10_Header = C.Struct(
    "dxgiFormat" / C.Int32ul,
    "resourceDimension" / C.Int32ul,
    "miscFlag" / C.Int32ul,
    "arraySize" / C.Int32ul,
    "miscFlags2" / C.Int32ul,
)

DDSHeader = C.Struct(
    "magic" / C.Const(0x20534444, C.Int32ul),
    "dwSize" / C.Const(124, C.Int32ul),
    "dwFlags" / C.Int32sl,  # 07100A00 #DW Header Flags
    "dwHeight" / C.Int32ul,
    "dwWidth" / C.Int32ul,
    # size of data as packed integer (width*height * bpp/8)
    "dwPitchOrLinearSize" / C.Int32ul,
    # Block Compressed: max( 1, ((width+3)/4) ) * block-size
    # R8G8_B8G8, G8R8_G8B8, legacy UYVY-packed: ((width+1) >> 1) * 4
    #Other ( width * bits-per-pixel + 7 ) / 8
    "dwDepth" / C.Int32ul,  # Only used for volumetric textures
    "dwMipMapCount" / C.Int32ul,
    "dwReserved1" / C.Int32ul[11],  # 0s
    "ddpfPixelFormat" / DDS_PIXELFORMAT,  # typeMagic
    "ddsCaps" / C.Int32ul[4],
    "dwReserved2" / C.Int32ul,
    "dx10Header" / C.If(C.this.ddpfPixelFormat.dwFourCC ==
                        "DX10", DX10_Header),
)
# If DX10 is set on the pixel format DX10_Header follows

ddsTypeEnum = ["UNKNOWN", "R32G32B32A32_TYPELESS", "R32G32B32A32_FLOAT", "R32G32B32A32_UINT",
               "R32G32B32A32_SINT", "R32G32B32_TYPELESS", "R32G32B32_FLOAT", "R32G32B32_UINT", "R32G32B32_SINT",
               "R16G16B16A16_TYPELESS", "R16G16B16A16_FLOAT", "R16G16B16A16_UNORM", "R16G16B16A16_UINT",
               "R16G16B16A16_SNORM", "R16G16B16A16_SINT", "R32G32_TYPELESS", "R32G32_FLOAT",
               "R32G32_UINT", "R32G32_SINT", "R32G8X24_TYPELESS", "D32_FLOAT_S8X24_UINT", "R32_FLOAT_X8X24_TYPELESS",
               "X32_TYPELESS_G8X24_UINT", "R10G10B10A2_TYPELESS", "R10G10B10A2_UNORM", "R10G10B10A2_UINT",
               "R11G11B10_FLOAT", "R8G8B8A8_TYPELESS", "R8G8B8A8_UNORM", "R8G8B8A8_UNORM_SRGB", "R8G8B8A8_UINT",
               "R8G8B8A8_SNORM", "R8G8B8A8_SINT", "R16G16_TYPELESS", "R16G16_FLOAT", "R16G16_UNORM",
               "R16G16_UINT", "R16G16_SNORM", "R16G16_SINT", "R32_TYPELESS", "D32_FLOAT", "R32_FLOAT",
               "R32_UINT", "R32_SINT", "R24G8_TYPELESS", "D24_UNORM_S8_UINT", "R24_UNORM_X8_TYPELESS", "X24_TYPELESS_G8_UINT",
               "R8G8_TYPELESS", "R8G8_UNORM", "R8G8_UINT", "R8G8_SNORM", "R8G8_SINT", "R16_TYPELESS", "R16_FLOAT",
               "D16_UNORM", "R16_UNORM", "R16_UINT", "R16_SNORM", "R16_SINT", "R8_TYPELESS", "R8_UNORM",
               "R8_UINT", "R8_SNORM", "R8_SINT", "A8_UNORM", "R1_UNORM", "R9G9B9E5_SHAREDEXP", "R8G8_B8G8_UNORM",
               "G8R8_G8B8_UNORM", "BC1_TYPELESS", "BC1_UNORM", "BC1_UNORM_SRGB", "BC2_TYPELESS", "BC2_UNORM",
               "BC2_UNORM_SRGB", "BC3_TYPELESS", "BC3_UNORM", "BC3_UNORM_SRGB", "BC4_TYPELESS", "BC4_UNORM",
               "BC4_SNORM", "BC5_TYPELESS", "BC5_UNORM", "BC5_SNORM", "B5G6R5_UNORM", "B5G5R5A1_UNORM",
               "B8G8R8A8_UNORM", "B8G8R8X8_UNORM", "R10G10B10_XR_BIAS_A2_UNORM", "B8G8R8A8_TYPELESS",
               "B8G8R8A8_UNORM_SRGB", "B8G8R8X8_TYPELESS", "B8G8R8X8_UNORM_SRGB", "BC6H_TYPELESS",
               "BC6H_UF16", "BC6H_SF16", "BC7_TYPELESS", "BC7_UNORM", "BC7_UNORM_SRGB", "AYUV", "Y410",
               "Y416", "NV12", "P010", "P016", "420_OPAQUE", "YUY2", "Y210", "Y216", "NV11", "AI44", "IA44",
               "P8", "A8P8", "B4G4R4A4_UNORM"]
ddsTypeEnum = [val.upper().replace("_", "") for val in ddsTypeEnum]
ddsMHRTypeEnum = dict(map(lambda x: (x.replace("_", ""), x), ddsTypeEnum))
ddsTypeFromName = {n: ix for ix, n in enumerate(ddsTypeEnum)}


def getBCBPP(BC):
    BC = BC.upper()
    if "BC1" in BC:
        return 8
    if "BC2" in BC:
        return 16
    if "BC3" in BC:
        return 16
    if "BC4" in BC:
        return 8
    if "BC5" in BC:
        return 16
    if "BC6H" in BC:
        return 16
    if "BC7" in BC:
        return 16


ddsBpps = {
    "Unknown": 0,
    "R32G32B32A32_Typeless": 128,    "R32G32B32A32_Float": 128,   "R32G32B32A32_UInt": 128,
    "R32G32B32A32_SInt": 128,        "R32G32B32_Typeless": 96,    "R32G32B32_Float": 96,
    "R32G32B32_UInt": 96,            "R32G32B32_SInt": 96,        "R16G16B16A16_Typeless": 64,
    "R16G16B16A16_Float": 64,        "R16G16B16A16_UNorm": 64,    "R16G16B16A16_UInt": 64,
    "R16G16B16A16_SNorm": 64,        "R16G16B16A16_SInt": 64,     "R32G32_Typeless": 64,
    "R32G32_Float": 64,              "R32G32_UInt": 64,           "R32G32_SInt": 64,
    "R32G8X24_Typeless": 64,         "D32_Float_S8X24_UInt": 64,  "R32_Float_X8X24_Typeless": 64,
    "X32_Typeless_G8X24_UInt": 64,   "R10G10B10A2_Typeless": 32,  "R10G10B10A2_UNorm": 32,
    "R10G10B10A2_UInt": 32,          "R11G11B10_Float": 32,       "R8G8B8A8_Typeless": 32,
    "R8G8B8A8_UNorm": 32,            "R8G8B8A8_UNorm_sRGB": 32,   "R8G8B8A8_UInt": 32,
    "R8G8B8A8_SNorm": 32,            "R8G8B8A8_SInt": 32,         "R16G16_Typeless": 32,
    "R16G16_Float": 32,              "R16G16_UNorm": 32,          "R16G16_UInt": 32,
    "R16G16_SNorm": 32,              "R16G16_SInt": 32,           "R32_Typeless": 32,
    "D32_Float": 32,                 "R32_Float": 32,             "R32_UInt": 32,
    "R32_SInt": 32,                  "R24G8_Typeless": 32,        "D24_UNorm_S8_UInt": 32,
    "R24_UNorm_X8_Typeless": 32,     "X24_Typeless_G8_UInt": 32,  "R8G8_Typeless": 16,
    "R8G8_UNorm": 16,                "R8G8_UInt": 16,             "R8G8_SNorm": 16,
    "R8G8_SInt": 16,                 "R16_Typeless": 16,          "R16_Float": 16,
    "D16_UNorm": 16,                 "R16_UNorm": 16,             "R16_UInt": 16,
    "R16_SNorm": 16,                 "R16_SInt": 16,              "R8_Typeless": 8,
    "R8_UNorm": 8,                   "R8_UInt": 8,                "R8_SNorm": 8,
    "R8_SInt": 8,                    "A8_UNorm": 8,               "R1_UNorm": 1,
    "R9G9B9E5_SharedExp": 32,        "R8G8_B8G8_UNorm": 16,       "G8R8_G8B8_UNorm": 16,
    "B5G6R5_UNorm": 16,              "B5G5R5A1_UNorm": 16,        "B8G8R8A8_UNorm": 32,
    "B8G8R8X8_UNorm": 32,            "B8G8R8A8_Typeless": 32,     "R10G10B10_XR_Bias_A2_UNorm": 32,
    "B8G8R8A8_UNorm_sRGB": 32,       "B8G8R8X8_Typeless": 32,     "B8G8R8X8_UNorm_sRGB": 32,
    "AYUV": 32,                      "Y410": 10,                  "Y416": 16,
    "NV12": 12,                      "P010": 10,                  "P016": 16,
    "Format_420_Opaque": 20,         "YUY2": 16,                  "Y210": 10,
    "Y216": 16,                      "NV11": 11,                  "AI44": 44,
    "IA44": 44,                      "P8": 8,                     "A8P8": 16,
    "B4G4R4A4_UNorm": 16,            "P208": 8,                   "V208": 8,
    "V408": 8,
    **{typing: (8*getBCBPP(typing))//16 for typing in ddsTypeEnum if "BC" in typing}
}
ddsBpps = {key.upper().replace("_", ""): val for key, val in ddsBpps.items()}

DDS_RESOURCE_MISC_TEXTURECUBE = 0x4


def ddsFromTexData(h, w, z, mmc, count, targetFormat, cubemap, data):
    bpp = ddsBpps[targetFormat.upper()]
    header = {"magic": 0x20534444,
              "dwSize": 124,
              # check for absence of mip maps
              "dwFlags": DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT | DDSD_MIPMAPCOUNT | DDSD_LINEARSIZE | DDSD_DEPTH*(z>1),
              "dwHeight": h,
              "dwWidth": w,
              # Spec ( w * bpp + 7 ) // 8,
              "dwPitchOrLinearSize": (w*h*bpp)//8,
              "dwDepth": z,
              "dwMipMapCount": mmc,
              "dwReserved1": [0]*11,
              "ddpfPixelFormat": {
                  "dwSize": 32,
                  "dwFlags": DDPF_FOURCC,
                  "dwFourCC": DX10,  # actually check for outliers
                  "dwRGBBitCount": 0,
                  "dwRBitMask": 0,
                  "dwGBitMask": 0,
                  "dwBBitMask": 0,
                  "dwABitMask": 0,
              },
              # check for absence of mip maps
              "ddsCaps": [DDSCAPS_TEXTURE | DDSCAPS_MIPMAP | (DDSCAPS_COMPLEX if cubemap else 0), (DDS_CUBEMAP_ALLFACES if cubemap else 0), 0, 0],
              "dwReserved2": 0,
              "dx10Header": {
                  "dxgiFormat": ddsTypeFromName[targetFormat],
                  "resourceDimension": D3D10_RESOURCE_DIMENSION_TEXTURE2D if z < 2 else D3D10_RESOURCE_DIMENSION_TEXTURE3D,
                  "miscFlag": DDS_RESOURCE_MISC_TEXTURECUBE if cubemap else 0,
                  "arraySize": count//(6 if cubemap else 1),
                  "miscFlags2": 0,  # should maybe probably actually be calculated
              },  # check for outliers
              }
    # print(header)
    return DDSHeader.build(header)+data


"""
        if (MAKEFOURCC('A', 'T', 'I', '1') == ddpf.fourCC) return DXGI_FORMAT_BC4_UNORM;
        if (MAKEFOURCC('B', 'C', '4', 'U') == ddpf.fourCC) return DXGI_FORMAT_BC4_UNORM;
        if (MAKEFOURCC('B', 'C', '4', 'S') == ddpf.fourCC) return DXGI_FORMAT_BC4_SNORM;

        if (MAKEFOURCC('A', 'T', 'I', '2') == ddpf.fourCC) return DXGI_FORMAT_BC5_UNORM;
        if (MAKEFOURCC('B', 'C', '5', 'U') == ddpf.fourCC) return DXGI_FORMAT_BC5_UNORM;
        if (MAKEFOURCC('B', 'C', '5', 'S') == ddpf.fourCC) return DXGI_FORMAT_BC5_SNORM;
"""

legacyMapping = {
    DXT1: "BC1UNORM",
    DXT2: "BC2UNORM",
    DXT3: "BC2UNORM_SRGB",
    DXT4: "BC3UNORM",
    DXT5: "BC3UNORM_SRGB",
    ATI1: "BC4UNORM",
    ATI2: "BC5UNORM",
    BC4U: "BC4UNORM",
    BC4S: "BC4SNORM",
    BC5U: "BC5UNORM",
    BC5S: "BC5SNORM",

}


def buildFormatString(header):
    pixelFormat = header.ddpfPixelFormat
    fourCC = pixelFormat.dwFourCC
    if fourCC == "DX10":
        return ddsTypeEnum[header.dx10Header.dxgiFormat].replace("_", "")
    elif fourCC in legacyMapping:
        return legacyMapping[fourCC].replace("_", "")
    else:
        Rbc = bitCount(pixelFormat.dwRBitMask)
        Gbc = bitCount(pixelFormat.dwGBitMask)
        Bbc = bitCount(pixelFormat.dwBBitMask)
        Abc = bitCount(pixelFormat.dwABitMask)
        R = (pixelFormat.dwRBitMask, "R", "%d" % Rbc)
        G = (pixelFormat.dwGBitMask, "G", "%d" % Gbc)
        B = (pixelFormat.dwBBitMask, "B", "%d" % Bbc)
        A = (pixelFormat.dwABitMask, "A", "%d" % Abc)
        RGBA = ''.join([channel_code + bit_count for mask,
                        channel_code, bit_count in sorted([R, G, B, A]) if mask])
        knownBits = sum([Rbc, Gbc, Bbc, Abc])
        if knownBits < pixelFormat.dwRGBBitCount:
            fill = "A" if RGBA[0] == "R" else "X"
            RGBA += "%s%d" % (fill, pixelFormat.dwRGBBitCount - knownBits)
        return RGBA+"UNORM"


def trim(binarydata):
    return binarydata.rstrip(b"\x00")

compressor = GDeflate()
class TextureData():
    def __init__(self, header, version=241106027):
        self.mipCount = header.dwMipMapCount
        self.cubemap = (header.ddsCaps[1] & DDSCAPS2_CUBEMAP != 0)*1
        self.version = version
        self.swizzable = self.version in swizzableFormats
        self.swizzled = self.version in swizzledFormats
        self.imageCount = 1 if not header.ddpfPixelFormat.dwFourCC == "DX10" else header.dx10Header.arraySize * \
            (6 if self.cubemap else 1)
        self.formatName = buildFormatString(header)
        self.x, self.y = header.dwWidth, header.dwHeight
        self.depth = header.dwDepth
        self.size = self.x, self.y
        self.formatData = packetSizeData(self.formatName)

    def padding(self,image,ddsSl,capSl,linecount):
        result = b''
        for ix in range(linecount):
            imgData = image[ix*ddsSl:(ix+1)*ddsSl]
            pad = b'\x00'*(capSl-ddsSl)
            result += imgData + pad
        return result
            
    def parselData(self, data,compress=True):
        miptex = []
        offset = 0
        minima = scanlineMinima(self.formatName)
        for tex in range(self.imageCount):
            mips = []
            for mip in range(self.mipCount):
                x,y = ruD(self.x, 2**mip), ruD(self.y, 2**mip)
                z = ruD(self.depth, 2**mip)
                xcount, ycount = ruD(x, self.formatData.tx), ruD(y, self.formatData.ty)
                mpacketSize = ruD(packetSize, round(
                    product(dotDivide(self.formatData.pixelPerPacket, self.formatData.texelSize))))
                # texelSize = packetTexelPacking and mTexelSize = tx,ty
                bytelen = xcount*ycount*z*mpacketSize
                mipmap = data[offset:offset+bytelen]
                
                capcomScanline = ruNX(xcount*mpacketSize,minima)
                
                ddsScanline = mpacketSize * xcount
                paddedMipmap = self.padding(mipmap,ddsScanline,capcomScanline,ycount*z)
                uncompressedSize = capcomScanline * ycount
                if x * y >= 64 and compress:
                    try:
                        compressedPaddedMipmap = compressor.compress(paddedMipmap,GDeflateCompressionLevel.BEST_RATIO)
                        s = compressor.get_uncompressed_size(compressedPaddedMipmap)
                        if len(compressedPaddedMipmap) > s:
                            compressedPaddedMipmap = paddedMipmap
                    except:
                        compressedPaddedMipmap = paddedMipmap
                else: 
                    compressedPaddedMipmap = paddedMipmap
                mipData = compressedPaddedMipmap, uncompressedSize, len(compressedPaddedMipmap), capcomScanline
                parsel = (mipData, (xcount, ycount))
                mips.append(parsel)
                offset += bytelen
                #assert len(parsel[0]) == bytelen
            miptex.append(mips)#add uncompressed and compressed size, divide uncompressed by z for that mip
        self.miptex = miptex
        self.packParsels()
        return self.build()

    def packParsels(self):
        mipstride = 0x10
        compressstride = 0x8
        baseHeader = 0x28
        mipbase = baseHeader + mipstride*self.imageCount*self.mipCount
        offset = 0x0
        mipoffset = 0x0
        tex = []
        mipImageHeaders = []
        compressImageHeaders = []
        for texture in self.miptex:
            mips = []
            mipHeaders = []
            compressHeaders = []
            for mip, (mipData, texelCount) in enumerate(texture):
                mipmap,uncompressedSize,compressedSize,scanlineSize = mipData
                tx, ty = texelCount
                mips.append(mipmap)
                mipheader = {
                    "mipOffset": mipbase+mipoffset,
                    "uncompressedSize": uncompressedSize,
                    "pitch": scanlineSize,
                }
                compressheader = {
                    "compressedSize":compressedSize,
                    "compressedOffset":offset,
                }
                offset += compressedSize
                mipoffset += uncompressedSize
                mipHeaders.append(mipheader)
                compressHeaders.append(compressheader)
            tex.append(mips)
            mipImageHeaders.append(mipHeaders)
            compressImageHeaders.append(compressHeaders)
        self.packedParsels = tex
        self.mheaders = mipImageHeaders
        self.cheaders = compressImageHeaders
        return

    def build(self):
        swizzable, swizzled = self.swizzable, self.swizzled
        if swizzable:
            counts = (self.mipCount << 12) | self.imageCount
        else:
            counts = (self.imageCount << 8) + self.mipCount
        formatting = formatEnum[self.formatName]
        header = {"magic": "TEX", "version": self.version, 
                  "width": self.x, "height": self.y, "depth": self.depth,
                  "imageCount":self.imageCount,
                  "mipSize":self.mipCount<<4,
                  "format": formatting, 
                  "swizzleControl": -1, 
                  "cubemapMarker": self.cubemap*4, "_controlNibbles": 0, 
                  "NULL0": 0,
                  "textureHeaders": self.mheaders,
                  "compressionHeaders": self.cheaders} 
        header["data"] = b''.join(
            map(lambda x: b''.join(x), self.packedParsels))
        header["swizzleData"] = {"swizzleHeightDepth":0,
                                "swizzleWidth":0,
                                "NULL1":0,
                                "SEVEN":0,
                                "ONE_1":0,
                                }
        return header

def texHeaderFromDDS(header, data, version=241106027, compress=True):
    td = TextureData(header, version)
    return td.parselData(data,compress)


def texHeaderFromDDSFile(stream, salt,compress=True):
    header = DDSHeader.parse_stream(stream)
    data = stream.read()
    return texHeaderFromDDS(header, data, salt, compress)
    