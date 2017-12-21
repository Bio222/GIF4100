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

        pix_fmt = v4l2_pix_format(width=640, height=480,
                                  pixelformat=V4L2_PIX_FMT_YUYV, field=V4L2_FIELD_NONE)
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
        self.x = None
        self.y = None

    def read(self):
        global editor
        global cam0
        global cam1
        global points

        fd = self.fd
        buf = self.buf[self.i]
        data = self.data[self.i]
        self.i = (self.i + 1) % 2

        ret = ioctl(fd, VIDIOC_DQBUF, buf)
        assert(ret == 0)

        # do something
        data.seek(0)
        img_data = data.read(buf.bytesused)
        img0 = np.fromstring(img_data[::2], dtype=np.uint8).reshape((480, 640))
        #self.img = cv2.imdecode(np.fromstring(img_data, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)

        """
        u = np.repeat(np.fromstring(img_data[1::4], dtype=np.uint8), 2)
        v = np.repeat(np.fromstring(img_data[3::4], dtype=np.uint8), 2)

        yuv = np.zeros((640*480*3), dtype=np.uint8)
        yuv[0::3] = img0.flatten()
        yuv[1::3] = u
        yuv[2::3] = v

        print(cam0.fd, self.fd)

        yuv = yuv.reshape((480, 640, 3))

        bgr = cv2.cvtColor(yuv,cv2.COLOR_YUV2BGR)

        cv2.imwrite('bgr.png', bgr)
        cv2.imwrite('y.png', img0)
        cv2.imwrite('u.png', u.reshape((480, 640)))
        cv2.imwrite('v.png', v.reshape((480, 640)))

        cv2.imshow('i', bgr)
        cv2.waitKey(0)

        cv2.imshow('i', img0)
        cv2.waitKey(0)

        cv2.imshow('i', u.reshape((480, 640)))
        cv2.waitKey(0)

        cv2.imshow('i', v.reshape((480, 640)))
        cv2.waitKey(0)
        """


        """
        img = cv2.GaussianBlur(img0,(3,3),0)

        ret, img = cv2.threshold(img,64,255,cv2.THRESH_BINARY)

        contours = cv2.findContours(img, cv2.RETR_EXTERNAL,
                                     cv2.CHAIN_APPROX_SIMPLE)[1]

        #img2 = np.zeros((480, 640), dtype=np.uint8)

        results = []

        for c in contours:
            area = cv2.contourArea(c)
            if area < 4.0 or area > 50.0:
                continue

            arclength = cv2.arcLength(c,True)

            if arclength > 15.0:
                continue

            #print(area, arclength)

            results += [c]

            #cv2.drawContours(img2, [c], -1, 255, -1)

        if len(results) == 1:
            c = results[0]

            ((x, y), radius) = cv2.minEnclosingCircle(c)
            self.x = x
            self.y = y
        else:
            self.x = None
            self.y = None

        #print(contour)

        self.img = img0
        """

        img = cv2.GaussianBlur(img0,(5,5),0)
        ret, img = cv2.threshold(img,64,255,cv2.THRESH_BINARY)

        minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(img)
        self.img = img0

        contours = cv2.findContours(img, cv2.RETR_EXTERNAL,
                                     cv2.CHAIN_APPROX_SIMPLE)[1]

        if (len(contours)) == 1:
            c = contours[0]
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            self.x = x
            self.y = y

            if cam0.x is not None and cam1.x is not None:
                projMatr1 = np.matrix([
                    [1365.74, 0.00, 556.89, 0],
                    [0.00, 1300.12, 610.75, 0],
                    [0, 0, 1.0, 0]])
                projMatr2 = np.matrix([
                    [1365.74, 0.00, 556.89, 0.13],
                    [0.00, 1300.12, 610.75, 0],
                    [0, 0, 1.0, 0]])

                worldpoint = cv2.triangulatePoints(projMatr1, projMatr2, (cam0.x, cam0.y), (cam1.x, cam1.y))
                if is_scanning:
                    points += [worldpoint]
                #ax.scatter(worldpoint[0], worldpoint[1], worldpoint[2], marker='o')

        else:
            self.x = None
            self.y = None


        editor.update()

        """

        print("frame on %i at %f %i" % (self.fd, time.perf_counter(), len(img_data)))

        minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(self.img)

        print(maxVal)

        contours = cv2.findContours(self.img, cv2.RETR_EXTERNAL,
                                     cv2.CHAIN_APPROX_SIMPLE)[-2]
        if len(contours) > 0:
            c = max(contours, key=cv2.contourArea)
            print(c)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            print(x, y, radius)


        self.dot = None
        if maxVal >= 255.0:
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

            points.extend([*worldpoint])

            #ax.scatter(worldpoint[0], worldpoint[1], worldpoint[2], marker='o')

        """


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
        return QSize(1280, 480)

    def initializeGL(self):
        init_gl(self)

    def paintGL(self):
        global cam0
        global cam1
        #global points

        gl = self.gl

        """
        gl.glViewport(0, 480, self.width(), self.height() - 480)

        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        gl.glLoadIdentity();
        gl.glFrustum(-1.0, 1.0, -1.0, 1.0, 1.0, 1024.0)

        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        gl.glPointSize(4.0)

        gl.glDisable(gl.GL_TEXTURE_2D)

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glVertexPointer(3, gl.GL_FLOAT, 0, points)
        gl.glDrawArrays(gl.GL_POINTS, 0, len(points) // 3)

        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        """

        gl.glLoadIdentity()

        gl.glViewport(0, 0, self.width(), 480)

        for (x, cam) in ((-1.0, cam0), (0.0, cam1)):
            if cam.img is not None:
                qimg = QImage(cam.img.tostring(), 640, 480, QImage.Format_Grayscale8)
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


                if cam.x is not None:
                    gl.glDisable(gl.GL_TEXTURE_2D)

                    gl.glPointSize(5.0)

                    gl.glColor4f(1.0, 0.0, 0.0, 1.0)
                    gl.glBegin(gl.GL_POINTS)


                    gl.glVertex2f(x + cam.x / 640.0, (480.0 - cam.y * 2.0) / 480.0)

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

def toggle_scan(object):
    global is_scanning
    global toggle_scan_button
    global points_ax
    global points
    global ax
    is_scanning = not is_scanning
    if (is_scanning):
        toggle_scan_button.label.set_text("Stop")
        if points_ax is not None:
            points_ax.remove()
            points_ax = None
    else:
        toggle_scan_button.label.set_text("Start")
        x = [p[0] for p in points]
        y = [p[1] for p in points]
        z = [p[2] for p in points]

        points_ax = ax.scatter(x, y, z, marker='o')
        points = []

if __name__ == '__main__':
    img_path = None

    app = QApplication([])

    main_widget = QWidget()
    editor = MyView()

    cam0 = camera('/dev/video0')
    cam1 = camera('/dev/video1')

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
    points_ax = None

    is_scanning = False

    toggle_scan_button = Button(plt.axes([0.04, 0.9, 0.1, 0.06]), 'Start')
    toggle_scan_button.on_clicked(toggle_scan)
    quit_button = Button(plt.axes([0.86, 0.05, 0.1, 0.06]), 'Quit')

    points = []

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
