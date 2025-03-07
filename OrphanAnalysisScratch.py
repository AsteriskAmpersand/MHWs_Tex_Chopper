cat = {}
fmt = {}
base = r"D:\Wilds\re_chunk_000\natives\STM\Art"
streaming = r"D:\Wilds\re_chunk_000\natives\STM\streaming\Art"
tot = list(Path(base).rglob("*.tex.*"))
for ix,file in enumerate(tot):
    equivalent = streaming/file.relative_to(base)
    with open(file,"rb") as inf:
        t = TEXHeader.parse(inf.read())
    k = list(map(lambda x: "%X"%x,t.controlNibbles)) + ["|"]
    if not equivalent.exists():
        #print(file)
        #print(k,reverseFormatEnum[t.format],file)
        continue
    with open(equivalent,"rb") as inf:
        t2 = TEXHeader.parse(inf.read())
    k = ''.join(k+list(map(lambda x: "%X"%x,t2.controlNibbles)))
    #print(t.streaming,t2.streaming)
    #print(t.base,t2.base)
    #print()
    if k not in cat:
        cat[k] = []
        #print(k)
    if (k,t.format) not in fmt:
        fmt[(k,t.format)] = []
        print(k,t.compressed,reverseFormatEnum[t.format],file)
    m,m2 = t.mipCount,t2.mipCount
    d = m2-m
    bd = ((t2.width//t.width).bit_length())-1
    ds = [m,m2,d,bd,t.compressed*1,t.width,t.height,t.width>>(t.mipCount-1),t.height>>(t.mipCount-1)]
    cat[k].append((reverseFormatEnum[t.format],file,ds))
    fmt[(k,t.format)].append((reverseFormatEnum[t.format],file,ds))
    if ix%100 == 0:
        print("%d/%d"%(ix,len(tot)))
with open(r"TexAnalysis.csv","w") as outf:
    outf.write(",".join(["nib","nib0","nib1","nib2","nib3","format","path","type","lowMipC","highMipC","mipCdiff","byteDif","compressed","lowX","lowY","minX","minY"]))
    outf.write("\n")
    for nib in cat.keys():
        for f,p,ds in cat[nib]:
            m,m2,d,bd,t,x,y,mx,my = ds
            extract = lambda x: p.split("_").find(".tex.")
            outf.write(','.join([nib,nib[0],nib[1],nib[2],nib[3],f,str(p),p.stem.split("_")[-1].split(".")[0],
                                 *list(map(str,[m,m2,d,bd,t,x,y,mx,my]))]))
            outf.write("\n")
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            

from dds import ddsBpps
from formatEnum import packetSizeData,scanlineMinima
from tex_math import (CoordinateMapping, getSwizzleSizes,
                      bitCount, ulog2, ruD, ruNX, packetSize, dotDivide)

def product(listing):
    cur = 1
    for element in listing:
        cur *= element
    return cur

def mpacket(formatName,x,y,ix):
    _,tx,ty,_ = formatParse(formatName)
    _,mtx,mty,_ = formatTexelParse(formatName)
    return ruD(packetSize, round(
        product(dotDivide((tx,ty), (mtx,mty)))))



def scs(formatName,x,y,ix):
    _, tx, ty, _ = formatTexelParse(formatName)
    _, mtx, mty, _ = formatParse(formatName)
    texelSize = tx,ty
    mTexelSize = mtx,mty
    xcount, ycount = ruD(
        ruD(x, 2**ix), mtx), ruD(ruD(y, 2**ix), mty)
    mpacketSize = ruD(packetSize, round(
                        product(dotDivide(texelSize, mTexelSize))))
    minima = scanlineMinima(formatName)
    scanlineSize = ruNX(xcount*mpacketSize,minima)
    virtualSize = scanlineSize*ycount
    return scanlineSize,virtualSize

fts = set()
miprainbow = []
satan = {}
def analysis(tex,filepath,filelen):
    prevO = 0
    prevS = 0
    pitch = None
    mp = pitch
    aligned = True
    pow2 = lambda x: (1<<(x.bit_length()-1) == x)
    exotic = (not pow2(tex.width)) or (not pow2(tex.height))
    formatName = reverseFormatEnum[tex.format]
    for im in tex.textureHeaders:
        for ix,mip in enumerate(im):
            x,y = tex.width, tex.height
            scanlineSize,byteCount = scs(formatName,x,y,ix)
            if mip.pitch != scanlineSize:
                print(file)
                print("Uncompressed Pitch {%s} [%d] Error %d/%d"%(formatName,ix,mip.pitch,scanlineSize))
                #raise
            if mip.uncompressedSize != byteCount:
                print(file)
                print("Uncompressed Mipmap {%s} [%d] Error %d/%d"%(formatName,ix,mip.uncompressedSize,byteCount))
                #raise
            if mip.uncompressedSize % mip.pitch != 0:
                print(file)
                print("Pitch Indivisibility %d/%d"%(mip.uncompressedSize,mip.pitch))
            mp = min(mp,mip.pitch) if mp is not None else mip.pitch
            miprainbow.append([filepath,formatName,x>>ix,y>>ix,mip.pitch,*packetSizeData(formatName),scanlineSize])
            if formatName not in satan or mip.pitch < satan[formatName]:
                satan[formatName] = mip.pitch
    fts.add(formatName)
    for im in tex.compressionHeaders:
        for c in im:
            if prevO + prevS != c.compressedOffset:
                aligned = False
                print(file)
                print("Misalignment %d/%d"%(prevO+prevS,c.compressedOffset))
            prevO = c.compressedOffset
            prevS = c.compressedSize
    if tex.start+prevO+prevS != filelen:
        aligned = False
        print(file)
        print("File Size Misalignment %d/%d"%(tex.start+prevO+prevS,filelen))
    return[tex.width,tex.height,tex.depth,tex.imageCount,tex.mipCount,reverseFormatEnum[tex.format],
           tex.cubemapMarker,tex.controlNibbles[0],tex.controlNibbles[1],tex.controlNibbles[2],tex.controlNibbles[3],
           aligned,exotic,mp]
        

result = []
base = r"D:\Wilds\re_chunk_000\natives\STM\Art"
streaming = r"D:\Wilds\re_chunk_000\natives\STM\streaming\Art"
tot = list(Path(base).rglob("*.tex.*"))#list()
for ix,file in enumerate(tot):
    equivalent = streaming/file.relative_to(base)
    with open(file,"rb") as inf:
        d = inf.read()
        t = TEXHeader.parse(d)
        a = analysis(t,file,len(d))
        result.append([file,file.stem]+a)
    k = list(map(lambda x: "%X"%x,t.controlNibbles)) + ["|"]
    if equivalent.exists():
        with open(equivalent,"rb") as inf:
            d = inf.read()
            t2 = TEXHeader.parse(d)
            a = analysis(t2,file,len(d))
            result.append([file,file.stem]+a)
    if ix%100 == 0:
        print("%d/%d"%(ix,len(tot)))
with open("AnalysisSize.csv","w") as outf:
    outf.write("path,stem,width,height,depth,imageCount,mipCount,format,cubemap,nib0,nib1,nib2,nib3,aligned,exotic,minpitch\n")
    for line in result:
        outf.write(",".join(map(str,line))+"\n")
with open("MipHell.csv","w") as outf:
    outf.write("file,format,x,y,pitch,px,py,pbitlen,pbytelen,ppitch\n")
    outf.write("\n".join(map(lambda x: ','.join(map(str,x)),miprainbow)))
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    base = r"D:\Wilds\re_chunk_000\natives\STM\Art"
    streaming = r"D:\Wilds\re_chunk_000\natives\STM\streaming\Art"
    tot = list(Path(base).rglob("*.tex.*"))#list()
    fails = []
    volFail = []

    def errorReport(t,file,e):
        print("Assert Fail")
        if t.depth > 1:
            print("Color Volume")
        print(file)
        print(e)
        if t.depth <= 1:
            fails.append(file)
        else:
            volFail.append(file)

    for ix,file in enumerate(tot):
        try:
            equivalent = streaming/file.relative_to(base)
            with open(file,"rb") as inf:
                d = inf.read()
                t = TEXHeader.parse(d)
                _convertFromTex(t,file,True)
        except Exception as e:
            errorReport(t,file,e)
        try:
            if equivalent.exists():
                with open(equivalent,"rb") as inf:
                    d = inf.read()
                    t2 = TEXHeader.parse(d)
                    _convertFromTex(t2,file,True)
            if ix%100 == 0:
                #print(file)
                print("%d/%d"%(ix,len(tot)))
        except Exception as e:
            errorReport(t,file,e)
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
from collections import defaultdict
base = r"D:\Wilds\re_chunk_000\natives\STM\Art"
streaming = r"D:\Wilds\re_chunk_000\natives\STM\streaming\Art"
tot = list(Path(base).rglob("*.tex.*"))#list()
fails = defaultdict(list)
volFail = defaultdict(list)

def errorReport(t,file,msg):
    print(msg)
    print(file)
    if t.depth <= 1:
        fails[msg].append(file)
    else:
        volFail[msg].append(file)
        
def analysis(file):
    mipCalcGen = lambda i: lambda x: max(1,x>>i)
    with open(file,"rb") as inf:
        d = inf.read()
        t = TEXHeader.parse(d)
        formatString = reverseFormatEnum[t.format]
        tx,ty,_,blen = packetSizeData(formatString)
        for img in t.textureHeaders:
            for mix,mip in enumerate(img):
                mipCalc = mipCalcGen(mix)
                x,y,z = map(mipCalc,[t.width,t.height,t.depth])
                xcount = ruD(x,tx)
                calcScanline = xcount*blen
                scanline = mip.pitch
                if scanline != calcScanline:
                    minima = scanlineMinima(formatString)
                    rnxScanline = ruNX(calcScanline,minima)
                    if scanline == minima:
                        #errorReport(t,file,"Minima")
                        pass
                    elif rnxScanline == scanline:
                        #errorReport(t,file,"Depth - Known")
                        pass
                    elif t.depth > 1:
                        errorReport(t,file,"Depth - Unknown")
                        pass
                    elif scanline == ruD(max(x,y),tx)*blen:
                        errorReport(t,file,"Extension to Square")
                        pass
                    else:
                        errorReport(t,file,"Unknown")
                else:
                    if x != y:
                        #print("Non-Square Predicted Correctly")
                        #print(file)
                        pass

for ix,file in enumerate(tot):
    equivalent = streaming/file.relative_to(base)
    analysis(file)
    if equivalent.exists():
        analysis(equivalent)
    if ix%100 == 0:
        #print(file)
        print("%d/%d"%(ix,len(tot)))