from math import sqrt, sin, cos, pi, inf, acos, tan, atan2
from PyQt5.QtGui import QPolygonF, QMatrix4x4, QMatrix3x3, QTransform, QPen
from PyQt5.QtCore import QLineF, QPointF, QRectF, Qt
from cmath import exp, phase
from qt_tools import simpleMaxContrastingColor, Pen

# Geometric Transformations

def mag2D(point):
    return sqrt(point.x()**2 + point.y()**2)

def det2D(A, B):
    return A.x() * B.y() - A.y() * B.x()

def dot2D(A, B):
    return A.x() * B.x() + A.y() * B.y()
        
def debugPrintTransformMatrix(T):
    print(str(T.m11()) + '  ' + str(T.m12()) + '  ' + str(T.m13()))
    print(str(T.m21()) + '  ' + str(T.m22()) + '  ' + str(T.m23()))
    print(str(T.m31()) + '  ' + str(T.m32()) + '  ' + str(T.m33()))
    
# Assumes no shearing or stretching.   
# Only Rotation, Translation, and Scaling. 
def extractTransformScale(T):
    # This is math matrix notation transposed (debug print self.sceneTransform() to see)
    Sx = sqrt(T.m11()**2 + T.m12()**2)      
    Sy = sqrt(T.m21()**2 + T.m22()**2)
    return Sx, Sy    

def extractTransformTranslate(T):
    return T.m31(), T.m32()

def regularPolygonVertices(num, radius):
    # Create a regular n-sided poly centered at origin
    n = num
    r = radius
    verts = []
    for k in range(0, n):         # 0.. n-1
        point = (r * cos(k / n * 2 * pi), r * sin(k / n * 2 * pi))
        verts.append(point)
    return verts

def verticesToQPolygonF(verts):
    poly = QPolygonF()
    for v in verts:
        poly.append(QPointF(*v))
    return poly

def minBoundingRect(rectList):
    if rectList == []:
        return None
    
    minX = rectList[0].left()
    minY = rectList[0].top()
    maxX = rectList[0].right()
    maxY = rectList[0].bottom()
    
    for k in range(1, len(rectList)):
        minX = min(minX, rectList[k].left())
        minY = min(minY, rectList[k].top())
        maxX = max(maxX, rectList[k].right())
        maxY = max(maxY, rectList[k].bottom())

    return QRectF(minX, minY, maxX-minX, maxY-minY)

def combine3DMatrices(matrices):
    M = QMatrix4x4()
    
    for N in matrices:
        N.applyTo(M)
        
    return M

def matrix3DToTransform(M):
    M = M.data()
    T = QTransform(
        M[0], M[1], M[2],
        M[4], M[5], M[6],
        M[8], M[9], M[10])
    return T       

def rectFromTwoPoints(A, B):
    x = min(A.x(), B.x())
    y = min(A.y(), B.y())
    x1 = max(A.x(), B.x())
    y1 = max(A.y(), B.y())
    return QRectF(x, y, x1-x, y1-y)


########## Rounded rectangle intersection ########

# q = (-1,-1), (1, 1), (-1, 1), or (1, -1)
def lineIntersectCircleQuadrantAtO(line, r, q):
    A = line.p1();  B = line.p2()
    V = A - B
    a = dot2D(V, V)
    b = 2*dot2D(A, V)
    c = dot2D(A, A) - r*r
    d = b*b - 4*a*c
    if d < 0:
        return []
    d = sqrt(d)
    a *= 2
    t0 = (-b + d)/a
    t1 = (-b - d)/a
    y0 = A + V*t0
    y1 = B + V*t1
    q = QPointF(*q) * r
    rect = rectFromTwoPoints(q, QPointF(0, 0))
    isects = []
    if rect.contains(y0):
        isects.append(y0)
    if rect.contains(y1):
        isects.append(y1)
    return isects

def rectCornerFromQuadrant(rect, quad):
    if quad[0] == -1:
        x = rect.left()
    else:
        x = rect.right()
    if quad[1] == -1:
        y = rect.top()
    else:
        y = rect.bottom()
    return QPointF(x,y)

allRectQuadrants = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
allRectSides = [(-1, 0), (0, 1), (0, -1), (1, 0)]

def lineIntersectRoundRectCorners(line, rect, r, quads=None):
    if quads is None:
        quads = allRectQuadrants
    isects = []
    for q in quads:
        C = rectCornerFromQuadrant(rect, q)
        R = r * QPointF(*q)
        O = -(C + R)
        line1 = line.translated(O)
        isects.extend(lineIntersectCircleQuadrantAtO(line1, r, q))
    return isects

def lineIntersectRoundRectSides(line, rect, r, sides=None):
    if sides is None:
        sides = allRectSides
    isects = []
    
    C = line.p1()
    D = line.p2()    
    CDy = C.y() - D.y()
    CDx = C.x() - D.x()
    detCD = det2D(C,D)
    
    for side in sides:
        if side[0] == -1:
            x0 = x1 = rect.left()
            y0 = rect.top()
            y1 = rect.bottom()
        elif side[0] == 1:
            x0 = x1 = rect.right()
            y0 = rect.top()
            y1 = rect.bottom()
        elif side[1] == -1:
            y0 = y1 = rect.top()
            x0 = rect.left()
            x1 = rect.right()
        elif side[1] == 1:
            y0 = y1 = rect.bottom()
            x0 = rect.left()
            x1 = rect.right()
            
        A = QPointF(x0, y0)
        B = QPointF(x1, y1)
        
        det = (A.x() - B.x())*CDy - (A.y() - B.y())*CDx
        if det == 0.0:
            continue
        
        detAB = det2D(A,B)
        ABx = A.x() - B.x()
        ABy = A.y() - B.y()
        x = (detAB*CDx - ABx*detCD)/det
        y = (detAB*CDy - ABy*detCD)/det
        
        isects.append(QPointF(x,y))
        
    return isects

def lineIntersectRoundRect(line, rect, r):
    isects = []

    isects.extend(lineIntersectRoundedRectCorners(line, rect, r))
    isects.extend(lineIntersectRoundedRectSides(line, rect, r))
            
    return isects


def polygonPlusMidpoints(poly):
    poly1 = QPolygonF()
    
    for k in range(1, poly.count() + 1):
        j = k % poly.count()
        poly1.append(poly[k-1])
        poly1.append((poly[k-1] + poly[j])/2)
        
    return poly1


def closestCenteredPointsOfParallelLineSegments(lineA, lineB):
    a = lineA.p1();  b = lineA.p2()
    c = lineB.p1();  d = lineB.p2()
    
    #Create complex numbers
    a0 = a = a.x() + a.y()*1j
    b = b.x() + b.y()*1j
    c = c.x() + c.y()*1j
    d = d.x() + d.y()*1j
    
    # Translate all to the origin by a
    b -= a;  c -= a;  d -= a;  a -= a

    phi = phase(b)
    R = exp(-1j * phi)
    
    # Rotate all to be parallel with x-axis
    b *= R;  c *= R;  d *= R
    
    a1 = min(a.real, b.real);  b1 = max(a.real, b.real)
    c1 = min(c.real, d.real);  d1 = max(c.real, d.real)
    e1 = max(a1, c1);  f1 = min(b1, d1)
    if f1 <= e1:  # empty / negative interval
        A = f1 + 0j
        B = e1 + 0j
    else:
        A = (f1 + e1)/2 + 0j
        B = A + d.imag * 1j  # offset to c,d line
        
    # Rotate back into place
    R = R.conjugate()
    A *= R;  B *= R
    
    # Translate back into place
    A += a0;  B += a0
    
    return QPointF(A.real, A.imag), QPointF(B.real, B.imag)

            
def boundingPolygonOfCircle(radius, sides):
    n = sides
    t = 2*pi/n
    r = radius / cos(t/2)
    poly = QPolygonF()
    for k in range(0, n):
        poly.append(QPointF(r*cos(t*k), r*sin(t*k)))
    return poly
    

# BUGFIX: Qt's QPolygonF ctor makes a polygon with 5 points for some reason
def rectToPoly(rect):
    poly = QPolygonF()
    poly.append(rect.topLeft())
    poly.append(rect.topRight())
    poly.append(rect.bottomRight())
    poly.append(rect.bottomLeft())
    return poly


def maxZValueItem(items):
    max_item = items[0]
    max_z = max_item.zValue()
    
    for k in range(1, len(items)):
        if items[k].zValue() > max_z:
            max_item = items[k]
            max_z = items[k].zValue()
    
    return max_item


def closestPolyPoint(poly, point):
    min_d = mag2D(poly[0] - point)
    min_point = poly[0]
    min_k = 0
    
    for k in range(1, poly.count()):
        d = mag2D(poly[k] - point)
        if d < min_d:
            min_k = k
            min_d = d
            min_point = poly[k]
            
    return min_point, min_k


def closestRectPoint(rect, point):
    poly = rectToPoly(rect)
    return closestPolyPoint(poly, point)
    

def debugPrintPoly(poly):
    string = '{'
    for k in range(0, poly.count()):
        string += str(poly[k]) + ', '
    string = string[0:-2] + '}'
    print(string)
    

def rectContainsRect(r0, r1):
    return r0.contains(r1.topLeft()) and r0.contains(r1.topRight()) and r0.contains(r1.bottomRight()) and r0.contains(r1.bottomLeft())


def orthogonalRectDelta(r0, r1):
    pairs = ((r0.top(), r1.bottom()), (r0.bottom(), r1.top()), (r0.left(), r1.right()), (r0.right(), r1.left()))

    min_d = inf
    min_delta = None
    
    for k in range(0, len(pairs)):
        p = pairs[k]
        d = p[0] - p[1]
        if abs(d) < min_d:
            min_d = abs(d)
            min_delta = QPointF(0, d) if k < 2 else QPointF(d, 0)
            
    return min_delta
        
    
def paintSelectionShape(painter, item):
    path = item.shape()
    # Local transform doesn't include translation in scene
    P = painter.transform()
    s = extractTransformScale(P)
    s = (s[0], s[1])
    T = item.transform() 
    T *= matrix3DToTransform(combine3DMatrices(item.transformations()))
    T *= QTransform.fromScale(*s)
    path = T.map(path)
    painter.save()
    painter.resetTransform()
    dx, dy = extractTransformTranslate(P)
    painter.translate(dx, dy)
    col = simpleMaxContrastingColor(item.scene().backgroundBrush().color())
    col1 = simpleMaxContrastingColor(col)
    painter.strokePath(path, QPen(col1, 1.0))
    painter.strokePath(path, QPen(col, 1.0, Qt.DashLine))
    painter.restore()        
    
    
def polygonFromArc(center, radius, start, end, seg):
    poly = QPolygonF()
    for k in range(0, seg):
        theta = 2 * pi / 360 * (start + k * (end - start) / seg)
        point = center + radius * QPointF(cos(theta), sin(theta))
        poly.append(point)
    return poly