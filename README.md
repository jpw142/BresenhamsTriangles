# BresenhamsTriangles
Bresenham's algorithm implementation for both triangles and lines, smooth and flat shaded.
CS480 Computer Graphics Course Work

Here is the overall design of the program:

drawLine uses bresenhams algorithm to draw continuous lines and uses the drawPoint method to actually interact with the buffer. 
Because Bresenham's can't handle steep slopes when the slope is greater than 1 it reverses the role of x and y.
All of this was done with great care to only use integers in order to increase speed.

pointsOnLine is the same exact thing as drawLine with the same exact logic just instead of drawing it returns a list of points it would have drawn.
This is useful for drawTriangle because it allows me to interact with a collection of the points on the line rather than doing bresenhams every time.
I decided to seperate this method from drawLine in order to not cause any unintended behavior with the drawLine method due to returning things not being in the spec.

drawTriangle first makes sure that the triangle its drawing has a flat bottom/top.
If it doesn't have a flat bottom it finds the middle vertice and then draws a line W between the other two vertices. Then it finds the point on W that is the same y as the middle vertice.
It's important to note here there is a little extra code that makes sure it grabs the furthest vertice if there are multiple on that y. 
This likely isn't necessary but I wanted to make sure that there wouldn't be any 2 or 3 pixel discrepencies.
Then after that it calls the two new draw calls and those triangles are gauranteed to have flat bottoms.
Then it gets all the points for the two non-flat sides and makes sure they are in the same y order. Because the way my implementation works sometimes one list will be in reverse order from the other.
Then it just scanlines across those two non-flat sides and fills it with color, bilinear interpolating between the sides if neccesary.
It's also important to note that in cases where there are multiple pixels on the same y it would draw 4+ lines for the same line. So instead id there are multiple pixels it just draws those pixels individually.
It then ensures that it only draws one line and if it overlaps those pixels it is a little inefficient but is more efficient then creating a lot of test cases for niche edge cases.
Because I'm essentially using bresenhams for everything then it naturally interpolates for smooth and flat shading easily with no overhead.

I also modified the left click and right click methods to draw lines and triangles accordingly.

