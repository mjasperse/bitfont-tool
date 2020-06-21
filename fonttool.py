from PySide import QtCore, QtGui
from flowlayout import FlowLayout

STANDARD = (
    ('Common', (0x20, 91)),
    ('Hexadecimal', (0x30, 23)),
    ('Alpha-numeric', (0x30, 75)),
    ('Numeric only', (0x30,10)),
)

class GlyphWidget(QtGui.QWidget):
    toggled = QtCore.Signal(int)
    def __init__(self, pixmap, glyph, w, parent):
        super(GlyphWidget,self).__init__(parent)
        self.setMinimumWidth(w)
        b = QtGui.QHBoxLayout(self)
        b.setContentsMargins(0,0,0,0)
        lb = QtGui.QLabel(self)
        lb.setPixmap(pixmap)
        lb.setToolTip('0x%02X (%d)'%(ord(glyph),ord(glyph)))
        b.addStretch()
        b.addWidget(lb)
        b.addStretch()
        self.show = True
        self.glyph = glyph
        self.toggled.connect(parent.toggleGlyph)
    def mouseDoubleClickEvent(self,evt):
        self.show = not self.show
        self.toggled.emit(self.show)

class FontTool(QtGui.QMainWindow):
    def __init__(self):
        super(FontTool,self).__init__()
        
        self.font = QtGui.QFont('Arial')
        self.font.setStyleStrategy(QtGui.QFont.NoAntialias)
        self.font.setPointSize(40)
        
        self.fixed = False
        self.flow = None
        self.lbs = []
        self.first = 0x20
        self.count = 0x60
        self.minimize = False
        self.ignore = {}
        
        self.initUI()
        self.fontchoice.setCurrentFont(self.font)
        
    def initUI(self):
        w = QtGui.QWidget(self)
        b = QtGui.QVBoxLayout(w)
        self.setCentralWidget(w)
        self.setWindowTitle('Font generation tool')
        
        h = QtGui.QHBoxLayout()
        b.addLayout(h)
        h.setContentsMargins(0,0,0,0)
        
        self.fontchoice = QtGui.QFontComboBox()
        self.fontchoice.currentFontChanged.connect(self.changeFont)
        self.fontsize = QtGui.QComboBox(self)
        self.fontsize.setEditable(True)
        self.fontsize.setEditText(str(self.font.pointSize()))
        self.fontsize.currentIndexChanged[str].connect(self.changeSize)
        self.fontsize.editTextChanged.connect(self.changeSize)
        h.addWidget(self.fontchoice)
        h.addWidget(self.fontsize)
        
        btn = QtGui.QCheckBox('Fixed width',self)
        btn.toggled.connect(self.changeFixed)
        h.addWidget(btn)
        btn = QtGui.QCheckBox('Minimize height',self)
        btn.toggled.connect(self.changeMinimize)
        h.addWidget(btn)
        h.addStretch()
        
        h = QtGui.QHBoxLayout()
        b.addLayout(h)
        h.setContentsMargins(0,0,0,0)
        
        h.addWidget(QtGui.QLabel('First character:',self))
        self.firstbox = w = QtGui.QLineEdit(str(self.first))
        w.textChanged.connect(self.changeRange)
        w.setValidator(QtGui.QIntValidator(0,0xFF))
        w.setMaximumWidth(40)
        h.addWidget(w)
        h.addWidget(QtGui.QLabel('Count:',self))
        self.countbox = w = QtGui.QLineEdit(str(self.count))
        w.setValidator(QtGui.QIntValidator(0,0xFF))
        w.textChanged.connect(self.changeRange)
        w.setMaximumWidth(40)
        h.addWidget(w)
        self.rangebox = cb = QtGui.QComboBox(self)
        cb.addItem('Standard ranges >>')
        for (s,x) in STANDARD: cb.addItem(s, userData=x)
        cb.currentIndexChanged[int].connect(self.setStandardRange)
        h.addWidget(cb)
        h.addStretch()
        
        self.scroller = QtGui.QScrollArea(self)
        self.scroller.setBackgroundRole(QtGui.QPalette.Dark)
        self.scroller.setWidgetResizable(True)
        self.scroller.setMinimumWidth(400)
        b.addWidget(self.scroller)
        
        h = QtGui.QFormLayout()
        b.addLayout(h)
        self.teststr = QtGui.QLineEdit(self)
        self.teststr.textChanged.connect(self.testString)
        h.addRow('Test string:',self.teststr)
        self.testlb = QtGui.QLabel(self)
        self.testlb.setAutoFillBackground(True)
        self.testlb.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
        h.addRow(self.testlb)
        
        sb = self.statusBar()
        self.lbsz = QtGui.QLabel(self)
        sb.addPermanentWidget(self.lbsz)
        
    def changeRange(self):
        try:
            self.first = int(self.firstbox.text())
            self.count = int(self.countbox.text())
        except ValueError:
            return
        self.generate()
        
    def changeFont(self, f):
        sz = self.font.pointSize()
        f.setPointSize(sz)
        self.font = f
        self.fontsize.blockSignals(True)
        self.fontsize.clear()
        for i in QtGui.QFontDatabase().pointSizes(f.family()): self.fontsize.addItem(str(i))
        i = self.fontsize.findText(str(sz))
        if i >= 0: self.fontsize.setCurrentIndex(i)
        else: self.fontsize.setEditText(str(self.font.pointSize()))
        self.fontsize.blockSignals(False)
        self.generate()
        
    def changeSize(self, sz):
        try: sz = int(sz)
        except: return
        self.font.setPointSize(sz)
        self.generate()
        
    def changeFixed(self,val):
        self.fixed = val
        self.generate()
        
    def changeMinimize(self,val):
        self.minimize = val
        self.generate()
        
    def setStandardRange(self,i):
        try: (x,y) = self.rangebox.itemData(i)
        except TypeError: return
        self.firstbox.blockSignals(True)
        self.firstbox.setText(str(x))
        self.firstbox.blockSignals(False)
        self.countbox.setText(str(y))
        
    def toggleGlyph(self):
        i = self.sender().glyph
        self.ignore[i] = not self.ignore.get(i,False)
        self.generate()
        
    def makePixmap(self,i):
        w = self.sz[0] if self.fixed else self.metrics.width(i)
        pix = QtGui.QPixmap(w,self.sz[1])
        pix.fill(QtCore.Qt.blue if self.ignore.get(i,False) else QtCore.Qt.white)
        painter = QtGui.QPainter()
        painter.begin(pix)
        painter.setFont(self.font)
        painter.drawText(0,self.baseline,i)
        painter.end()
        self.glyphs[i] = pix
        pix.glyph = i
        return pix
        
    def generate(self):
        self.glyphs = {}
        self.metrics = QtGui.QFontMetrics(self.font)
        
        chrs = [chr(i) for i in range(self.first,self.first+self.count)]
        rects = [self.metrics.boundingRect(i) for i in chrs if not self.ignore.get(i,False)]
        bounds = [min([R.left() for R in rects]), min([R.top() for R in rects]),
                    max([R.right() for R in rects]), max([R.bottom() for R in rects])]
        self.sz = [bounds[2]-bounds[0], bounds[3]-bounds[1]]
        self.baseline = -bounds[1]-1
        if self.minimize:
            self.sz[1] -= self.metrics.descent()-1
            self.baseline -= self.metrics.descent()-1
        print self.sz, self.baseline, self.metrics.descent()
        
        frame = QtGui.QFrame(self)
        self.scroller.setWidget(frame)
        flow = FlowLayout(frame)
        flow.setSpacing(5)
        
        for i in chrs:
            flow.addWidget(GlyphWidget(self.makePixmap(i),i,self.sz[0],self))
        
        # compute the memory required for all the glyphs
        mem = sum([g.width() for i,g in self.glyphs.items() if not self.ignore.get(i, False)])*self.sz[1]/8
        self.lbsz.setText("Required memory: %d bytes"%mem)
        # generate a test string to see how it looks
        self.testString()
        
    def testString(self, str=None):
        if str is None: str = self.teststr.text()
        pxlist = [self.glyphs[i] for i in str if i in self.glyphs]
        w = sum([px.width() for px in pxlist])
        if w == 0: w = 1
        testpx = QtGui.QPixmap(w,self.sz[1])
        testpx.fill(QtCore.Qt.white)
        x = 0
        painter = QtGui.QPainter()
        painter.begin(testpx)
        for px in pxlist:
            painter.drawPixmap(x,0,px)
            x += px.width()
        painter.end()
        self.testlb.setPixmap(testpx)
        
if __name__ == '__main__':
    app = QtGui.QApplication([])
    wnd = FontTool()
    wnd.show()
    wnd.resize(800,600)
    app.exec_()
