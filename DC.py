import wx
import random

class BufferedFrame(wx.Frame):

    def __init__(self, *args, **kwargs):
        # Make sure the NO_FULL_REPAINT_ON_RESIZE style flag is set.
        # And define a new kwargs entry for wx.python
        kwargs['style'] = kwargs.setdefault('style', wx.NO_FULL_REPAINT_ON_RESIZE) | wx.NO_FULL_REPAINT_ON_RESIZE
        super().__init__( *args, **kwargs)

        # Setup event handlers for drawing
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        # OnSize called to make sure the buffer is initialized.
        self.OnSize(None)

    def Draw(self, dc):
        pass

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self, self._Buffer)

    def OnSize(self,event):
        Size  = self.ClientSize

        # Make new offscreen bitmap: this bitmap will always have the
        # current drawing in it, so it can be used to save the image to
        # a file, or whatever.
        self._Buffer = wx.Bitmap(*Size)
        self.UpdateDrawing()

    def UpdateDrawing(self):
        '''
         This would get called if the drawing is changed, for whatever reason.

         The idea here is that the drawing is based on some data generated
         elsewhere in the system. If that data changes, the drawing needs to
         be updated.

         This code re-draws the buffer, then calls Update, which forces a paint event.
        '''
        dc = wx.MemoryDC()
        dc.SelectObject(self._Buffer)
        self.Draw(dc)
        del dc      # need to get rid of the MemoryDC before Update() is called.
        self.Refresh()
        self.Update()
            
class DrawFrame(BufferedFrame):
    '''
     Purpose: Initialization for Draw()
    '''
    def __init__(self, *args, **kwargs):
        '''
         Any data the Draw() function needs must be initialized before
         initialization of BufferedFrame, since this will trigger the Draw
         function.
        '''
        self.DrawData = {}
        super().__init__(*args, **kwargs)  # initialize parent (BufferedFrame)

    def Draw(self, dc):
        '''
         Purpose: to generate all the cmds for drawing
          Note:
           1. Overrides Draw() in BufferedFrame()
        '''
        dc.SetBackground( wx.Brush("White") )
        dc.Clear() # make sure you clear the bitmap!

        # Here's the actual drawing code.
        for key, data in self.DrawData.items():
            if key == "Rectangles":
                dc.SetBrush(wx.BLUE_BRUSH)
                dc.SetPen(wx.Pen('VIOLET', 4))
                for r in data:
                    dc.DrawRectangle(*r)
            elif key == "Ellipses":
                dc.SetBrush(wx.Brush("GREEN YELLOW"))
                dc.SetPen(wx.Pen('CADET BLUE', 2))
                for r in data:
                    dc.DrawEllipse(*r)
            elif key == "Polygons":
                dc.SetBrush(wx.Brush("SALMON"))
                dc.SetPen(wx.Pen('VIOLET RED', 4))
                for r in data:
                    dc.DrawPolygon(r)

class MyFrame(wx.Frame):
    '''
     Purpose: initialize a frame to hold DC and setup menu bar
    '''
    def __init__(self, parent=None):
        wx.Frame.__init__(self, parent,
                          title = "Double Buffered Test",
                          style = wx.DEFAULT_FRAME_STYLE)

        ## Set up the MenuBar
        MenuBar   = wx.MenuBar()
        file_menu = wx.Menu()
        # Define each item in menu bar and their event handlers

        draw_menu = wx.Menu()
        item = draw_menu.Append(wx.ID_ANY, "&New Drawing","Update the Drawing Data")
        self.Bind(wx.EVT_MENU, self.NewDrawing, item)
        MenuBar.Append(draw_menu, "&Draw")

        self.SetMenuBar(MenuBar)
        self.Frame = DrawFrame(self) # initialize window for drawing
        self.Show()
        # Initialize a drawing -- it has to be done after Show() is called
        #   so that the Window is correctly sized.
        self.NewDrawing()

    def OnQuit(self,event):
        self.Close(True)
        
    def NewDrawing(self, event=None):
        self.Frame.DrawData = self.MakeNewData()
        self.Frame.UpdateDrawing()

    def MakeNewData(self):
        '''
         Purpose: generate some data for randomly shaped geometric
                  structures (rectangles, ellipses and polygons)
        '''
        MaxX, MaxY = self.GetClientSize() # to limit the size of these structures
        
        DrawData = {}
        # Define some random rectangles
        lst = []
        for i in range(5):
            w = random.randint(1,MaxX//2)
            h = random.randint(1,MaxY//2)
            x = random.randint(1,MaxX-w)
            y = random.randint(1,MaxY-h)
            lst.append( (x,y,w,h) )
        DrawData["Rectangles"] = lst

        # Define some random ellipses
        lst = []
        for i in range(5):
            w = random.randint(1,MaxX//2)
            h = random.randint(1,MaxY//2)
            x = random.randint(1,MaxX-w)
            y = random.randint(1,MaxY-h)
            lst.append( (x,y,w,h) )
        DrawData["Ellipses"] = lst

        # Define some random Polygons
        lst = []
        for i in range(3):
            points = []
            for j in range(random.randint(3,8)):
                point = (random.randint(1,MaxX),random.randint(1,MaxY))
                points.append(point)
            lst.append(points)
        DrawData["Polygons"] = lst

        return DrawData

class DemoApp(wx.App):
    '''
     Purpose: initialize frame to hold DC
      Note:
       1. Uses the default OnInit method in wx.App
    '''
    def OnInit(self):
        frame = MyFrame()
        self.SetTopWindow(frame)
        return True

if __name__ == "__main__":
    # Ok, let's run it ...
    app = DemoApp(0)
    app.MainLoop()
