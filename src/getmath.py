from pygame import Rect as PyRect
from math import cos, sin, pi, atan2, sqrt

INV_SQRT2 = 1 / sqrt(2)

def sign(n):
	if (n < 0):
		return -1
	elif (n > 0):
		return 1
	else:
		return 0

def v2_int(v):
	result = (int(v[0]), int(v[1]))
	return result

def v2_dot(v1, v2):
	result = v1[0]*v2[0] + v1[1]*v2[1]
	return result

def v2_add(v1, v2):
	result = (v1[0]+v2[0], v1[1]+v2[1])
	return result

def v2_sub(v1, v2):
	result = (v1[0]-v2[0], v1[1]-v2[1])
	return result

def v2_mult(v1, scalar):
	resultx = v1[0] * scalar
	resulty = v1[1] * scalar
	return (resultx, resulty)

def v2_max(v1, v2):
	if (v1[0]**2 + v1[1]**2 >= v2[0]**2 + v2[1]**2):
		return v1
	else:
		return v2

def v2_len2(v):
	result = v[0]**2 + v[1]**2
	return result

def v2_deg(v):
	result = atan2(v[0], v[1]) / pi * 180.0
	return result

def v2_rad(v):
	result = atan2(v[0], v[1])
	return result

# if clamp is a rect, 
# scale v until it intersects the perimeter of the rect
def v2_scale2clamp(v, clamp):
	cw, ch = clamp
	vw, vh = v

	diffx = cw - vw
	diffy = ch - vh

	rw = rh = 0

	if (diffx > diffy):
		rw = cw
		rh = cw * vh / vw
	else:
		rw = ch * vw / vh
		rh = ch	

	return (rw, rh)

def v2_len(v):
	result = sqrt(v[0]**2 + v[1]**2)
	return result

def v2_normalize(v):
	# cardinal directions and (0, 0) just return the vector
	if (v[0]==0 and v[1]==0):
		return (0, 0)
	elif (v[0]==0):
		return (0, 1) if v[1] > 0 else (0, -1)
	elif (v[1]==0):
		return (1, 0) if v[0] > 0 else (-1, 0)
	# common diagonals like (1, 1), quickly return using 0.7071 as 1/sqrt(2)
	elif (v[0] + v[1] <= 2 and v[0]**2 + v[1]**2 == 2):
		return (v[0]*0.7071, v[1]*0.7071)
	else:
		vlen = v2_len(v)
		result = (v[0]/vlen, v[1]/vlen)
		return result

def sum_tuples(tuples):
	resultx = 0
	resulty = 0
	for x, y in tuples:
		resultx += x
		resulty += y
	return (resultx, resulty)

def tuple_mult(tup, scalar):
	resultx = tup[0] * scalar
	resulty = tup[1] * scalar
	return (resultx, resulty)

def deg2rad(deg):
	result = deg / 180.0 * pi
	return result

def rad2deg(rad):
	result = rad / pi * 180.0
	return result

class CircularArc:
	def __init__(self, origin, inner_radius, outer_radius, direction, angle):
		self.x = origin[0]
		self.y = origin[1]
		self.inner_radius = inner_radius
		self.outer_radius = outer_radius
		self.direction = v2_normalize(direction)
		self.angle = angle # 2 * degrees from center vector to outer limit in either direction

	def contains_point(self, point):
		square_dist = (point[0]-self.x)**2 + (point[1]-self.y)**2
		vec2point = v2_sub(point, self.origin)
		halfangle_radians = deg2rad(self.angle)

		# theta = acos((u . v) / (|u||v|))
		# |u|^2 * |v|^2 * cos2(theta) > (u . v)^2
		insideangle = ((v2_len2(self.direction) * v2_len2(vec2point) * cos(halfangle_radians)**2) > (v2_dot(vec2point, self.direction) ** 2))
		
		result = (
			square_dist > self.inner_radius**2 and
			square_dist < self.outer_radius**2 and
			insideangle
		)
		return result

	def get_drawinfo(self):
		# pygame.draw.arc(surface, color, rect, start_angle[radians], stop_angle[radians], width)
		inner_rect = pygame.Rect(
			self.origin[0]-self.inner_radius, 
			self.origin[1]-self.inner_radius,
			self.inner_radius * 2,
			self.inner_radius * 2
		)
		outer_rect = pygame.Rect(
			self.origin[0]-self.outer_radius, 
			self.origin[1]-self.outer_radius,
			self.outer_radius * 2,
			self.outer_radius * 2
		)

		ang_in_rads = deg2rad(self.angle)
		direction_rads = v2_rad(self.direction)

		startang = direction_rads - ang_in_rads/2
		stopang = direction_rads + ang_in_rads/2

		innerarc = (inner_rect, startang, stopang)
		outerarc = (outer_rect, startang, stopang)

		centerlinestart = v2_mult(self.direction, self.inner_radius)
		centerlineend = v2_mult(self.direction, self.outer_radius)

		# rotate center line about (0, 0)
		line1start = (
			centerlinestart[0] * cos(-1*ang_in_rads/2) - centerlinestart[1] * sin(-1*ang_in_rads/2),
			centerlinestart[1] * sin(-1*ang_in_rads/2) - centerlinestart[1] * cos(-1*ang_in_rads/2)
		)
		line1end = (
			centerlineend[0] * cos(-1*ang_in_rads/2) - centerlineend[1] * sin(-1*ang_in_rads/2),
			centerlineend[1] * sin(-1*ang_in_rads/2) - centerlineend[1] * cos(-1*ang_in_rads/2)
		)
		line2start = (
			centerlinestart[0] * cos(ang_in_rads/2) - centerlinestart[1] * sin(ang_in_rads/2),
			centerlinestart[1] * sin(ang_in_rads/2) - centerlinestart[1] * cos(ang_in_rads/2)
		)
		line2end = (
			centerlineend[0] * cos(ang_in_rads/2) - centerlineend[1] * sin(ang_in_rads/2),
			centerlineend[1] * sin(ang_in_rads/2) - centerlineend[1] * cos(ang_in_rads/2)
		)

		# transpose line starts and ends to self.origin
		line1start = v2_add(self.origin, line1start)
		line1end = v2_add(self.origin, line1end)
		line2start = v2_add(self.origin, line2start)
		line2end = v2_add(self.origin, line2end)

		line1 = (line1start, line1end)
		line2 = (line2start, line2end)

		return (innerarc, outerarc, line1, line2)

class Rect:
	def __init__(self, pos, dim):
		self.x = pos[0]
		self.y = pos[1]
		self.width = dim[0]
		self.height = dim[1]

	def copy(self):
		result = Rect((self.x, self.y), (self.width, self.height))
		return result

	def print(self):
		print((self.x, self.y), (self.width, self.height))

	def __str__(self):
		return 'Rect<%f, %f, %f, %f>' % (self.x, self.y, self.width, self.height)

	def get_dim(self):
		result = (self.width, self.height)
		return result

	def move(self, dp):
		self.x += dp[0]
		self.y += dp[1]
		return self

	def get_center(self):
		result = (self.x + self.width/2.0, self.y + self.height/2.0)
		return result

	def get_topleft(self):
		result = (self.x, self.y)
		return result

	def get_fat(self):
		result = Rect(
			(self.x - (self.width*RECT_FAT_MOD - self.width)/2, self.y), 
			(self.width*RECT_FAT_MOD, self.height)
		)
		return result

	def get_verts(self):
		topleft = (self.x, self.y)
		topright = (self.x+self.width, self.y)
		botleft = (self.x, self.y+self.height)
		botright = (self.x+self.width, self.y+self.height)

		return (topleft, topright, botleft, botright)

	def get_pyrect(self):
		result = PyRect((int(self.x), int(self.y)), (int(self.width), int(self.height)))
		return result

	def contains_point(self, point):
		'''
		using strictly gt/lt on the left and top edges so that
		collision detection doesn't think it's colliding down
		when rubbing a wall on the left. 
		Easy fix and no discernable difference right now.
		'''
		result = (
			point[0] > self.x and
			point[0] < self.x+self.width and
			point[1] > self.y and
			point[1] < self.y+self.height
		)
		return result

	def collides_rect(self, rect):
		sum_rect = Rect(
			(self.x-rect.width/2.0, self.y-rect.height/2.0), 
			(self.width+rect.width, self.height+rect.height)
		)
		point = rect.get_center()
		result = sum_rect.contains_point(point)
		return result

	def contains_rect(self, rect):
		result = True
		for point in rect.get_verts():
			if (not self.contains_point(point)):
				result = False
				break
		return result

	def contains_circle(self, center, radius):
		deltax, deltay = (abs(center[0] - self.x), abs(center[1] - self.y))

		if (deltax <= self.width/2):
			return True
		if (deltay <= self.height/2):
			return True

		cornerdist_sq = (deltax - self.width/2)**2 + (deltay - self.height/2)**2

		result = cornerdist_sq <= radius**2
		return result