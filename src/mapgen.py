from enum import IntEnum
from random import choice
from src.getmath import v2_add
from src.constants import *
import json

GAMEMAP_SIZE = GAMEMAP_TILES_HIGH * GAMEMAP_TILES_WIDE

PATH_TO_REGIONDATA = './data/maps/testregionsdata.json'
PATH_TO_COLLISIONDATA = './data/maps/collisiontilemap.dat'

TOTALREGIONS = 5 # test:5, game:28?

class RegionName(IntEnum):
	# Testbother
	TESTROAD			= 0
	TESTBOTHER			= 1
	TESTHOUSE			= 2
	# Test End
	TESTSGATE			= 3
	TESTTEMPLE			= 4

'''
	# West End
	PILGRIMSGATE 		= 0
	OLDWESTBRIDGE 		= 1
	WESTMARKETSQ		= 2
	# The Mud
	SAINTSTREET			= 3
	NJALBRIDGE			= 4
	BLACKSQ				= 5
	DOWNSHIRE			= 6
	NORTHWHARFS			= 7
	# The Docks
	EMPRESSSQ			= 8
	EMPORERSQ			= 9
	DOCKSMARKET			= 10
	ROLLINGBARREL		= 11
	WESTWHARFS			= 12
	# The Brass
	FOXHILLSQ			= 13
	TWINDRAKEHALL		= 14
	CASTLETONGREN		= 15
	# Downbull
	DOWNBULL			= 16
	# The Stays
	EASTWHARFS			= 17
	NAVALYARD			= 18
	CISTERNSQ			= 19
	WIGGINSASYLUM		= 20
	# East End
	GALLOWSSQ			= 21
	ALLHEROESJAIL		= 22
	# The Market
	MARKETSQ			= 23
	TEMPLESQ			= 24
	PUREWATERTEMPLE		= 25
	INNERSANCTUM		= 26 ################ << TODO: add this to data
	# Rossbother		
	ROSSBOTHER 			= 27
	PILGRIMROAD			= 28
'''

class TileLayer(IntEnum):
	BG 		= 0
	MG 		= 1
	FG 		= 2

class RegionMap:
	def __init__(self, coldata):

		self.tile_layers = [[]] * 3

		####### test combat map -- grass and fenced-in area ################
		self.tile_layers[TileLayer.BG] = [
			2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 2, 3, 4, 2,
			4, 2, 3, 4, 5, 10, 11, 12, 13, 2, 3, 4, 5, 2, 3, 5, 2, 3, 4,
			3, 4, 2, 3, 4, 12, 13, 10, 11, 5, 2, 3, 4, 5, 2, 4, 3, 4, 2,
			2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4,
			3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 2, 4, 3, 4, 2,
			4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 2, 3, 5, 4, 2, 3, 
			5, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 3, 4, 2, 5, 3, 4,
			2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 2, 5, 3, 4, 2, 5, 3,
			3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 2,
			4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 2, 3, 5, 4, 2, 3,
			5, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 3, 4, 2, 5, 3, 4,
			3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 2, 5, 4, 2, 3,
			4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 2, 3, 4, 2, 3, 4,
			2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 5, 3, 4, 2, 5,
			3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 2, 4, 3, 4, 2
		]

		self.tile_layers[TileLayer.MG] = [0] * GAMEMAP_TILES_WIDE * GAMEMAP_TILES_HIGH
		self.tile_layers[TileLayer.MG][130] = 112
		
		self.tile_layers[TileLayer.FG] = [0] * GAMEMAP_TILES_WIDE * GAMEMAP_TILES_HIGH
		######################################################################

		self.collisionmap = self.load_collisionmap(coldata)

		# TODO: change this to one of four directions, and extrapolate both character positions from that
		self.curr_spawn_tile = (7, 6) 

	def get_spawnpos(self):
		# offset pixels so player position is in center of tile indicated
		return (
			self.curr_spawn_tile[0]*TILE_WIDTH + TILE_WIDTH//2,
			self.curr_spawn_tile[1]*TILE_WIDTH + TILE_WIDTH//2
		)

	'''
	use this for int-map of collision tiles

	0x0000_1234 =>

		1  2

		3  4 (not that we would ever use 2, 3 or 4. Just showing them here for illustration purpose)

	'''
	def get_colltile(self, coltilex, coltiley):
		tilex = coltilex // 2
		tiley = coltiley // 2
		xoff = coltilex % 2
		yoff = coltiley % 2 # because collision is 2x2 grid on each tile

		collint = self.collisionmap[tilex + tiley * GAMEMAP_TILES_WIDE]
		bitmask = (0x1 << yoff*8) << xoff*4

		return collint & bitmask > 0

	def load_collisionmap(self, coldata):
		# go through each of the tile layers, OR the coll ints
		result = []

		for i in range(GAMEMAP_TILES_WIDE*GAMEMAP_TILES_HIGH):
			collint = 0

			collint |= coldata[self.tile_layers[TileLayer.BG][i]]
			collint |= coldata[self.tile_layers[TileLayer.MG][i]]
			# NOTE: foreground (fg) layer does not collide

			result.append(collint)

		return result

class RegionData:
	def __init__(self):
		self.index		= -1
		self.name 		= None
		self.zone 		= None
		self.width 		= 0
		self.height 	= 0
		self.nummaps 	= 0

		self.connections = None
		self.mapindex 	= -1

	def load(self, name, data):
		self.name = name
		self.index = int(data['index'])
		self.zone = data['zone']
		self.width = w = int(data['width'])
		self.height = h = int(data['height'])
		self.nummaps = w*h
		self.connections = data['connections']

class MapData:
	def __init__(self, regionindex):
		self.regionindex = regionindex

		# exits (index in allmaps of connected map)
		self.northexit = None
		self.eastexit = None
		self.westexit = None
		self.southexit = None
		self.buildingexit = None

		# tiles
		self.groundarray = None
		self.blockarray = None

	def print(self):
		print()
		printlist = [str(i) for i in self.blockarray]
		for j in range(1, GAMEMAP_TILES_HIGH+1):
			print(' '.join(printlist[(j-1)*GAMEMAP_TILES_WIDE:j*GAMEMAP_TILES_WIDE]))
		print()

def load_regiondata_from_json(allregions):
	fin = open(PATH_TO_REGIONDATA, 'r')
	rawregiondata = json.load(fin)
	fin.close()

	i = 0
	for regionname in rawregiondata:
		data = rawregiondata[regionname]
		allregions[i].load(regionname, data)
		i += 1

	allregions.sort(key=lambda r: r.index)

def print_regionconnections(allregions):
	for region in allregions:
		print(region.index, region.name, region.zone)

def setup_tilearrays(mapdata):
	mapdata.groundarray = [0] * GAMEMAP_SIZE
	mapdata.blockarray = [0] * GAMEMAP_SIZE

	# frame map with blockers, skipping exit squares
	for j in range(GAMEMAP_TILES_HIGH):
		for i in range(GAMEMAP_TILES_WIDE):

			if i==1:
				if not mapdata.westexit or j-1!=GAMEMAP_TILES_HIGH//2:
					mapdata.blockarray[i+j*GAMEMAP_TILES_WIDE] = 1
					continue
			if i==GAMEMAP_TILES_WIDE-2:
				if not mapdata.eastexit or j-1!=GAMEMAP_TILES_HIGH//2:
					mapdata.blockarray[i+j*GAMEMAP_TILES_WIDE] = 1
					continue
			if j==1:
				if not mapdata.northexit or j-1!=GAMEMAP_TILES_WIDE//2:
					mapdata.blockarray[i+j*GAMEMAP_TILES_WIDE] = 1
					continue
			if j==GAMEMAP_TILES_HIGH-2:
				if not mapdata.southexit or j-1!=GAMEMAP_TILES_WIDE//2:
					mapdata.blockarray[i+j*GAMEMAP_TILES_WIDE] = 1
					continue

#############################################################################################
## GEN TILE ARRAYS FOR EACH REGION ##########################################################
#############################################################################################

def gentilearray_rossbother(mapdata):
	# fill in tile array in rossbother style
	pass

## END TILE ARRAY GEN #######################################################################

class MazeNode:
	def __init__(self):
		self.north 		= None
		self.south 		= None
		self.east 		= None
		self.west 		= None

def maze_generator(width, height, nodes):
	# generate maze!
	edgeorigins = {}
	edgenodes = []
	visitednodes = []
	nodexy = (0, 0)

	while (len(visitednodes) < height*width):
		# visit the chosen node
		nodeindex = nodexy[0] + nodexy[1] * width
		currnode = nodes[nodeindex]
		visitednodes.append(nodexy)

		# add neighbors to edge (if they aren't visited)
		potentialedges = []
		if (nodexy[0] > 0):
			potentialedges.append(('west', 	v2_add(nodexy, (-1, 0))))
		if (nodexy[1] > 0):
			potentialedges.append(('north', v2_add(nodexy, (0, -1))))
		if (nodexy[0] < width-1):
			potentialedges.append(('east', 	v2_add(nodexy, (1,  0))))
		if (nodexy[1] < height-1):
			potentialedges.append(('south', v2_add(nodexy, (0,  1))))

		for edgeinfo in potentialedges:
			direction, edge = edgeinfo
			if (not edge in visitednodes and not edge in edgenodes):
				edgeorigins[edge] = (nodeindex, direction)
				edgenodes.append(edge)

		# choose new node
		if (len(edgenodes) > 0):
			nodexy = choice(edgenodes)
			edgenodes.remove(nodexy)
			ognodeindex, direction = edgeorigins[nodexy]
			newnodeindex = nodexy[0] + nodexy[1] * width
		else:
			break

	# use edge origins map to set flags
	for edge in edgeorigins:
		ogindex, direction = edgeorigins[edge]
		edgeindex = edge[0] + edge[1] * width

		if direction == 'west':
			nodes[ogindex].west = edgeindex
			nodes[edgeindex].east = ogindex
		elif direction == 'north':
			nodes[ogindex].north = edgeindex
			nodes[edgeindex].south = ogindex
		elif direction == 'east':
			nodes[ogindex].east = edgeindex
			nodes[edgeindex].west = ogindex
		elif direction == 'south':
			nodes[ogindex].south = edgeindex
			nodes[edgeindex].north = ogindex

class AdjacentMapDirection(IntEnum):
	NORTH 		= 0
	SOUTH		= 1
	EAST 		= 2
	WEST		= 3
	BUILDING	= 4

	TOTAL		= 5

class MapGenerator:
	def __init__(self):
		self.allregions = []
		self.allmaps = []

		# collision data for tilemaps (same for all tilemaps, as long as they follow the template)
		colfin = open(PATH_TO_COLLISIONDATA, 'r')
		self.tilemap_coldata = [int(i) for i in colfin.read().split(' ')]
		colfin.close()

		self.curr_regionmap = RegionMap(self.tilemap_coldata)

		self.adj_regionmaps = [RegionMap(self.tilemap_coldata) for i in range(AdjacentMapDirection.TOTAL)]

	def get_currmap(self):
		return self.curr_regionmap

	def load_regionmap_fromindex(self, mapdata_index):
		pass

	def load_adjacentregionmap(self, adjacent_map_dir):
		pass

	def run(self):
		# load region data
		self.allregions = []
		for i in range(TOTALREGIONS):
			self.allregions.append(RegionData())
		load_regiondata_from_json(self.allregions)

		# create map data from region data
		self.allmaps = []

		# go once through all regions to stamp mapindex
		mapindex = 0
		for region in self.allregions:
			region.mapindex = mapindex # region stamped with index of top map in allmaps
			for i in range(region.nummaps):
				self.allmaps.append(MapData(region.index))
			mapindex += region.nummaps

		# set region exits
		for region in self.allregions:
			# exits connecting between regions
			for conndata in region.connections:
				connregionname = conndata["region"]
				mapindex = region.mapindex + (conndata['y'] * region.width) + conndata['x']
				connregion = self.allregions[RegionName[connregionname].value]
				connmapindex = connregion.mapindex + (conndata['cy'] * connregion.width) + conndata['cx']
				if (conndata['exit'] == "north"):
					self.allmaps[mapindex].northexit = connmapindex
				elif (conndata['exit'] == "south"):
					self.allmaps[mapindex].southexit = connmapindex
				elif (conndata['exit'] == "east"):
					self.allmaps[mapindex].eastexit = connmapindex
				elif (conndata['exit'] == "west"):
					self.allmaps[mapindex].westexit = connmapindex
				elif (conndata['exit'] == "building"):
					self.allmaps[mapindex].buildingexit = connmapindex

			# exits within regions (maze algo)
			mazenodes = [MazeNode() for n in range(region.nummaps)]
			maze_generator(region.width, region.height, mazenodes)
			for i in range(len(mazenodes)):
				mapindex = region.mapindex + i
				mazenode = mazenodes[i]
				if mazenode.north != None:
					self.allmaps[mapindex].northexit = mazenode.north + region.mapindex
				if mazenode.south != None:
					self.allmaps[mapindex].southexit = mazenode.south + region.mapindex
				if mazenode.east != None:
					self.allmaps[mapindex].eastexit = mazenode.east + region.mapindex
				if mazenode.west != None:
					self.allmaps[mapindex].westexit = mazenode.west + region.mapindex


##########################################################################################################
## TEST ##################################################################################################
##########################################################################################################

def test():
	mapgen = MapGenerator()
	mapgen.run()

	# print results
	for region in mapgen.allregions:
		print(region.name)
		print()
		for y in range(region.height):
			line = []
			for x in range(region.width):
				newnodestr = ''
				node = mapgen.allmaps[region.mapindex + x + y * region.width]

				if node.westexit != None:
					newnodestr += '<'

				if node.northexit != None:
					newnodestr += '^'

				if node.buildingexit != None:
					newnodestr += 'B'

				if node.southexit != None:
					newnodestr += 'v'

				if node.eastexit != None:
					newnodestr += '>'

				newnodestr += ' '*(len(newnodestr)-5)

				line.append(newnodestr)
			print(' ' + '\t'.join(line))
			print()		

if __name__=='__main__':
	test()