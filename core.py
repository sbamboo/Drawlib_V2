from types import MethodType
from libs.conUtils import clear,getConSize,setConSize
from terminal import draw
from coloring import removeAnsiSequences,TextObj,DrawlibStdPalette,autoNoneColor
import json,os

# region Exceptions
class InvalidOutputSize(Exception):
    def __init__(self,message="Drawlib.Output: InvalidSize!"):
        self.message = message
        super().__init__(self.message)

class UnfinishedMethod(Exception):
    def __init__(self,message="Drawlib.Output: This method has not been defined correctly!"):
        self.message = message
        super().__init__(self.message)

class UncreatedBuffer(Exception):
    def __init__(self,message="Drawlib.Buffer: Attempted call on non-created buffer!"):
        self.message = message
        super().__init__(self.message)

class CellOpOutofBounds(Exception):
    def __init__(self,message="Drawlib.Output: Attempted cell operation out of bounds!"):
        self.message = message
        super().__init__(self.message)

class InvalidOutputMode(Exception):
    def __init__(self,message="Drawlib.Output: Invalid output mode!"):
        self.message = message
        super().__init__(self.message)

class DelimToLong(Exception):
    def __init__(self,message="Drawlib.Buffer: Deliminator to long!"):
        self.message = message
        super().__init__(self.message)

class InvalidOutputObj(Exception):
    def __init__(self,message="Drawlib: Invalid and/or non-created output object! Pass a valid object or use base_croutput()."):
        self.message = message
        super().__init__(self.message)

class InvalidSectionRangeType(Exception):
    def __init__(self,message="Drawlib.Buffer: SecionRanges must be of type 'list' or 'tuple' containing two values a min and one max."):
        self.message = message
        super().__init__(self.message)

class SectionRangeOutOfBounds(Exception):
    def __init__(self,message="Drawlib.Buffer: Attempted use of section-range outside the buffer size."):
        self.message = message
        super().__init__(self.message)

class NoOutput(Exception):
    def __init__(self,message="Drawlib: Attempted use of undefined output object."):
        self.message = message
        super().__init__(self.message)
# endregion

# region Placeholders
class Placeholders():
    def __init__(self): pass
    def vh(self): return os.get_terminal_size()[-1]
    def vw(self): return os.get_terminal_size()[0]

placeholders = Placeholders()
vh = placeholders.vh
'''ConsoleSize.Height'''
vw = placeholders.vw
'''ConsoleSize.Width'''
del placeholders
# endregion

# region Helpers
def checkSectionRange(xRange=None,yRange=None,bufferXKeys=list,bufferYKeys=list) -> bool:
    t = "Drawlib.Buffer: Attempted use of section-range outside the buffer size."
    section = False
    validRange = True
    if xRange != None:
        if isinstance(xRange, (list,tuple)) != True or len(xRange) > 2: raise InvalidSectionRangeType()
        errMsg = ""
        try:
            if xRange[0] < int(bufferXKeys[0]) or xRange[1] > int(bufferXKeys[-1]):
                validRange = False
                errMsg=f"XBoundsCheck\nXrangeMin:{xRange[0]} < XbuffMin:{int(bufferXKeys[0])} || XrangeMax:{xRange[1]} > XbuffMax:{int(bufferXKeys[-1])}"
        except IndexError as e:
            validRange = False
            errMsg=f"ErrorOnXBoundsCheck\nIndex: [0,-1]\nxRange: {xRange}\nbuffXkeys: {bufferXKeys}\nyRange: {yRange}\nbuffYkeys: {bufferYKeys}\nException: {e}"
        except Exception as e:
            validRange = False
            errMsg=f"ErrorOnXBoundsCheck: {e}"
        xRange = range(xRange[0],xRange[1])
        section = True
    if yRange != None:
        if isinstance(yRange, (list,tuple)) != True or len(yRange) > 2: raise InvalidSectionRangeType()
        try:
            if yRange[0] < int(bufferYKeys[0]) or yRange[1] > int(bufferYKeys[-1]):
                validRange = False
                errMsg=f"YBoundsCheck\nYrangeMin:{yRange[0]} < YbuffMin:{int(bufferYKeys[0])} || YrangeMax:{yRange[1]} > YbuffMax:{int(bufferYKeys[-1])}"
        except IndexError as e:
            validRange = False
            errMsg=f"ErrorOnXBoundsCheck\nIndex: [0,-1]\nxRange: {xRange}\nbuffXkeys: {bufferXKeys}\nyRange: {yRange}\nbuffYkeys: {bufferYKeys}\nException: {e}"
        except Exception as e:
            validRange = False
            errMsg=f"ErrorOnYBoundsCheck: {e}"
        yRange = range(yRange[0],yRange[1])
        section = True
    if validRange == False: raise SectionRangeOutOfBounds(errMsg)
    return section,xRange,yRange
# endregion

# region Buffer & Output classes
class Buffer():
    def __init__(self,width,height,fallbackChar=" ",autoStr=True):
        if height == "vh" or isinstance(height,MethodType): height = int(getConSize()[-1])
        if width == "vw" or isinstance(width,MethodType): width = int(getConSize()[0])
        if type(width) != int:
            width = max(width)+1
        if type(height) != int:
            height = max(height)+1
        self.bufferSize = (width,height)
        self.buffer = None
        self.fallbackChar = fallbackChar
        self.autoStr = autoStr
    def isCreated(self):
        if self.buffer == None:
            return False
        else:
            return True
    def isOutOfBoundsX(self,x):
        if x < 0 or x > self.bufferSize[0]: return True
        else: return False
    def isOutOfBoundsY(self,y):
        if y < 0 or y > self.bufferSize[1]: return True
        else: return False
    def anyOutOfBounds(self,xs=[],ys=[]):
        for x in xs:
            if self.isOutOfBoundsX(x):
                raise CellOpOutofBounds()
        for y in ys:
            if self.isOutOfBoundsY(y):
                raise CellOpOutofBounds()
    def create(self):
        if self.isCreated() == False:
            self.buffer = {}
            for y in range(self.bufferSize[1]):
                self.buffer[y] = {}
    def clear(self):
        if self.isCreated() == True:
            self.buffer = {}
            for y in range(self.bufferSize[1]):
                self.buffer[y] = {}
    def destroy(self):
        if self.isCreated() == True:
            self.buffer = None
    def put(self,x,y,st):
        self.anyOutOfBounds([x],[y])
        # raise on non-created
        if self.isCreated() == False:
            raise UncreatedBuffer()
        # put
        if self.autoStr == True: st = str(st)
        self.buffer[y][x] = st
    def draw(self,nc=False,baseColor=None,palette=DrawlibStdPalette,xRange=None,yRange=None):
        baseColor = autoNoneColor(baseColor,palette)
        # raise on non-created
        if self.isCreated() == False:
            raise UncreatedBuffer()
        # Check sections
        section,xRange,yRange = checkSectionRange(xRange,yRange, list(range(0,self.bufferSize[0]+1)), list(range(0,self.bufferSize[1]+1)))
        # Clear
        if nc == False: clear()
        # draw sectioned
        if section == True:
            yKeys = list(self.buffer.keys())
            for y in yRange:
                if y in yKeys:
                    xKeys = list(self.buffer[y].keys())
                    for x in xRange:
                        if x in xKeys:
                            v = self.buffer[y].get(x)
                            if v == "" or v == None: v = self.fallbackChar
                            draw(x,y,v,baseColor)
        # draw un-sectioned
        else:
            for y in self.buffer:
                for x in self.buffer[y]:
                    v = self.buffer[y].get(x)
                    if v == "" or v == None: v = self.fallbackChar
                    draw(x,y,v,baseColor)
    def putDelim(self,x,y,st,delim=";"):
        self.anyOutOfBounds([x],[y])
        # raise on non-created
        if self.isCreated() == False:
            raise UncreatedBuffer()
        # put
        if len(delim) > 1:
            raise DelimToLong()
        st = st.replace(f"\\{delim}","§delim§")
        sst = st.split(delim)
        for i,p in enumerate(sst):
            sst[i] == p.replace("§delim§",delim)
        ln = len(st)
        for i in range(ln):
            self.put(x+i,y,sst[i])
    def putCharList(self,x,y,li=list):
        self.anyOutOfBounds([x],[y])
        # raise on non-created
        if self.isCreated() == False:
            raise UncreatedBuffer()
        # put
        ln = len(li)
        for i in range(ln):
            self.put(x+i,y,sst[i])
    def _toStr(self,autoStr=False) -> dict:
        data = {}
        for y in self.buffer:
            data[y] = {}
            for x in self.buffer[y]:
                v = self.buffer[y][x]
                if isinstance(v, TextObj) and autoStr == False:
                    v = v.exprt()
                    v["tag"] = 1
                else:
                    v = str(v)
                data[y][x] = v
        return data
    def exportF(self) -> str:
        # raise on non-created
        if self.isCreated() == False:
            raise UncreatedBuffer()
        # exprt
        return json.dumps(self._toStr())
    def importF(self,jsonStr,encoding="utf-8"):
        data = json.loads(jsonStr)
        for y in data:
            for x in data[y]:
                if isinstance(data[y][x], dict):
                    idata = data[y][x]
                    data[y][x] = TextObj("")
                    data[y][x].imprt(idata)
        self.buffer = data
    def getStrLines(self,xRange=None,yRange=None):
        # raise on non-created
        if self.isCreated() == False:
            raise UncreatedBuffer()
        # Check sections
        section,xRange,yRange = checkSectionRange(xRange,yRange, list(self.buffer[0].keys()), list(self.buffer.keys()))
        # get sectioned
        if section == True:
            lines = []
            yKeys = list(self.buffer.keys())
            for y in yRange:
                if y in yKeys:
                    lines.append("")
                    xKeys = list(self.buffer[y].keys())
                    for x in xRange:
                        if x in xKeys:
                            lines[y] += self.buffer[y][x]
            return lines
        # get un-sectioned
        else:
            lines = []
            for y in self.buffer:
                lines.append("")
                for x in self.buffer[y]:
                    lines[y] += self.buffer[y][x]
            return lines
    def copyStr(self,xRange=None,yRange=None):
        lines = self.getStrLines(xRange,yRange)
        return '\n'.join(lines)
    def fill(self,st=str,xRange=None,yRange=None):
        # raise on non-created
        if self.isCreated() == False:
            raise UncreatedBuffer()
        # Check sections
        section,xRange,yRange = checkSectionRange(xRange,yRange, list(range(0,self.bufferSize[0]+1)), list(self.buffer.keys()))
        # Sectioned
        if section == True:
            yKeys = list(self.buffer.keys())
            for y in yRange:
                if y in yKeys:
                    for x in xRange:
                        self.put(x,y,st)                    
        # Un-Sectioned
        else:
            for y in self.buffer:
                for xi in range(self.bufferSize[0]):
                    self.put(xi,y,st)

class Output():
    def __init__(self,width=None,height=None,name="Drawlib.Buffer.Generic"):
        if height == "vh" or isinstance(height,MethodType): height = getConSize()[-1]
        if width == "vw" or isinstance(width,MethodType): width = getConSize()[0]
        self.name = name
        self.width = width
        self.height = height
        self.validForBase = True
    def _checkSizeInit(self):
        if self.width == None or self.height == None:
            raise InvalidOutputSize(self.name+": Invalid Size!")
    def clear(self):
        raise UnfinishedMethod()
    def put(self,x=int,y=int,inp=str,baseColor=None,palette=None):
        raise UnfinishedMethod()
    def draw(self,x=int,y=int,nc=False,baseColor=None,palette=None,xRange=None,yRange=None):
        raise UnfinishedMethod()
    def mPut(self,coords=list,st=str,baseColor=None,palette=None):
        for pair in coords:
            self.put(pair[0],pair[1],st,baseColor=baseColor,palette=palette)
    def lPut(self,lines=list,stX=int,stY=int,baseColor=None,palette=None):
        c = 0
        for line in lines:
            y = stY + c
            self.put(stX,y,line,baseColor,palette)
            c += 1

class BufferOutput(Output):
    def __init__(self,width=None,height=None,name="Drawlib.Buffer.Buffer", fallbackChar=" ",autoStr=True,buffInst=None):
        if height == "vh" or isinstance(height,MethodType): height = getConSize()[-1]
        if width == "vw" or isinstance(width,MethodType): width = getConSize()[0]
        super().__init__(width,height,name)
        if buffInst != None:
            self.buffer = buffInst
        else:
            self.buffer = Buffer(width,height,fallbackChar=fallbackChar,autoStr=autoStr)
    def create(self):
        self.buffer.create()
        return self
    def destroy(self):
        self.buffer.destroy()
    def clear(self):
        self.buffer.clear()
    def put(self,x=int,y=int,inp=str,baseColor=None,palette=None):
        # put
        self.buffer.put(x,y,st=inp)
    def draw(self,nc=False,baseColor=None,palette=DrawlibStdPalette,xRange=None,yRange=None):
        self.buffer.draw(nc,baseColor,palette,xRange=xRange,yRange=yRange)
        print("\033[0m")
    def getBuf(self,retEmpty=False):
        return self.buffer.getBuf(retEmpty)
    def fill(self,st=str,baseColor=None,palette=None,xRange=None,yRange=None):
        self.buffer.fill(st,xRange,yRange)

class ConsoleOutput(Output):
    def __init__(self):
        self.conSize = getConSize()
        super().__init__(self.conSize[0],self.conSize[-1],None)
    def getSize(self):
        self.conSize = getConSize()
        return self.conSize
    def setSize(self,x=None,y=None):
        if x == None:
            x = self.conSize[0]
        if y == None:
            y = self.conSize[-1]
        setConSize(x,y)
    def isOutOfBoundsX(self,x):
        if x < 0 or x > self.conSize[0]: return True
        else: return False
    def isOutOfBoundsY(self,y):
        if y < 0 or y > self.conSize[1]: return True
        else: return False
    def anyOutOfBounds(self,xs=[],ys=[]):
        for x in xs:
            if self.isOutOfBoundsX(x):
                raise CellOpOutofBounds()
        for y in ys:
            if self.isOutOfBoundsY(y):
                raise CellOpOutofBounds()
    def clear(self):
        clear()
    def put(self,x=int,y=int,st=str,baseColor=None,palette=DrawlibStdPalette):
        baseColor = autoNoneColor(baseColor,palette)
        # handle out-of-bounds
        self.anyOutOfBounds([x],[y])
        # put
        draw(x,y,st,baseColor)
        print("\033[0m")
    def fill(self,st=str,baseColor=None,palette=DrawlibStdPalette,xRange=None,yRange=None):
        # Check sections
        yKeys = list(range(0,self.conSize[-1]+1))
        xKeys = list(range(0,self.conSize[0]+1))
        section,xRange,yRange = checkSectionRange(xRange,yRange, xKeys, yKeys)
        # Sectioned
        if section == True:
            for y in yRange:
                if y in yKeys:
                    for x in xRange:
                        if x in xKeys:
                            self.put(x,y,st,baseColor,palette)
        # Un-Sectioned
        else:
            for y in range(self.conSize[-1]):
                for x in range(self.conSize[0]):
                    self.put(x,y,st,baseColor,palette)

class HybridOutput(Output):
    def __init__(self,name="Drawlib.Buffer.Hybrid", fallbackChar=" ",autoStr=True,buffInst=None):
        self.conSize = getConSize()
        super().__init__(self.conSize[0],self.conSize[-1],name)
        if buffInst != None:
            self.buffer = buffInst
        else:
            self.buffer = Buffer(self.conSize[0],self.conSize[-1],fallbackChar=fallbackChar,autoStr=autoStr)
    def getSize(self):
        self.conSize = getConSize()
        return self.conSize
    def setSize(self,x=None,y=None):
        if x == None:
            x = self.conSize[0]
        if y == None:
            y = self.conSize[-1]
        setConSize(x,y)
    def create(self):
        self.buffer.create()
        return self
    def destroy(self):
        self.buffer.destroy()
    def clear(self):
        clear()
        self.buffer.clear()
    def put(self,x=int,y=int,inp=str,baseColor=None,palette=DrawlibStdPalette,skpBuf=False):
        baseColor = autoNoneColor(baseColor,palette)
        if skpBuf != True: self.buffer.put(x,y,st=inp)
        draw(x,y,inp,baseColor)
    def draw(self,nc=False,baseColor=None,palette=DrawlibStdPalette,xRange=None,yRange=None):
        self.buffer.draw(nc,baseColor,xRange=xRange,yRange=yRange)
    def clearCon(self):
        clear()
    def clearBuf(self):
        self.buffer.clear()
    def putCon(self,x=int,y=int,inp=str):
        draw(x,y,inp)
    def putBuf(self,x=int,y=int,inp=str):
        self.buffer.put(x,y,st=inp)
    def getBuf(self,retEmpty=False):
        return self.buffer.getBuf(retEmpty)
    def fill(self,st=str,baseColor=None,palette=DrawlibStdPalette,xRange=None,yRange=None):
        # buf
        self.buffer.fill(st,xRange,yRange)
        # con
        # Check sections
        yKeys = list(range(0,self.conSize[-1]+1))
        xKeys = list(range(0,self.conSize[0]+1))
        section,xRange,yRange = checkSectionRange(xRange,yRange, xKeys, yKeys)
        # Sectioned
        if section == True:
            for y in yRange:
                if y in yKeys:
                    for x in xRange:
                        if x in xKeys:
                            self.put(x,y,st,baseColor,palette)
        # Un-Sectioned
        else:
            for y in range(self.conSize[-1]):
                for x in range(self.conSize[0]):
                    self.put(x,y,st,baseColor,palette,skpBuf=True)

class ChannelOutput(Output):
    def __init__(self,channelObj,width=None,height=None,name="Drawlib.Buffer.Channel", fallbackChar=" ",autoStr=True,buffInst=None):
        if height == "vh" or isinstance(height,MethodType): height = getConSize()[-1]
        if width == "vw" or isinstance(width,MethodType): width = getConSize()[0]
        super().__init__(width,height,name)
        if buffInst != None:
            self.buffer = buffInst
        else:
            self.buffer = Buffer(width,height,fallbackChar=fallbackChar,autoStr=autoStr)
        self.channelClassInstance = channelObj
    def create(self):
        self.buffer.create()
        return self
    def destroy(self):
        self.buffer.destroy()
    def clear(self):
        self.buffer.clear()
    def put(self,x=int,y=int,inp=str,baseColor=None,palette=None):
        # put
        self.buffer.put(x,y,st=inp)
    def draw(self,nc=False,baseColor=None,palette=DrawlibStdPalette,xRange=None,yRange=None):
        ostr = self.buffer.copyStr(xRange,yRange)
        self.channelClassInstance.send(ostr)
    def getBuf(self,retEmpty=False):
        return self.buffer.getBuf(retEmpty)
    def fill(self,st=str,baseColor=None,palette=None,xRange=None,yRange=None):
        self.buffer.fill(st,xRange,yRange)

class DrawlibOut():
    def __init__(self,mode=None,overwWidth=None,overwHeight=None,buffIChar=None,buffAutoStr=True,buffInst=None,channelObj=None,outputObj=None,wi=None,hi=None,autoLink=False):
        if wi != None: overwWidth = wi
        if hi != None: overwHeight = hi
        self.allowedMods = ["Buffer","Console","Hybrid","Channel"]
        self.defMode = "Console"
        if overwHeight == "vh" or isinstance(overwHeight,MethodType): overwHeight = getConSize()[-1]
        if overwWidth == "vw" or isinstance(overwHeight,MethodType): overwWidth = getConSize()[0]
        self.overwWidth = overwWidth
        self.overwHeight = overwHeight
        self.buffIChar = buffIChar
        self.buffAutoStr = buffAutoStr
        self.channelObj = channelObj
        self.buffInst = buffInst
        self.outputObj = outputObj
        self.validForBase = True
        if mode in self.allowedMods:
            self.mode = mode
        else:
            self.mode = self.defMode
        self.linked = None
        if autoLink == True:
            self._link()
    def setM(self,mode=None):
        if mode not in self.allowedMods:
            raise InvalidOutputMode()
        else:
            self.mode = mode
    def resM(self):
        self.mode = self.defMode
    def _link(self):
        if self.outputObj != None:
            self.linked = self.outputObj
        else:
            if self.mode == "Buffer":
                width = vw
                height = vh
                if self.overwWidth != None: width = self.overwWidth
                if self.overwHeight != None: height = self.overwHeight
                self.linked = BufferOutput(width,height,fallbackChar=self.buffIChar,autoStr=self.buffAutoStr,buffInst=self.buffInst).create()
            elif self.mode == "Console":
                self.linked = ConsoleOutput()
            elif self.mode == "Hybrid":
                self.linked = HybridOutput(fallbackChar=self.buffIChar,autoStr=self.buffAutoStr,buffInst=self.buffInst).create()
            elif self.mode == "Channel":
                width = vw
                height = vh
                if self.overwWidth != None: width = self.overwWidth
                if self.overwHeight != None: height = self.overwHeight
                self.linked = ChannelOutput(self.channelObj,width,height,fallbackChar=self.buffIChar,autoStr=self.buffAutoStr,buffInst=self.buffInst).create()
    def put(self,x,y,st,baseColor=None,palette=DrawlibStdPalette):
        if self.linked == None: self._link()
        self.linked.put(x,y,st,baseColor=baseColor,palette=palette)
    def draw(self,nc=False,baseColor=None,palette=DrawlibStdPalette,xRange=None,yRange=None):
        if self.linked == None: self._link()
        self.linked.draw(nc=nc,baseColor=baseColor,palette=palette,xRange=xRange,yRange=yRange)
    def clear(self):
        if self.linked == None: self._link()
        self.linked.clear()
    def mPut(self,*args,**kwargs):
        if self.linked == None: self._link()
        self.linked.mPut(*args,**kwargs)
    def lPut(self,*args,**kwargs):
        if self.linked == None: self._link()
        self.linked.lPut(*args,**kwargs)
    def fill(self,st=str,baseColor=None,palette=DrawlibStdPalette,xRange=None,yRange=None):
        if self.linked == None: self._link()
        self.linked.fill(st,baseColor,palette,xRange=xRange,yRange=yRange)
# endregion

# region draw functions
def base_croutput(overwWidth=None,overwHeight=None,mode="Console",buffIChar=" ",buffAutoStr=True,buffInst=None,channelObj=None,outputObj=None):
    '''Returns a drawlib-output object created with the given parameters.'''
    return DrawlibOut(
        mode=mode,
        overwWidth=overwWidth,
        overwHeight=overwHeight,
        buffIChar=buffIChar,
        buffAutoStr=buffAutoStr,
        buffInst=buffInst,
        channelObj=channelObj,
        outputObj=outputObj
    )

def base_draw(st=str,x=int,y=int,output=object,baseColor=None,palette=DrawlibStdPalette,drawNc=False):
    '''Uses a drawlib-output object to draw on x,y.'''
    valid = True
    try:
        if output.mode == None:
            valid = False
    except: valid = False
    if valid == False: raise InvalidOutputObj()
    output.put(x,y,st,baseColor,palette)
    try:
        if output.mode != "Console":
            output.draw(drawNc,baseColor,palette)
    except AttributeError(): pass

def base_mdraw(st=str,coords=list,output=object,baseColor=None,palette=DrawlibStdPalette,drawNc=False):
    '''Uses a drawlib-output object to draw on each coord-pair in coords list.'''
    valid = True
    try:
        if output.validForBase != True:
            valid = False
    except: valid = False
    if valid == False: raise InvalidOutputObj()
    output.mPut(coords,st,baseColor,palette)
    try:
        if output.mode != "Console":
            output.draw(drawNc,baseColor,palette)
    except AttributeError(): pass

def base_fill(st=str,output=object,baseColor=None,palette=DrawlibStdPalette,drawNc=False):
    '''Uses a drawlib-output object to draw on each cell.'''
    valid = True
    try:
        if output.validForBase != True:
            valid = False
    except: valid = False
    if valid == False: raise InvalidOutputObj()
    output.fill(st,baseColor,palette)
    try:
        if output.mode != "Console":
            output.draw(drawNc,baseColor,palette)
    except AttributeError(): pass

def base_texture(textureFile=str,tlCoordX=int,tlCoordY=int,output=object,baseColor=None,palette=DrawlibStdPalette,drawNc=False):
    '''Uses a drawlib-output to draw a texture.'''
    # Validate output obj
    valid = True
    try:
        if output.validForBase != True:
            valid = False
    except: valid = False
    if valid == False: raise InvalidOutputObj()
    # Get the texture content from the file
    if os.path.exists(textureFile):
        rawContent = open(textureFile, 'r').read()
    else:
        raise FileNotFoundError(f"Drawlib: Texture file not found! '{textureFile}'")
    # Split the rawContent into lines of text
    spriteLines = rawContent.split('\n')
    # Render the texture at the tl-coords:
    c = 0 # Set incr-counter to 0
    orgScreenCoordY = int(tlCoordY) # Save the original y-coord
    for line in spriteLines: # iterate through the lines
        coordY = orgScreenCoordY + c # Increment the Y coordinate
        # Prep line
        line = line.replace("\\033","\033")
        line = line.replace("\033[0m","")
        line += "\033[0m"
        # Use the object to put the texture on the output
        output.put(tlCoordX,coordY,line,baseColor,palette)
        # Icrement y
        c += 1
    # If not mode=console then draw
    try:
        if output.mode != "Console":
            output.draw(drawNc,baseColor,palette)
    except AttributeError(): pass
# endregion
