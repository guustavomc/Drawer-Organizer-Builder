import math
import numpy as np

from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *

from model import OrganizerModel

# ─────────────────────────────────────────────
#  3-D OpenGL preview
# ─────────────────────────────────────────────

class GLPreview(QOpenGLWidget):
    def __init__(self, model: OrganizerModel):
        super().__init__()
        self.model = model
        self._triangles = []
        self._rot_x = 30.0
        self._rot_z = -45.0
        self._zoom = 1.0
        self._last_pos = None
        self.setMinimumSize(300, 300)

    def refresh(self):
        self._triangles = self.model.build_triangles()
        self.update()

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightfv(GL_LIGHT0, GL_POSITION, [1, 2, 3, 0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1, 1, 1, 1])
        glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.25, 0.25, 0.25, 1])
        glClearColor(0.12, 0.12, 0.18, 1)
        self._triangles = self.model.build_triangles()

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        w, h = self.width(), self.height()
        aspect = w / h if h else 1
        diag = math.sqrt(self.model.width**2 + self.model.depth**2 + self.model.height**2)
        gluPerspective(45, aspect, 1, diag * 10)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        dist = diag * 1.5 / self._zoom
        gluLookAt(0, 0, dist, 0, 0, 0, 0, 1, 0)

        cx = self.model.width / 2
        cy = self.model.depth / 2
        cz = self.model.height / 2
        glTranslatef(-cx, -cy, -cz)
        # rotate around centre
        glTranslatef(cx, cy, cz)
        glRotatef(self._rot_x, 1, 0, 0)
        glRotatef(self._rot_z, 0, 0, 1)
        glTranslatef(-cx, -cy, -cz)

        glColor3f(0.36, 0.58, 0.87)
        glBegin(GL_TRIANGLES)
        for v0, v1, v2 in self._triangles:
            n = np.cross(v1 - v0, v2 - v0)
            ln = np.linalg.norm(n)
            if ln > 0:
                n = n / ln
            glNormal3f(*n)
            glVertex3f(*v0)
            glVertex3f(*v1)
            glVertex3f(*v2)
        glEnd()

    def mousePressEvent(self, event):
        self._last_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self._last_pos:
            dx = event.pos().x() - self._last_pos.x()
            dy = event.pos().y() - self._last_pos.y()
            self._rot_z += dx * 0.5
            self._rot_x += dy * 0.5
            self._last_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self._last_pos = None

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self._zoom *= (1.1 if delta > 0 else 0.9)
        self._zoom = max(0.2, min(10.0, self._zoom))
        self.update()
