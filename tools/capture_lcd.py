"""Capture a newly rendered g800 LCD region, without desktop/window chrome.

FR: capture de l'ecran LCD uniquement. EN: LCD-only screenshot capture.
Windows; optional Pillow dependency. No ROM or emulator is bundled.
"""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import subprocess
import tempfile
import time
from cli_i18n import Parser,pick


def capture(emulator,program,output,model='PC-G801',zoom=6,clock=None):
    from PIL import Image
    g850='850' in model
    palette_counts=(2,) if g850 else (2,3) # G80X cell gaps can use a third LCD tone.
    lcd_x,lcd_y,lcd_w,lcd_h=(18,2,144,48) if g850 else (1,6,144,32)
    minimum_w,minimum_h=(lcd_x+lcd_w)*zoom,(lcd_y+lcd_h)*zoom
    clock=clock or (8000 if g850 else 4000)
    user=C.WinDLL('user32',use_last_error=True)
    gdi=C.WinDLL('gdi32',use_last_error=True)
    user.GetDC.argtypes=[W.HWND];user.GetDC.restype=W.HDC
    user.ReleaseDC.argtypes=[W.HWND,W.HDC]
    user.PrintWindow.argtypes=[W.HWND,W.HDC,W.UINT];user.PrintWindow.restype=W.BOOL
    user.GetClientRect.argtypes=[W.HWND,C.POINTER(W.RECT)]
    user.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)]
    user.ShowWindow.argtypes=[W.HWND,C.c_int]
    user.SetWindowPos.argtypes=[W.HWND,W.HWND,C.c_int,C.c_int,C.c_int,C.c_int,W.UINT]
    user.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
    gdi.CreateCompatibleDC.argtypes=[W.HDC];gdi.CreateCompatibleDC.restype=W.HDC
    gdi.CreateDIBSection.argtypes=[W.HDC,C.c_void_p,W.UINT,C.POINTER(C.c_void_p),W.HANDLE,W.DWORD]
    gdi.CreateDIBSection.restype=W.HBITMAP
    gdi.SelectObject.argtypes=[W.HDC,W.HGDIOBJ];gdi.SelectObject.restype=W.HGDIOBJ
    gdi.BitBlt.argtypes=[W.HDC,C.c_int,C.c_int,C.c_int,C.c_int,W.HDC,C.c_int,C.c_int,W.DWORD]
    gdi.DeleteObject.argtypes=[W.HGDIOBJ];gdi.DeleteDC.argtypes=[W.HDC]
    class BIH(C.Structure):
        _fields_=[('size',W.DWORD),('width',W.LONG),('height',W.LONG),('planes',W.WORD),('bits',W.WORD),
                  ('compression',W.DWORD),('image_size',W.DWORD),('x',W.LONG),('y',W.LONG),('colors',W.DWORD),('important',W.DWORD)]
    def bitmap(width,height):
        dc=gdi.CreateCompatibleDC(None)
        info=BIH(40,width,-height,1,32,0,width*height*4,0,0,0,0)
        pointer=C.c_void_p()
        handle=gdi.CreateDIBSection(dc,C.byref(info),0,C.byref(pointer),None,0)
        if not handle: raise C.WinError(C.get_last_error())
        previous=gdi.SelectObject(dc,handle)
        return dc,handle,previous,pointer
    callback_type=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
    handles=[]
    startup=subprocess.STARTUPINFO()
    startup.dwFlags=subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow=0
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryFile() as log:
        process=subprocess.Popen([str(Path(emulator).resolve()),'-machine='+model,'-rom_dir=','-ram_path=','-basic_path=',
            '-emulate_iocs=y','-clock='+str(clock),'-zoom='+str(zoom),'-use_joy=n','-refresh=120',str(Path(program).resolve()),'100'],
            cwd=Path(emulator).resolve().parent,stdout=log,stderr=log,startupinfo=startup,creationflags=subprocess.CREATE_NO_WINDOW)
        hwnd=None
        try:
            @callback_type
            def visit(window,_):
                pid=W.DWORD()
                user.GetWindowThreadProcessId(window,C.byref(pid))
                bounds=W.RECT()
                if pid.value==process.pid and user.GetClientRect(window,C.byref(bounds)) and bounds.right>=minimum_w and bounds.bottom>=minimum_h:
                    handles.append(window)
                return True
            for _ in range(100):
                handles.clear();user.EnumWindows(visit,0)
                if handles: hwnd=handles[0];break
                if process.poll() is not None: raise RuntimeError('g800 exited before display')
                time.sleep(.05)
            if not hwnd: raise RuntimeError('g800 window unavailable')
            user.ShowWindow(hwnd,4) # SW_SHOWNOACTIVATE: no keyboard focus is taken.
            # SDL/GDI may return occluding desktop pixels for GetDC/PrintWindow.
            # Keep this temporary capture window visible, without taking focus.
            user.SetWindowPos(hwnd,W.HWND(-1),0,0,0,0,0x0013)
            time.sleep(.65)
            rect=W.RECT();user.GetClientRect(hwnd,C.byref(rect))
            width,height=lcd_w*zoom,lcd_h*zoom
            assert rect.right>=minimum_w and rect.bottom>=minimum_h,(rect.right,rect.bottom)
            full=bitmap(rect.right,rect.bottom);lcd=bitmap(width,height)
            try:
                for attempt in range(12):
                    user.PrintWindow(hwnd,full[0],3) # client + rendered content
                    if not gdi.BitBlt(lcd[0],0,0,width,height,full[0],lcd_x*zoom,lcd_y*zoom,0x00CC0020): raise RuntimeError('BitBlt failed')
                    raw=C.string_at(lcd[3],width*height*4)
                    picture=Image.frombytes('RGB',(width,height),raw,'raw','BGRX')
                    if len(picture.getcolors(width*height) or []) in palette_counts: break
                    source=user.GetDC(hwnd)
                    try:
                        if not gdi.BitBlt(lcd[0],0,0,width,height,source,lcd_x*zoom,lcd_y*zoom,0x00CC0020): raise RuntimeError('LCD BitBlt failed')
                        raw=C.string_at(lcd[3],width*height*4)
                        picture=Image.frombytes('RGB',(width,height),raw,'raw','BGRX')
                    finally: user.ReleaseDC(hwnd,source)
                    if len(picture.getcolors(width*height) or []) in palette_counts: break
                    time.sleep(.1)
                if len(picture.getcolors(width*height) or []) not in palette_counts: raise RuntimeError('LCD capture has an unexpected palette')
                Path(output).parent.mkdir(parents=True,exist_ok=True)
                picture.save(output)
            finally:
                for dc,handle,previous,_ in (full,lcd):
                    gdi.SelectObject(dc,previous);gdi.DeleteObject(handle);gdi.DeleteDC(dc)
            return {'model':model,'zoom':zoom,'lcd_pixels':[width,height],'client_region':[lcd_x*zoom,lcd_y*zoom,width,height],
                    'source':'g800 newly rendered LCD; no Sharp ROM','windows_chrome':False}
        finally:
            if hwnd: user.PostMessageW(hwnd,0x0010,0,0)
            try: process.wait(timeout=3)
            except subprocess.TimeoutExpired: process.kill();process.wait(timeout=3)


if __name__=='__main__':
    parser=Parser('Capturer seulement le LCD de g800 sous Windows.','Capture only the g800 LCD on Windows.')
    parser.add_argument('--emulator',required=True,help='g800.exe')
    parser.add_argument('--program',required=True,help='HEX')
    parser.add_argument('--output',required=True,help='PNG')
    parser.add_argument('--model',default='PC-G801')
    args=parser.parse_args()
    capture(args.emulator,args.program,args.output,args.model)
    print(pick(args.lang,'Capture LCD enregistree.','LCD capture saved.'))
