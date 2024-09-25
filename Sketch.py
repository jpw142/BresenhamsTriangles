"""
This is the main entry of your program. Almost all things you need to implement is in this file.
The main class Sketch inherit from CanvasBase. For the parts you need to implement, they all marked TODO.
First version Created on 09/28/2018

:author: micou(Zezhou Sun)
:version: 2021.2.1

Jack Weber U97268134
I added the draw line method that uses bresenham's algorithm along with some adjustments for different slope cases to draw line
- Has option of smooth / flat shading
I changed it so the draw line call with left click actually calls the drawLine method
I added a method pointsOnLine that does bresenhams but doesn't draw and instead returns a list of the points it would draw
I added a drawTriangle method that first makes sure there is a flat bottom and if not splits the triangle in half from the middle vertex using the pointsOnLine method
Then it gets the points for the two non flat sides of the triangle, makes sure they are lined up starting at the same y
Then it scanlines between those two lines making sure to only draw 1 line because there are edge cases were many lines were drawn for the same y
- Has option of smooth / flat shading
Then I made it so the right click method draws a line between the first two points and then draws a triangle when it has 3 points
"""

import os

import wx
import math
import random
import numpy as np

from Buff import Buff
from Point import Point
from ColorType import ColorType
from CanvasBase import CanvasBase

try:
    # From pip package "Pillow"
    from PIL import Image
except Exception:
    print("Need to install PIL package. Pip package name is Pillow")
    raise ImportError


class Sketch(CanvasBase):
    """
    Please don't forget to override interrupt methods, otherwise NotImplementedError will throw out
    
    Class Variable Explanation:

    * debug(int): Define debug level for log printing

        * 0 for stable version, minimum log is printed
        * 1 will print general logs for lines and triangles
        * 2 will print more details and do some type checking, which might be helpful in debugging
    
    * texture(Buff): loaded texture in Buff instance
    * random_color(bool): Control flag of random color generation of point.
    * doTexture(bool): Control flag of doing texture mapping
    * doSmooth(bool): Control flag of doing smooth
    * doAA(bool): Control flag of doing anti-aliasing
    * doAAlevel(int): anti-alising super sampling level
        
    Method Instruction:

    * Interrupt_MouseL(R): Used to deal with mouse click interruption. Canvas will be refreshed with updated buff
    * Interrupt_Keyboard: Used to deal with key board press interruption. Use this to add new keys or new methods
    * drawPoint: method to draw a point
    * drawLine: method to draw a line
    * drawTriangle: method to draw a triangle with filling and smoothing
    
    List of methods to override the ones in CanvasBase:

    * Interrupt_MouseL
    * Interrupt_MouseR
    * Interrupt_Keyboard
        
    Here are some public variables in parent class you might need:

    * points_r: list<Point>. to store all Points from Mouse Right Button
    * points_l: list<Point>. to store all Points from Mouse Left Button
    * buff    : Buff. buff of current frame. Change on it will change display on screen
    * buff_last: Buff. Last frame buffer
        
    """

    debug = 0
    texture_file_path = "./pattern.jpg"
    texture = None

    # control flags
    randomColor = False
    doTexture = False
    doSmooth = False
    doAA = False
    doAAlevel = 4

    # test case status
    MIN_N_STEPS = 6
    MAX_N_STEPS = 192
    n_steps = 12  # For test case only
    test_case_index = 0
    test_case_list = []  # If you need more test case, write them as a method and add it to list

    def __init__(self, parent):
        """
        Initialize the instance, load texture file to Buff, and load test cases.

        :param parent: wxpython frame
        :type parent: wx.Frame
        """
        super(Sketch, self).__init__(parent)
        self.test_case_list = [lambda _: self.clear(),
                               self.testCaseLine01,
                               self.testCaseLine02,
                               self.testCaseTri01,
                               self.testCaseTri02,
                               self.testCaseTriTexture01]  # method at here must accept one argument, n_steps
        # Try to read texture file
        if os.path.isfile(self.texture_file_path):
            # Read image and make it to an ndarray
            texture_image = Image.open(self.texture_file_path)
            texture_array = np.array(texture_image).astype(np.uint8)
            # Because imported image is upside down, reverse it
            texture_array = np.flip(texture_array, axis=0)
            # Store texture image in our Buff format
            self.texture = Buff(texture_array.shape[1], texture_array.shape[0])
            self.texture.setStaticBuffArray(np.transpose(texture_array, (1, 0, 2)))
            if self.debug > 0:
                print("Texture Loaded with shape: ", texture_array.shape)
                print("Texture Buff have size: ", self.texture.size)
        else:
            raise ImportError("Cannot import texture file")

    def __addPoint2Pointlist(self, pointlist, x, y):
        if self.randomColor:
            p = Point((x, y), ColorType(random.random(), random.random(), random.random()))
        else:
            p = Point((x, y), ColorType(1, 0, 0))
        pointlist.append(p)

    # Deal with Mouse Left Button Pressed Interruption
    def Interrupt_MouseL(self, x, y):
        self.__addPoint2Pointlist(self.points_l, x, y)
        # Draw a point when one point provided or a line when two ends provided
        if len(self.points_l) % 2 == 1:
            if self.debug > 0:
                print("point 1 for line", self.points_l[-1])
        elif len(self.points_l) % 2 == 0 and len(self.points_l) > 0:
            if self.debug > 0:
                print("draw a line from ", self.points_l[-1], " -> ", self.points_l[-2])
            # Allow it to draw lines when clicking
            self.drawLine(self.buff, self.points_l[-1], self.points_l[-2], doSmooth = self.doSmooth)
            self.points_l.clear()

    # Deal with Mouse Right Button Pressed Interruption
    def Interrupt_MouseR(self, x, y):
        self.__addPoint2Pointlist(self.points_r, x, y)
        if len(self.points_r) % 3 == 2:
            if self.debug > 0:
                print("draw a line from ", self.points_r[-1], " -> ", self.points_r[-2])
            self.drawLine(self.buff, self.points_r[-2], self.points_r[-1], doSmooth= self.doSmooth)
        elif len(self.points_r) % 3 == 0 and len(self.points_r) > 0:
            if self.debug > 0:
                print("draw a triangle {} -> {} -> {}".format(self.points_r[-3], self.points_r[-2], self.points_r[-1]))
            # Draws triangle with the 3 points
            self.drawTriangle(self.buff, self.points_r[-3], self.points_r[-2], self.points_r[-1], doSmooth= self.doSmooth)
            self.points_r.clear()

    def Interrupt_Keyboard(self, keycode):
        """
        keycode Reference: https://docs.wxpython.org/wx.KeyCode.enumeration.html#wx-keycode

        * r, R: Generate Random Color point
        * c, C: clear buff and screen
        * LEFT, UP: Last Test case
        * t, T, RIGHT, DOWN: Next Test case
        """
        # Trigger for test cases
        if keycode in [wx.WXK_LEFT, wx.WXK_UP]:  # Last Test Case
            self.clear()
            if len(self.test_case_list) != 0:
                self.test_case_index = (self.test_case_index - 1) % len(self.test_case_list)
            self.test_case_list[self.test_case_index](self.n_steps)
            print("Display Test case: ", self.test_case_index, "n_steps: ", self.n_steps)
        if keycode in [ord("t"), ord("T"), wx.WXK_RIGHT, wx.WXK_DOWN]:  # Next Test Case
            self.clear()
            if len(self.test_case_list) != 0:
                self.test_case_index = (self.test_case_index + 1) % len(self.test_case_list)
            self.test_case_list[self.test_case_index](self.n_steps)
            print("Display Test case: ", self.test_case_index, "n_steps: ", self.n_steps)
        if chr(keycode) in ",<":
            self.clear()
            self.n_steps = max(self.MIN_N_STEPS, round(self.n_steps / 2))
            self.test_case_list[self.test_case_index](self.n_steps)
            print("Display Test case: ", self.test_case_index, "n_steps: ", self.n_steps)
        if chr(keycode) in ".>":
            self.clear()
            self.n_steps = min(self.MAX_N_STEPS, round(self.n_steps * 2))
            self.test_case_list[self.test_case_index](self.n_steps)
            print("Display Test case: ", self.test_case_index, "n_steps: ", self.n_steps)

        # Switches
        if chr(keycode) in "rR":
            self.randomColor = not self.randomColor
            print("Random Color: ", self.randomColor)
        if chr(keycode) in "cC":
            self.clear()
            print("clear Buff")
        if chr(keycode) in "sS":
            self.doSmooth = not self.doSmooth
            print("Do Smooth: ", self.doSmooth)
        if chr(keycode) in "aA":
            self.doAA = not self.doAA
            print("Do Anti-Aliasing: ", self.doAA)
        if chr(keycode) in "mM":
            self.doTexture = not self.doTexture
            print("texture mapping: ", self.doTexture)

    def queryTextureBuffPoint(self, texture: Buff, x: int, y: int) -> Point:
        """
        Query a point at texture buff, should only be used in texture buff query

        :param texture: The texture buff you want to query from
        :type texture: Buff
        :param x: The query point x coordinate
        :type x: int
        :param y: The query point y coordinate
        :type y: int
        :rtype: Point
        """
        if self.debug > 1:
            if x != min(max(0, int(x)), texture.width - 1):
                print("Warning: Texture Query x coordinate outbound")
            if y != min(max(0, int(y)), texture.height - 1):
                print("Warning: Texture Query y coordinate outbound")
        return texture.getPointFromPointArray(x, y)

    @staticmethod
    def drawPoint(buff, point):
        """
        Draw a point on buff

        :param buff: The buff to draw point on
        :type buff: Buff
        :param point: A point to draw on buff
        :type point: Point
        :rtype: None
        """
        x, y = point.coords
        c = point.color
        # because we have already specified buff.buff has data type uint8, type conversion will be done in numpy
        buff.buff[x, y, 0] = c.r * 255
        buff.buff[x, y, 1] = c.g * 255
        buff.buff[x, y, 2] = c.b * 255


    def drawLine(self, buff, p1, p2, doSmooth=True, doAA=False, doAAlevel=4):
        """
        Draw a line between p1 and p2 on buff

        :param buff: The buff to edit
        :type buff: Buff
        :param p1: One end point of the line
        :type p1: Point
        :param p2: Another end point of the line
        :type p2: Point
        :param doSmooth: Control flag of color smooth interpolation
        :type doSmooth: bool
        :param doAA: Control flag of doing anti-aliasing
        :type doAA: bool
        :param doAAlevel: anti-aliasing super sampling level
        :type doAAlevel: int
        :rtype: None
        """
        ##### TODO 1: Use Bresenham algorithm to draw a line between p1 and p2 on buff.
        # Requirements:
        #   1. Only integer is allowed in interpolate point coordinates between p1 and p2
        #   2. Float number is allowed in interpolate point color

        p1_x, p1_y = p1.getCoords()
        p1_c = p1.getColor()
        p2_x, p2_y = p2.getCoords()
        p2_c = p2.getColor()
        
        # If it's shallow do it in perspective of X
        if abs(p2_y - p1_y) <= abs(p2_x - p1_x):
            # Left to right in x
            if p1_x < p2_x:
                l_c = p1_c # Left Color
                l_x = p1_x # Left X
                l_y = p1_y # Left Y
                r_c = p2_c # Right Color
                r_x = p2_x # Right X
                r_y = p2_y # Right Y
            else:
                l_c = p2_c # Left Color
                l_x = p2_x # Left X
                l_y = p2_y # Left Y
                r_c = p1_c # Right Color
                r_x = p1_x # Right X
                r_y = p1_y # Right Y

            # Keeping slope as integers so just seperate dx and dy
            dx = r_x - l_x
            dy = r_y - l_y

            
            ji = 1
            # At this point we can only have shallow positive -> shallow negative lines
            # Allowed to only check dy as negative because dx is always positive due to choosing order
            if dy < 0:
                ji = -1 # If the slope is negative decrement instead of increment 
                dy = dy * -1 # act as if we are going up but instead just go down the same amount

            # Precompute important terms
            dy2 = dy * 2
            dy2dx2 = dy2  - (dx * 2)
            #D0
            D = dy2 - dx
            j = l_y
            # We want to include the last point
            for i in range(l_x, r_x + 1):
                # Smooth Shading
                if doSmooth:
                    if dx == 0:
                        t = 1
                    else:
                        t = (i - l_x) / dx
                    t_inv = 1 - t
                    # This is just the lerp between each of the color channels
                    r = t_inv * l_c.r + t * r_c.r 
                    g = t_inv * l_c.g + t * r_c.g
                    b = t_inv * l_c.b + t * r_c.b
                    color = ColorType(r, g, b) 
                # Flat Shading
                else:
                    color = p1_c # Color is chosen by first point
                point = Point([i, j], color)
                self.drawPoint(buff, point)
                # If D decides to move rows
                if D > 0:
                    j = j + ji # Increment / Decrement
                    D = D + dy2dx2 # Derived in class
                else:
                    D = D + dy2 # If it doesn't go up then y_k+1 - y_k = 0 and that cancels out dx
                

        # If it's steep do it in perspective of Y
        else:
            # Left to right in perspective y
            if p1_y < p2_y:
                l_c = p1_c # Left Color
                l_y = p1_y # Left Y
                l_x = p1_x # Left X
                r_c = p2_c # Right Color
                r_y = p2_y # Right Y
                r_x = p2_x # Right X
            else:
                l_c = p2_c # Left Color
                l_y = p2_y # Left Y
                l_x = p2_x # Left X
                r_c = p1_c # Right Color
                r_y = p1_y # Right Y
                r_x = p1_x # Right X

            # Keeping slope as integers so just seperate dx and dy
            dy = r_y - l_y
            dx = r_x - l_x

            
            ii = 1
            # At this point we can only have shallow positive -> shallow negative lines y perspective
            # Allowed to only check dx as negative because dy is always positive due to choosing order
            if dx < 0:
                ii = -1 # If the slope is negative decrement instead of increment 
                dx = dx * -1 # act as if we are going up but instead just go down the same amount

            # Precompute important terms
            dx2 = dx * 2
            dx2dy2 = dx2  - (dy * 2)
            
            # D0
            D = dx2 - dy
            i = l_x
            # We want to include the last point
            for j in range(l_y, r_y + 1):
                if doSmooth:
                    t = (j - l_y) / dy
                    t_inv = 1 - t
                    # This is just the lerp between each of the color channels
                    r = t_inv * l_c.r + t * r_c.r 
                    g = t_inv * l_c.g + t * r_c.g
                    b = t_inv * l_c.b + t * r_c.b
                    color = ColorType(r, g, b) 
                # Flat Shading
                else:
                    color = p1_c # Color is chosen by first point
                point = Point([i, j], color)
                self.drawPoint(buff, point)
                if D > 0:
                    i = i + ii
                    D = D + dx2dy2
                else:
                    # If it doesn't go up then x_k+1 - x_k = 0 and that cancels out dy
                    D = D + dx2
        return

    # Does Bresenham but doesn't draw and rather returns a list of points it would have drawn
    # Purpose is to not do any unintended behavior in the regular drawLine function
    # Note doesn't need buff because it's not drawing
    def pointsOnLine(self, p1, p2, doSmooth=True, doAA=False, doAAlevel=4):
        pointList = []
        
        p1_x, p1_y = p1.getCoords()
        p1_c = p1.getColor()
        p2_x, p2_y = p2.getCoords()
        p2_c = p2.getColor()
        
        # If it's shallow do it in perspective of X
        if abs(p2_y - p1_y) <= abs(p2_x - p1_x):
            # Left to right in x
            if p1_x < p2_x:
                l_c = p1_c # Left Color
                l_x = p1_x # Left X
                l_y = p1_y # Left Y
                r_c = p2_c # Right Color
                r_x = p2_x # Right X
                r_y = p2_y # Right Y
            else:
                l_c = p2_c # Left Color
                l_x = p2_x # Left X
                l_y = p2_y # Left Y
                r_c = p1_c # Right Color
                r_x = p1_x # Right X
                r_y = p1_y # Right Y

            # Keeping slope as integers so just seperate dx and dy
            dx = r_x - l_x
            dy = r_y - l_y

            
            ji = 1
            # At this point we can only have shallow positive -> shallow negative lines
            # Allowed to only check dy as negative because dx is always positive due to choosing order
            if dy < 0:
                ji = -1 # If the slope is negative decrement instead of increment 
                dy = dy * -1 # act as if we are going up but instead just go down the same amount

            # Precompute important terms
            dy2 = dy * 2
            dy2dx2 = dy2  - (dx * 2)

            # D0
            D = dy2 - dx
            j = l_y
            # We want to include the last point
            for i in range(l_x, r_x + 1):
                # Smooth Shading
                if doSmooth:
                    t = (i - l_x) / dx
                    t_inv = 1 - t
                    # This is just the lerp between each of the color channels
                    r = t_inv * l_c.r + t * r_c.r 
                    g = t_inv * l_c.g + t * r_c.g
                    b = t_inv * l_c.b + t * r_c.b
                    color = ColorType(r, g, b) 
                # Flat Shading
                else:
                    color = p1_c # Color is chosen by first point
                point = Point([i, j], color)
                pointList.append(point)
                # If D decides to move rows
                if D > 0:
                    j = j + ji # Increment / Decrement
                    D = D + dy2dx2 # Derived in class
                else:
                    D = D + dy2 # If it doesn't go up then y_k+1 - y_k = 0 and that cancels out dx
                

        # If it's steep do it in perspective of Y
        else:
            # Left to right in perspective y
            if p1_y < p2_y:
                l_c = p1_c # Left Color
                l_y = p1_y # Left Y
                l_x = p1_x # Left X
                r_c = p2_c # Right Color
                r_y = p2_y # Right Y
                r_x = p2_x # Right X
            else:
                l_c = p2_c # Left Color
                l_y = p2_y # Left Y
                l_x = p2_x # Left X
                r_c = p1_c # Right Color
                r_y = p1_y # Right Y
                r_x = p1_x # Right X

            # Keeping slope as integers so just seperate dx and dy
            dy = r_y - l_y
            dx = r_x - l_x

            
            ii = 1
            # At this point we can only have shallow positive -> shallow negative lines y perspective
            # Allowed to only check dx as negative because dy is always positive due to choosing order
            if dx < 0:
                ii = -1 # If the slope is negative decrement instead of increment 
                dx = dx * -1 # act as if we are going up but instead just go down the same amount

            # Precompute important terms
            dx2 = dx * 2
            dx2dy2 = dx2  - (dy * 2)

            D = dx2 - dy
            i = l_x
            # We want to include the last point
            for j in range(l_y, r_y + 1):
                if doSmooth:
                    t = (j - l_y) / dy
                    t_inv = 1 - t
                    # This is just the lerp between each of the color channels
                    r = t_inv * l_c.r + t * r_c.r 
                    g = t_inv * l_c.g + t * r_c.g
                    b = t_inv * l_c.b + t * r_c.b
                    color = ColorType(r, g, b) 
                # Flat Shading
                else:
                    color = p1_c # Color is chosen by first point
                point = Point([i, j], color)
                pointList.append(point)
                if D > 0:
                    i = i + ii
                    D = D + dx2dy2
                else:
                    # If it doesn't go up then x_k+1 - x_k = 0 and that cancels out dy
                    D = D + dx2
        return pointList

    def drawTriangle(self, buff, p1, p2, p3, doSmooth=True, doAA=False, doAAlevel=4, doTexture=False):
        """
        draw Triangle to buff. apply smooth color filling if doSmooth set to true, otherwise fill with first point color
        if doAA is true, apply anti-aliasing to triangle based on doAAlevel given.

        :param buff: The buff to edit
        :type buff: Buff
        :param p1: First triangle vertex
        :param p2: Second triangle vertex
        :param p3: Third triangle vertex
        :type p1: Point
        :type p2: Point
        :type p3: Point
        :param doSmooth: Color smooth filling control flag
        :type doSmooth: bool
        :param doAA: Anti-aliasing control flag
        :type doAA: bool
        :param doAAlevel: Anti-aliasing super sampling level
        :type doAAlevel: int
        :param doTexture: Draw triangle with texture control flag
        :type doTexture: bool
        :rtype: None
        """
        ##### TODO 2: Write a triangle rendering function, which support smooth bilinear interpolation of the vertex color
        ##### TODO 3(For CS680 Students): Implement texture-mapped fill of triangle. Texture is stored in self.texture
        # Requirements:
        #   1. For flat shading of the triangle, use the first vertex color.
        #   2. Polygon scan fill algorithm and the use of barycentric coordinate are not allowed in this function
        #   3. You should be able to support both flat shading and smooth shading, which is controlled by doSmooth
        #   4. For texture-mapped fill of triangles, it should be controlled by doTexture flag.

        p1_x, p1_y = p1.getCoords()
        p2_x, p2_y = p2.getCoords()
        p3_x, p3_y = p3.getCoords()
        
        # Not entirely necessary but just makes it more robust and is for my sanity
        if not doSmooth:
            p2.setColor(p1.getColor())
            p3.setColor(p1.getColor())

       # Set equal vertices to v1 and v2 and other vertice to v3
       # The flat bottom will be v1 -> v2 no matter what
        if p1_y == p2_y:
            v1 = p1
            v2 = p2
            v3 = p3
        elif p2_y == p3_y:
           v1 = p2
           v2 = p3
           v3 = p1
        elif p3_y == p1_y:
           v1 = p3
           v2 = p1
           v3 = p2
        else:
            # split triangle if none are the same y
            # If p1 is inbetween p2 and p3
            if (p1_y > p2_y and p1_y < p3_y) or (p1_y < p2_y and p1_y > p3_y):
                line = self.pointsOnLine(p2, p3, True)
                i = 0
                # There has to be a point where this ends because it's in the middle
                while True:
                    if i < (len(line) - 1):
                        if line[i].getCoords()[1] == line[i+1].getCoords()[1]: 
                            i = i + 1
                            continue

                    
                    if line[i].getCoords()[1] == p1_y:
                        self.drawTriangle(buff, p1, p2, line[i], doSmooth)
                        self.drawTriangle(buff, p1, p3, line[i], doSmooth)
                        return
                    i = i + 1
            # If p2 is inbetween p1 and p3
            elif (p2_y > p1_y and p2_y < p3_y) or (p2_y < p1_y and p2_y > p3_y):
                line = self.pointsOnLine(p1, p3, True)
                i = 0
                while True:
                    if i < (len(line) - 1):
                        if line[i].getCoords()[1] == line[i+1].getCoords()[1]: 
                            i = i + 1
                            continue
                    if line[i].getCoords()[1] == p2_y:
                        self.drawTriangle(buff, p1, p2, line[i], doSmooth)
                        self.drawTriangle(buff, p2, p3, line[i], doSmooth)
                        return
                    i = i + 1
            # If p3 is inbetween p2 and p1
            elif (p3_y > p1_y and p3_y < p2_y) or (p3_y < p1_y and p3_y > p2_y):
                line = self.pointsOnLine(p1, p2, True)
                i = 0
                while True:
                    if i < (len(line) - 1):
                        if line[i].getCoords()[1] == line[i+1].getCoords()[1]: 
                            i = i + 1
                            continue
                    if line[i].getCoords()[1] == p3_y:
                        self.drawTriangle(buff, p1, p3, line[i], doSmooth)
                        self.drawTriangle(buff, p3, p2, line[i], doSmooth)
                        return
                    i = i + 1

        # "Draw" the two non flat sides of the triangle
        line1 = self.pointsOnLine(v3, v1, doSmooth)
        line2 = self.pointsOnLine(v3, v2, doSmooth)
        # If the beginning y does not equal for both lines then reverse one because one is drawn in y perspective
        # Want the y's to be the same so we can scan line 1 y level at a time
        if line1[0].getCoords()[1] != line2[0].getCoords()[1]:
            line2.reverse()
        i = 0
        j = 0
        while (i != len(line1) and j != len(line2)):
            # These cases are for when there is a line when y = #
            # - - - W W W W - - - - Z Z Z Z - - - -
            # Don't want to draw a line from every W to every Z, that's 3+ extra lines
            # So if you move x and the y is still the same just draw the point their rather than a line
            # And if you reach a place where the y changes then you can draw a line
            # So you're always drawing at most 1 line from one end of the W to one end of the Z filling in any gaps along the way with points
            if i < (len(line1) - 1):
                if line1[i].getCoords()[1] == line1[i+1].getCoords()[1]: 
                    self.drawPoint(buff, line1[i])
                    i = i + 1
                    continue
            if j < (len(line2) - 1):
                if line2[j].getCoords()[1] == line2[j+1].getCoords()[1]: 
                    self.drawPoint(buff, line2[j])
                    j = j + 1
                    continue

            # Just use bresenhams because it handles lerp and could easily be expanded to handle verticle scan line
            self.drawLine(buff, line1[i], line2[j])
            # Once we get to this point we guarantee that line1 and line2 will both change y next step
            # So we are allowed to increment both
            i = i + 1
            j = j + 1
        return

    # test for lines lines in all directions
    def testCaseLine01(self, n_steps):
        center_x = int(self.buff.width / 2)
        center_y = int(self.buff.height / 2)
        radius = int(min(self.buff.width, self.buff.height) * 0.45)

        v0 = Point([center_x, center_y], ColorType(1, 1, 0))
        for step in range(0, n_steps):
            theta = math.pi * step / n_steps
            v1 = Point([center_x + int(math.sin(theta) * radius), center_y + int(math.cos(theta) * radius)],
                       ColorType(0, 0, (1 - step / n_steps)))
            v2 = Point([center_x - int(math.sin(theta) * radius), center_y - int(math.cos(theta) * radius)],
                       ColorType(0, (1 - step / n_steps), 0))
            self.drawLine(self.buff, v2, v0, doSmooth=True)
            self.drawLine(self.buff, v0, v1, doSmooth=True)

    # test for lines: drawing circle and petal 
    def testCaseLine02(self, n_steps):
        n_steps = 2 * n_steps
        d_theta = 2 * math.pi / n_steps
        d_petal = 12 * math.pi / n_steps
        cx = int(self.buff.width / 2)
        cy = int(self.buff.height / 2)
        radius = (0.75 * min(cx, cy))
        p = radius * 0.25

        # Outer petals
        for i in range(n_steps + 2):
            self.drawLine(self.buff,
                          Point((math.floor(0.5 + radius * math.sin(d_theta * i) + p * math.sin(d_petal * i)) + cx,
                                 math.floor(0.5 + radius * math.cos(d_theta * i) + p * math.cos(d_petal * i)) + cy),
                                ColorType(1, (128 + math.sin(d_theta * i * 5) * 127) / 255,
                                          (128 + math.cos(d_theta * i * 5) * 127) / 255)),
                          Point((math.floor(
                              0.5 + radius * math.sin(d_theta * (i + 1)) + p * math.sin(d_petal * (i + 1))) + cx,
                                 math.floor(0.5 + radius * math.cos(d_theta * (i + 1)) + p * math.cos(
                                     d_petal * (i + 1))) + cy),
                                ColorType(1, (128 + math.sin(d_theta * 5 * (i + 1)) * 127) / 255,
                                          (128 + math.cos(d_theta * 5 * (i + 1)) * 127) / 255)),
                          doSmooth=True, doAA=self.doAA, doAAlevel=self.doAAlevel)

        # Draw circle
        for i in range(n_steps + 1):
            v0 = Point((math.floor(0.5 * radius * math.sin(d_theta * i)) + cx,
                        math.floor(0.5 * radius * math.cos(d_theta * i)) + cy), ColorType(1, 97. / 255, 0))
            v1 = Point((math.floor(0.5 * radius * math.sin(d_theta * (i + 1))) + cx,
                        math.floor(0.5 * radius * math.cos(d_theta * (i + 1))) + cy), ColorType(1, 97. / 255, 0))
            self.drawLine(self.buff, v0, v1, doSmooth=True, doAA=self.doAA, doAAlevel=self.doAAlevel)

    # test for smooth filling triangle
    def testCaseTri01(self, n_steps):
        n_steps = int(n_steps / 2)
        delta = 2 * math.pi / n_steps
        radius = int(min(self.buff.width, self.buff.height) * 0.45)
        cx = int(self.buff.width / 2)
        cy = int(self.buff.height / 2)
        theta = 0

        for _ in range(n_steps):
            theta += delta
            v0 = Point((cx, cy), ColorType(1, 1, 1))
            v1 = Point((int(cx + math.sin(theta) * radius), int(cy + math.cos(theta) * radius)),
                       ColorType((127. + 127. * math.sin(theta)) / 255,
                                 (127. + 127. * math.sin(theta + 2 * math.pi / 3)) / 255,
                                 (127. + 127. * math.sin(theta + 4 * math.pi / 3)) / 255))
            v2 = Point((int(cx + math.sin(theta + delta) * radius), int(cy + math.cos(theta + delta) * radius)),
                       ColorType((127. + 127. * math.sin(theta + delta)) / 255,
                                 (127. + 127. * math.sin(theta + delta + 2 * math.pi / 3)) / 255,
                                 (127. + 127. * math.sin(theta + delta + 4 * math.pi / 3)) / 255))
            self.drawTriangle(self.buff, v1, v0, v2, False, self.doAA, self.doAAlevel)

    def testCaseTri02(self, n_steps):
        # Test case for no smooth color filling triangle
        n_steps = int(n_steps / 2)
        delta = 2 * math.pi / n_steps
        radius = int(min(self.buff.width, self.buff.height) * 0.45)
        cx = int(self.buff.width / 2)
        cy = int(self.buff.height / 2)
        theta = 0

        for _ in range(n_steps):
            theta += delta
            v0 = Point((cx, cy), ColorType(1, 1, 1))
            v1 = Point((int(cx + math.sin(theta) * radius), int(cy + math.cos(theta) * radius)),
                       ColorType((127. + 127. * math.sin(theta)) / 255,
                                 (127. + 127. * math.sin(theta + 2 * math.pi / 3)) / 255,
                                 (127. + 127. * math.sin(theta + 4 * math.pi / 3)) / 255))
            v2 = Point((int(cx + math.sin(theta + delta) * radius), int(cy + math.cos(theta + delta) * radius)),
                       ColorType((127. + 127. * math.sin(theta + delta)) / 255,
                                 (127. + 127. * math.sin(theta + delta + 2 * math.pi / 3)) / 255,
                                 (127. + 127. * math.sin(theta + delta + 4 * math.pi / 3)) / 255))
            self.drawTriangle(self.buff, v0, v1, v2, True, self.doAA, self.doAAlevel)

    def testCaseTriTexture01(self, n_steps):
        # Test case for no smooth color filling triangle
        n_steps = int(n_steps / 2)
        delta = 2 * math.pi / n_steps
        radius = int(min(self.buff.width, self.buff.height) * 0.45)
        cx = int(self.buff.width / 2)
        cy = int(self.buff.height / 2)
        theta = 0

        triangleList = []
        for _ in range(n_steps):
            theta += delta
            v0 = Point((cx, cy), ColorType(1, 1, 1))
            v1 = Point((int(cx + math.sin(theta) * radius), int(cy + math.cos(theta) * radius)),
                       ColorType((127. + 127. * math.sin(theta)) / 255,
                                 (127. + 127. * math.sin(theta + 2 * math.pi / 3)) / 255,
                                 (127. + 127. * math.sin(theta + 4 * math.pi / 3)) / 255))
            v2 = Point((int(cx + math.sin(theta + delta) * radius), int(cy + math.cos(theta + delta) * radius)),
                       ColorType((127. + 127. * math.sin(theta + delta)) / 255,
                                 (127. + 127. * math.sin(theta + delta + 2 * math.pi / 3)) / 255,
                                 (127. + 127. * math.sin(theta + delta + 4 * math.pi / 3)) / 255))
            triangleList.append([v0, v1, v2])

        for t in triangleList:
            self.drawTriangle(self.buff, *t, doTexture=True)


if __name__ == "__main__":
    def main():
        print("This is the main entry! ")
        app = wx.App(False)
        # Set FULL_REPAINT_ON_RESIZE will repaint everything when scaling the frame
        # here is the style setting for it: wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE
        # wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER will disable canvas resize.
        frame = wx.Frame(None, size=(500, 500), title="Test", style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE)

        canvas = Sketch(frame)
        canvas.debug = 0

        frame.Show()
        app.MainLoop()


    def codingDebug():
        """
        If you are still working on the assignment, we suggest to use this as the main call.
        There will be more strict type checking in this version, which might help in locating your bugs.
        """
        print("This is the debug entry! ")
        import cProfile
        import pstats
        profiler = cProfile.Profile()
        profiler.enable()

        app = wx.App(False)
        # Set FULL_REPAINT_ON_RESIZE will repaint everything when scaling the frame
        # here is the style setting for it: wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE
        # wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER will disable canvas resize.
        frame = wx.Frame(None, size=(500, 500), title="Test", style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE)
        canvas = Sketch(frame)
        canvas.debug = 2
        frame.Show()
        app.MainLoop()

        profiler.disable()
        stats = pstats.Stats(profiler).sort_stats('cumtime').reverse_order()
        stats.print_stats()

    main()
    #codingDebug()
