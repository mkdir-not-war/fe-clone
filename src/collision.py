from src.constants import TILE_WIDTH, GAMEMAP_TILES_WIDE, GAMEMAP_TILES_HIGH
from src.mymath import *
from math import sqrt, pi, cos, sin

# collision constants
COLTILE_WIDTH = TILE_WIDTH//2
COLLISION_MAPTILE_SPLITLEN = 2
COLTILE_WIDTH = TILE_WIDTH // COLLISION_MAPTILE_SPLITLEN

COLLISION_EPSILON = 0.008 # distance from wall to hit

# adapted from handmade hero day 048
def test_collision_walls_diamond(wallX, posX, posY, deltaX, deltaY, minY, maxY, cornX, cornY, norm, tMin_list):
	
	#### OG HANDMADE CODE -- works great but corners are too sharp ###############
	if deltaX != 0:
		# these X and Ys might not actually be X, Y in coordinate. Might be switched
		t_result = (wallX - posX) / deltaX	
		y_result = posY + t_result * deltaY
		
		# if the vector actually intersected the wall segment
		if (y_result >= minY+cornY and y_result <= maxY-cornY):

			# if t value is smaller than current minimum
			if (t_result > 0 and t_result < tMin_list[0]):
				tMin_list[0] = t_result
				return (True, norm)
		## end OG HANDMADE CODE ######################################################

		#### CORNER CODE #############################################################
		else:
			endX, endY = (posX+deltaX, posY+deltaY)

			x1, x2, x3 = (posX, endX, wallX)
			x4 = x3+cornX if (norm[0]+norm[1] < 0) else x3-cornX
			y1, y2 = (posY, endY)

			# at max corner
			if (y_result > 0 and y_result <= maxY):

				y3, y4 = (maxY-cornY, maxY)

				t_numer = (x1-x3)*(y3-y4) - (y1-y3)*(x3-x4)
				t_denom = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)

				u_numer = (x1-x3)*(y1-y2) - (y1-y3)*(x1-x2)
				u_denom = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)

				if (t_denom != 0 and u_denom != 0):
					t_result = t_numer / t_denom
					u_result = u_numer / u_denom

					if (0 <= t_result and t_result <= 1 and
						0 <= u_result and u_result <= 1):
						
						if norm == (-1, 0):
							rotate_normal = (-1, 1)
						elif norm == (1, 0):
							rotate_normal = (1, 1)
						elif norm == (0, -1):
							rotate_normal = (1, -1)
						elif norm == (0, 1):
							rotate_normal = (1, 1)

						rotate_normal = (cornX*rotate_normal[0], cornY*rotate_normal[1]) # normalize later
						tMin_list[0] = t_result

						return (True, rotate_normal)

			# at min corner
			elif (y_result < 0 and y_result >= minY):

				y3, y4 = (minY+cornY, minY)

				t_numer = (x1-x3)*(y3-y4) - (y1-y3)*(x3-x4)
				t_denom = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)

				u_numer = (x1-x3)*(y1-y2) - (y1-y3)*(x1-x2)
				u_denom = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)

				if (t_denom != 0 and u_denom != 0):
					t_result = t_numer / t_denom
					u_result = u_numer / u_denom

					if (0 <= t_result and t_result <= 1 and
						0 <= u_result and u_result <= 1):

						if norm == (-1, 0):
							rotate_normal = (-1, -1)
						elif norm == (1, 0):
							rotate_normal = (1, -1)
						elif norm == (0, -1):
							rotate_normal = (-1, -1)
						elif norm == (0, 1):
							rotate_normal = (-1, 1)

						rotate_normal = (cornX*rotate_normal[0], cornY*rotate_normal[1]) # normalize later
						tMin_list[0] = t_result

						return (True, rotate_normal)
		## end CORNER CODE #####################################################

	return (False, (0, 0))

def do_collision(regionmap, entity):
	entitydelta = v2_sub(entity.get_pos(), entity.get_prevpos())

	# get bounding box of all tiles the movedelta might pass through
	# assume width and height are never negative
	mintilex = min(entity.prev_x, entity.x)
	mintiley = min(entity.prev_y, entity.y)
	maxtilex = max(entity.prev_x, entity.x) 
	maxtiley = max(entity.prev_y, entity.y)

	# expand area to include area covered by entity collision-width/height
	# entity position is center-x, center-y of collision box
	mintilex -= entity.coll_width
	mintiley -= entity.coll_height
	maxtilex += entity.coll_width
	maxtiley += entity.coll_height

	# scale from map-space to collision-tile-space
	mintilex = int(mintilex / COLTILE_WIDTH)
	mintiley = int(mintiley / COLTILE_WIDTH)

	maxtilex = int(maxtilex / COLTILE_WIDTH) + 1 # one past to include the final tile
	maxtiley = int(maxtiley / COLTILE_WIDTH) + 1

	coltilearraylength = GAMEMAP_TILES_WIDE * GAMEMAP_TILES_HIGH * COLLISION_MAPTILE_SPLITLEN**2

	tRemaining = 1.0 # how much of the timestep would have been thru the collision-space

	# iterate a couple times
	for i in range(4):
		if tRemaining <= 0:
			break

		tMin = 1.0 # time step used to the closest colliding wall
		wallnormal = (0, 0)

		# check walls of each collider-tile
		for tiley in range(mintiley, maxtiley):
			for tilex in range(mintilex, maxtilex):
				testtileindex = tilex + (GAMEMAP_TILES_WIDE*COLLISION_MAPTILE_SPLITLEN) * tiley

				# skip checking out of bounds on flat array
				if (testtileindex < 0 or 
					testtileindex >= coltilearraylength):
					continue

				# player positions with respect to the current tile's center
				epos = v2_sub(entity.get_pos(), ((tilex+0.5)*COLTILE_WIDTH, (tiley+0.5)*COLTILE_WIDTH))
				eppos = v2_sub(entity.get_prevpos(), ((tilex+0.5)*COLTILE_WIDTH, (tiley+0.5)*COLTILE_WIDTH))

				# if collision map has the tile as a collider
				if (regionmap.get_colltile(tilex, tiley)):

					minX = -(0.5*COLTILE_WIDTH + entity.coll_width)
					minY = -(0.5*COLTILE_WIDTH + entity.coll_height)

					maxX = 0.5*COLTILE_WIDTH + entity.coll_width
					maxY = 0.5*COLTILE_WIDTH + entity.coll_height

					corner_height = entity.coll_height
					corner_width = entity.coll_width

					# get line segments of tileindex rect (direction from player)
					# X vars and Y vars just need to be opposite, not necessarily 0 and 1 respectively
					east = (
						minX, # between eppos and eppos+delta, find percentage of deltaX => t_result
						eppos[0], eppos[1], 
						entitydelta[0], entitydelta[1], 
						minY, maxY, # y-bounds to check if line crosses segment
						corner_width, corner_height,
						(-1, 0)
					)
					west = (
						maxX,
						eppos[0], eppos[1], # rotate 180
						entitydelta[0], entitydelta[1], 
						minY, maxY,
						corner_width, corner_height,
						(1, 0)
					)
					north = (
						maxY,
						eppos[1], eppos[0], 
						entitydelta[1], entitydelta[0], # deltaX < 0
						minX, maxX,
						corner_height, corner_width,
						(0, 1)
					)
					south = (
						minY,
						eppos[1], eppos[0], 
						entitydelta[1], entitydelta[0], # deltaX > 0
						minX, maxX,
						corner_height, corner_width,
						(0, -1)
					)

					# cardinal collisions
					tMin_list = [tMin]

					for d in [east, west, north, south]:
						result, normal = test_collision_walls_diamond(*d, tMin_list)
						if result:
							# don't overwrite walls with corners?? TODO: is this right?
							if (normal[0] * normal[1] == 0 or wallnormal == (0, 0)):
								wallnormal = normal
							tMin = tMin_list[0]

		tRemaining -= tMin*tRemaining

		# normalize the wallnormal if needed
		wallnormal = v2_normalize(wallnormal)

		# update entity position
		entity.x = entity.prev_x + entitydelta[0] * tMin + wallnormal[0] * COLLISION_EPSILON
		entity.y = entity.prev_y + entitydelta[1] * tMin + wallnormal[1] * COLLISION_EPSILON
			
		# on an edge, glide along the edge
		entity.dp = v2_sub(entity.dp, v2_mult(wallnormal, v2_dot(entity.dp, wallnormal)))
		entitydelta = v2_sub(entitydelta, v2_mult(wallnormal, v2_dot(entitydelta, wallnormal)))