from v4l2 import *
from fcntl import *
from ctypes import *
from mmap import *
from select import *
import struct
import os
import time
import cv2
import numpy as np
import random

class camera(object):
    def __init__(self, path):
        fd = os.open(path, os.O_RDWR)

        ret = ioctl(fd, VIDIOC_S_INPUT, c_int(0))
        assert(ret == 0)

        pix_fmt = v4l2_pix_format(width=800, height=600,
                                  pixelformat=V4L2_PIX_FMT_MJPEG, field=V4L2_FIELD_NONE)
        fmt = v4l2_format(type=V4L2_BUF_TYPE_VIDEO_CAPTURE, fmt=v4l2_format._u(pix=pix_fmt))
        ret = ioctl(fd, VIDIOC_S_FMT, fmt)
        assert(ret == 0)

        parm = v4l2_streamparm(type=V4L2_BUF_TYPE_VIDEO_CAPTURE)
        ret = ioctl(fd, VIDIOC_G_PARM, parm)
        assert(ret == 0)

        parm.parm.capture.timeperframe.numerator = 1
        parm.parm.capture.timeperframe.denominator = 30

        ret = ioctl(fd, VIDIOC_S_PARM, parm)
        assert(ret == 0)

        parm = v4l2_streamparm(type=V4L2_BUF_TYPE_VIDEO_CAPTURE)
        ret = ioctl(fd, VIDIOC_G_PARM, parm)
        assert(ret == 0)

        req = v4l2_requestbuffers(count=2, type=V4L2_BUF_TYPE_VIDEO_CAPTURE, memory=V4L2_MEMORY_MMAP)
        ret = ioctl(fd, VIDIOC_REQBUFS, req)
        assert(ret == 0 and req.count == 2)

        self.buf = []
        self.data = []

        for i in range(req.count):
            buf = v4l2_buffer(type=V4L2_BUF_TYPE_VIDEO_CAPTURE, memory=V4L2_MEMORY_MMAP, index=i)
            ret = ioctl(fd, VIDIOC_QUERYBUF, buf)
            assert(ret == 0)

            data = mmap(fd, buf.length, prot=PROT_READ|PROT_WRITE, offset=buf.m.offset)

            self.buf += [buf]
            self.data += [data]

        for buf in self.buf:
            ret = ioctl(fd, VIDIOC_QBUF, buf)
            assert(ret == 0)

        ret = ioctl(fd, VIDIOC_STREAMON, c_int(V4L2_BUF_TYPE_VIDEO_CAPTURE))
        assert(ret == 0)

        self.fd = fd
        self.i = 0
        self.img = None
        self.dot = None

    def read(self):
        global editor
        global cam0
        global cam1
        global ax

        fd = self.fd
        buf = self.buf[self.i]
        data = self.data[self.i]
        self.i = (self.i + 1) % 2

        ret = ioctl(fd, VIDIOC_DQBUF, buf)
        assert(ret == 0)

        # do something
        data.seek(0)
        img_data = data.read(buf.bytesused)
        self.img = cv2.imdecode(np.fromstring(img_data, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)

        editor.update()

        print("frame on %i at %f" % (self.fd, time.perf_counter()))

        minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(self.img)

        self.dot = None
        if maxVal >= 75.0:
            self.dot = maxLoc

        if cam0.dot is not None and cam1.dot is not None:
            projMatr1 = np.matrix([
                [1365.74, 0.00, 556.89, 0],
                [0.00, 1300.12, 610.75, 0],
                [0, 0, 1.0, 0]])
            projMatr2 = np.matrix([
                [1365.74, 0.00, 556.89, 0.13],
                [0.00, 1300.12, 610.75, 0],
                [0, 0, 1.0, 0]])

            worldpoint = cv2.triangulatePoints(projMatr1, projMatr2, cam0.dot, cam1.dot)
            print(worldpoint)
            ax.scatter(worldpoint[0], worldpoint[1], worldpoint[2], marker='o')


        ret = ioctl(fd, VIDIOC_QBUF, buf)
        assert(ret == 0)

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog
from PyQt5.Qt import *
from PyQt5.QtCore import Qt
import skimage.io
import array
import os.path

from PyQt5.QtCore import pyqtSignal, QPoint, QSize, Qt
from PyQt5.QtGui import QColor, QOpenGLVersionProfile, QOpenGLShaderProgram, QOpenGLShader, QOpenGLFramebufferObject
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QOpenGLWidget, QSlider, QWidget

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.widgets import Button

"""
initialize opengl, used by editor/minimap widgets
"""
def init_gl(self):
    global vertex_shader
    global fragment_shader

    version = QOpenGLVersionProfile()
    version.setVersion(2, 1)
    self.gl = self.context().versionFunctions(version)
    self.gl.initializeOpenGLFunctions()

"""
main editor logic / rendering
"""
class MyView(QOpenGLWidget):
    def __init__(self):
        super(MyView, self).__init__()

        self.setMouseTracking(True)

        format = QSurfaceFormat()
        format.setRenderableType(QSurfaceFormat.OpenGL)
        self.setFormat(format)

    def sizeHint(self):
        return QSize(1600, 600)

    def initializeGL(self):
        init_gl(self)

    def paintGL(self):
        global cam0
        global cam1

        gl = self.gl

        gl.glViewport(0, 0, self.width(), self.height())

        gl.glLoadIdentity()

        for (x, img) in ((-1.0, cam0.img), (0.0, cam1.img)):
            if img is not None:
                qimg = QImage(img.tostring(), 800, 600, QImage.Format_Grayscale8)
                tex = QOpenGLTexture(qimg, QOpenGLTexture.DontGenerateMipMaps)
                tex.bind()

                gl.glEnable(gl.GL_TEXTURE_2D)

                gl.glColor4f(1.0, 1.0, 1.0, 1.0)
                gl.glBegin(gl.GL_TRIANGLE_STRIP)

                gl.glTexCoord2f(0.0, 1.0)
                gl.glVertex2f(x, -1.0)

                gl.glTexCoord2f(1.0, 1.0)
                gl.glVertex2f(x + 1.0, -1.0)

                gl.glTexCoord2f(0.0, 0.0)
                gl.glVertex2f(x, 1.0)

                gl.glTexCoord2f(1.0, 0.0)
                gl.glVertex2f(x + 1.0, 1.0)

                gl.glEnd()

                tex.release()

    def mousePressEvent(self, event):
        pass

    def mouseMoveEvent(self, event):
        pass

def toolbar_button(icon, text, action):
    global main_widget
    global main_toolbar

    x = QAction(icon, text, main_widget)
    x.triggered.connect(action)
    main_toolbar.addAction(x)
    return x

def action_none():
    return

if __name__ == '__main__':
    cam0 = camera('/dev/video0')
    cam1 = camera('/dev/video1')

    img_path = None

    app = QApplication([])

    main_widget = QWidget()
    editor = MyView()

    notify0 = QSocketNotifier(cam0.fd, QSocketNotifier.Read)
    notify0.activated.connect(lambda x: cam0.read())

    notify1 = QSocketNotifier(cam1.fd, QSocketNotifier.Read)
    notify1.activated.connect(lambda x: cam1.read())

    main_toolbar = QToolBar('test')

    toolbar_button(QIcon.fromTheme('document-open'), 'Open', action_none)
    toolbar_button(QIcon.fromTheme('go-previous'), 'Previous', action_none)
    toolbar_button(QIcon.fromTheme('go-next'), 'Next', action_none)
    toolbar_button(QIcon.fromTheme('document-save'), 'Save', action_none)
    toolbar_button(QIcon.fromTheme('edit-undo'), 'Undo', action_none)
    toolbar_button(QIcon.fromTheme('edit-redo'), 'Redo', action_none)

    main_toolbar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    figure = plt.figure()
    canvas = FigureCanvas(figure)

    ax = figure.add_subplot(111, projection='3d')

    toggle_scan_button = Button(plt.axes([0.04, 0.9, 0.1, 0.06]), 'Stop')
    quit_button = Button(plt.axes([0.86, 0.05, 0.1, 0.06]), 'Quit')

    """
    focal = 0.004
    baseline = 0.1

    projMatr1 = np.matrix([[1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [0, 0, 1/focal, 0]])
    projMatr2 = np.matrix([[1, 0, 0, baseline],
                        [0, 1, 0, 0],
                        [0, 0, 1/focal, 0]])

    for i in range(1):
        projPoints1 = np.array([0 + random.uniform(0.005, 0.02), 0 - random.uniform(0.005, 0.02)])
        projPoints2 = np.array([0 - random.uniform(0.005, 0.02), 0 + random.uniform(0.005, 0.02)])

        worldPoint = cv2.triangulatePoints(projMatr1, projMatr2, projPoints1, projPoints2)
        ax.scatter(worldPoint[0], worldPoint[1], worldPoint[2], marker='o')
    """

    main_layout = QVBoxLayout()
    main_layout.addWidget(canvas)
    main_layout.addWidget(editor)

    main_widget.setLayout(main_layout)
    main_widget.setWindowTitle('Logiciel Vision')
    main_widget.show()

sys.exit(app.exec_())
