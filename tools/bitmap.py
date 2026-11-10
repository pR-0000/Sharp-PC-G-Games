"""FR/EN: tiny uncompressed BMP reader/writer, standard Python only."""
from pathlib import Path
import struct
import zlib

def write_png(path,width,height,pixels):
    """RGB tuples, no smoothing or external image library / sans dependance."""
    if len(pixels)!=width*height:raise ValueError('PNG dimensions')
    def chunk(kind,payload):
        return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload))
    rgb=bytes(channel for pixel in pixels for channel in pixel)
    rows=b''.join(b'\0'+rgb[y*width*3:(y+1)*width*3] for y in range(height))
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+
                          chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def write_bmp(path,width,height,pixels):
    if len(pixels)!=width*height:raise ValueError('Dimensions BMP / BMP dimensions')
    stride=(width*3+3)&~3
    data=bytearray()
    for y in reversed(range(height)):
        for r,g,b in pixels[y*width:(y+1)*width]:data.extend((b,g,r))
        data.extend(bytes(stride-width*3))
    header=struct.pack('<2sIHHI',b'BM',54+len(data),0,0,54)
    header+=struct.pack('<IiiHHIIiiII',40,width,height,1,24,0,len(data),2835,2835,0,0)
    Path(path).write_bytes(header+data)

def read_bmp(path):
    data=Path(path).read_bytes()
    def invalid():raise ValueError('BMP non compresse 1/4/8/24/32 bits requis / Uncompressed 1/4/8/24/32-bit BMP required')
    if len(data)<54 or data[:2]!=b'BM':invalid()
    offset,dib=struct.unpack_from('<I',data,10)[0],struct.unpack_from('<I',data,14)[0]
    width,sheight,planes,depth,compression=struct.unpack_from('<iiHHI',data,18)
    height=abs(sheight)
    if dib<40 or planes!=1 or compression or depth not in (1,4,8,24,32):invalid()
    if not(0<width<=8192 and 0<height<=8192) or offset<14+dib:invalid()
    stride=((width*depth+31)//32)*4
    if offset+stride*height>len(data):invalid()
    palette=[]
    if depth<=8:
        count=struct.unpack_from('<I',data,46)[0] or 1<<depth
        if count>1<<depth or 14+dib+4*count>offset:invalid()
        for i in range(count):
            b,g,r,_=data[14+dib+4*i:18+dib+4*i];palette.append((r,g,b))
    pixels=[]
    for y in range(height):
        row=offset+(height-1-y if sheight>0 else y)*stride
        for x in range(width):
            if depth>=24:
                b,g,r=data[row+x*(depth//8):row+x*(depth//8)+3];pixels.append((r,g,b))
            else:
                bit=x*depth;index=(data[row+bit//8]>>(8-depth-bit%8))&((1<<depth)-1)
                if index>=len(palette):invalid()
                pixels.append(palette[index])
    return width,height,pixels
