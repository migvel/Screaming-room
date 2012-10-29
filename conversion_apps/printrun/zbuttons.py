# This file is part of the Printrun suite.
# 
# Printrun is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Printrun is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Printrun.  If not, see <http://www.gnu.org/licenses/>.

import wx, os, math
from bufferedcanvas import *

def imagefile(filename):
    if os.path.exists(os.path.join(os.path.dirname(__file__), "images", filename)):
        return os.path.join(os.path.dirname(__file__), "images", filename)
    else:
        return os.path.join(os.path.split(os.path.split(__file__)[0])[0], "images", filename)
    
    

def sign(n):
    if n < 0: return -1
    elif n > 0: return 1
    else: return 0

class ZButtons(BufferedCanvas):
    button_ydistances = [7, 30, 55, 83] # ,112
    center = (30, 118)
    label_overlay_positions = {
        0: (1, 18, 11),
        1: (1, 41, 13),
        2: (1, 67, 15),
        3: None
    }

    def __init__(self, parent, moveCallback=None, ID=-1):
        self.bg_bmp = wx.Image(imagefile("control_z.png"),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.range = None
        self.direction = None
        self.orderOfMagnitudeIdx = 0 # 0 means '1', 1 means '10', 2 means '100', etc.
        self.moveCallback = moveCallback
        self.enabled = False

        BufferedCanvas.__init__(self, parent, ID)

        self.SetSize(wx.Size(59, 244))

        # Set up mouse and keyboard event capture
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow)

    def disable(self):
        self.enabled = False
        self.update()
    
    def enable(self):
        self.enabled = True
        self.update()

    def lookupRange(self, ydist):
        idx = -1
        for d in ZButtons.button_ydistances:
            if ydist < d:
                return idx
            idx += 1
        return None
    
    def highlight(self, gc, rng, dir):
        assert(rng >= -1 and rng <= 3)
        assert(dir >= -1 and dir <= 1)

        fudge = 11
        x = 0 + fudge
        w = 59 - fudge*2
        if rng >= 0:
            k = 1 if dir > 0 else 0
            y = ZButtons.center[1] - (dir * ZButtons.button_ydistances[rng+k])
            h = ZButtons.button_ydistances[rng+1] - ZButtons.button_ydistances[rng]
            gc.DrawRoundedRectangle(x, y, w, h, 4)
            # gc.DrawRectangle(x, y, w, h)
        # self.drawPartialPie(dc, center, r1-inner_ring_radius, r2-inner_ring_radius, a1+fudge, a2-fudge)
    
    def getRangeDir(self, pos):
        ydelta = ZButtons.center[1] - pos[1]
        return (self.lookupRange(abs(ydelta)), sign(ydelta))

    def draw(self, dc, w, h):
        dc.Clear()
        gc = wx.GraphicsContext.Create(dc)
        if self.bg_bmp:
            w, h = (self.bg_bmp.GetWidth(), self.bg_bmp.GetHeight())
            gc.DrawBitmap(self.bg_bmp, 0, 0, w, h)

        if self.enabled:
            # Draw label overlays
            gc.SetPen(wx.Pen(wx.Colour(255,255,255,128), 1))
            gc.SetBrush(wx.Brush(wx.Colour(255,255,255,128+64)))
            for idx, kpos in ZButtons.label_overlay_positions.items():
                if kpos and idx != self.range:
                    r = kpos[2]
                    gc.DrawEllipse(ZButtons.center[0]-kpos[0]-r, ZButtons.center[1]-kpos[1]-r, r*2, r*2)
            
            # Top 'layer' is the mouse-over highlights
            gc.SetPen(wx.Pen(wx.Colour(100,100,100,172), 4))
            gc.SetBrush(wx.Brush(wx.Colour(0,0,0,128)))
            if self.range != None and self.direction != None:
                self.highlight(gc, self.range, self.direction)
        else:
            gc.SetPen(wx.Pen(wx.Colour(255,255,255,0), 4))
            gc.SetBrush(wx.Brush(wx.Colour(255,255,255,128)))
            gc.DrawRectangle(0, 0, w, h)

    ## ------ ##
    ## Events ##
    ## ------ ##

    def OnMotion(self, event):
        if not self.enabled:
            return
        
        oldr, oldd = self.range, self.direction

        mpos = event.GetPosition()
        self.range, self.direction = self.getRangeDir(mpos)

        if oldr != self.range or oldd != self.direction:
            self.update()

    def OnLeftDown(self, event):
        if not self.enabled:
            return

        mpos = event.GetPosition()
        r, d = self.getRangeDir(mpos)
        if r >= 0:
            value = math.pow(10, self.orderOfMagnitudeIdx) * math.pow(10, r - 1) * d
            if self.moveCallback:
                self.moveCallback(value)

    def OnLeaveWindow(self, evt):
        self.range = None
        self.direction = None
        self.update()
