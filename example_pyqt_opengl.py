import sys
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog
from PyQt5.Qt import *
from PyQt5.QtCore import Qt
import skimage.io
import numpy as np
import array
import os.path
import struct

from PyQt5.QtCore import pyqtSignal, QPoint, QSize, Qt
from PyQt5.QtGui import QColor, QOpenGLVersionProfile, QOpenGLShaderProgram, QOpenGLShader, QOpenGLFramebufferObject
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QOpenGLWidget, QSlider, QWidget

vertex_shader = '''
attribute highp vec2 pos;
varying highp vec2 coord;
uniform highp vec4 matrix;
void main() {
    coord = pos;
    gl_Position = vec4(matrix.xy * pos + matrix.zw, 0.0, 1.0);
}
'''

fragment_shader = '''
varying highp vec2 coord;
void main() {
    gl_FragColor = vec4(coord, 1.0, 1.0);
}
'''

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

    self.program = QOpenGLShaderProgram(self)
    self.program.addShaderFromSourceCode(QOpenGLShader.Vertex, vertex_shader)
    self.program.addShaderFromSourceCode(QOpenGLShader.Fragment, fragment_shader)
    self.program.link()

    self.m_pos = self.program.attributeLocation('pos')
    self.m_matrix = self.program.uniformLocation('matrix')

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
        return QSize(800, 800)

    def initializeGL(self):
        init_gl(self)

    def paintGL(self):
        gl = self.gl

        gl.glViewport(0, 0, self.width(), self.height())

        # with shader
        self.program.bind()

        self.program.setUniformValue(self.m_matrix, 1.0, 1.0, -1.0, 0.0)

        vertices = array.array('f', [0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0])
        gl.glEnableVertexAttribArray(self.m_pos)
        gl.glVertexAttribPointer(self.m_pos, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, vertices)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)

        self.program.release()

        # without shader
        gl.glLoadIdentity()
        gl.glColor4f(1.0, 0.0, 0.0, 1.0)
        gl.glBegin(gl.GL_TRIANGLE_STRIP)
        gl.glVertex2f(0.0, 0.0)
        gl.glVertex2f(1.0, 0.0)
        gl.glVertex2f(0.0, 1.0)
        gl.glVertex2f(1.0, 1.0)
        gl.glEnd()

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
    img_path = None

    app = QApplication([])

    main_widget = QWidget()
    editor = MyView()

    main_toolbar = QToolBar('test')

    toolbar_button(QIcon.fromTheme('document-open'), 'Open', action_none)
    toolbar_button(QIcon.fromTheme('go-previous'), 'Previous', action_none)
    toolbar_button(QIcon.fromTheme('go-next'), 'Next', action_none)
    toolbar_button(QIcon.fromTheme('document-save'), 'Save', action_none)
    toolbar_button(QIcon.fromTheme('edit-undo'), 'Undo', action_none)
    toolbar_button(QIcon.fromTheme('edit-redo'), 'Redo', action_none)

    main_toolbar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    main_layout = QVBoxLayout()
    main_layout.addWidget(main_toolbar)
    main_layout.addWidget(editor)

    main_widget.setLayout(main_layout)
    main_widget.setWindowTitle('Logiciel Vision')
    main_widget.show()

    sys.exit(app.exec_())
