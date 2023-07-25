from enum import IntEnum
from random import choice
import json

'''
from getmath import v2_add
from constants import *

PATH_TO_REGIONDATA = '../data/maps/testregionsdata.json'
PATH_TO_COLLISIONDATA = '../data/maps/collisiontilemap.dat'
'''

from src.mymath import *
from src.constants import *

PATH_TO_REGIONDATA = './data/maps/testregionsdata.json'
PATH_TO_COLLISIONDATA = './data/maps/collisiontilemap.dat'

SPAWNTILES_FROM_EDGE = 3

TOTALREGIONS = 5 # test:5, game:28?

def get_tilepos_center(tilexy, percentx=0.5, percenty=0.5):
	# offset pixels so player position is in center of tile indicated
	return (
		tilexy[0]*TILE_WIDTH + int(TILE_WIDTH * percentx),
		tilexy[1]*TILE_WIDTH + int(TILE_WIDTH * percenty)
	)

class RegionName(IntEnum):
	# Testbother
	TESTROAD			= 0
	TESTBOTHER			= 1
	TESTHOUSE			= 2
	# Test End
	TESTSGATE			= 3
	TESTTEMPLE			= 4

REGIONNAMESTEXT = {
	RegionName.TESTROAD		: 'Test Road',
	RegionName.TESTBOTHER	: 'Testbother',
	RegionName.TESTHOUSE	: 'Test House',
	# Test End
	RegionName.TESTSGATE	: 'Test\'s Gate',
	RegionName.TESTTEMPLE	: 'Testmaster\'s Office'
}

'''
	# Rossbother	
	PILGRIMROAD			= 0	
	ROSSBOTHER 			= 1
	HIGHTAILHALL		= 2 ################## tutorial "boss" room (key to pilgrims gate)
	# West End
	PILGRIMSGATE 		= 3
	OLDWESTBRIDGE 		= 4
	WESTMARKETSQ		= 5
	# The Mud
	SAINTSTREET			= 6
	NJALBRIDGE			= 7
	BLACKSQ				= 8
	DOWNSHIRE			= 9
	DOWNSHIREKEEP		= 10 ################# boss room (unlock character)
	NORTHWHARFS			= 11
	# The Docks
	EMPRESSSQ			= 11
	EMPORERSQ			= 12
	CHAPELOFLURUE		= 13 ################ boss room (unlock character)
	DOCKSMARKET			= 14
	ROLLINGBARREL		= 15
	VIPROOM				= 16 ################ boss room (unlock character)
	WESTWHARFS			= 17
	# The Brass
	FOXHILLSQ			= 18
	TWINDRAKEHALL		= 18
	GUILDMASTERSOFFICE	= 20 ################ boss room (unlock character)
	CASTLETONGREN		= 21
	THRONEROOM			= 22 ################ boss room (key to castle tongren)
	# Downbull
	DOWNBULL			= 23
	DOWNBULLKEEP		= 24 ################ boss room (key to castle tongren)
	# The Stays
	EASTWHARFS			= 25
	NAVALYARD			= 26
	OFFICERQUARTERS		= 27 ################ boss room (unlock character)
	CISTERNSQ			= 28
	WIGGINSASYLUM		= 29
	OPERATINGROOM		= 30 ################ boss room (explosion scroll for castle tongren)
	# East End
	GALLOWSSQ			= 31
	ALLHEROESJAIL		= 32
	MAXSECURITY			= 33 ################ boss room (thief's tools for castle tongren)
	# The Market
	MARKETSQ			= 34
	TEMPLESQ			= 35
	PUREWATERTEMPLE		= 36
	INNERSANCTUM		= 37 ################ final boss room!
	
'''

class ExitDirection(IntEnum):
	NORTH 		= 0
	SOUTH		= 1
	EAST 		= 2
	WEST		= 3
	BUILDING	= 4

	TOTAL		= 5

EXIT_TILES = {
	ExitDirection.NORTH 	: (GAMEMAP_TILES_WIDE//2, 	0),
	ExitDirection.SOUTH 	: (GAMEMAP_TILES_WIDE//2, 	GAMEMAP_TILES_HIGH-1),
	ExitDirection.EAST 		: (GAMEMAP_TILES_WIDE-1, 	GAMEMAP_TILES_HIGH//2),
	ExitDirection.WEST 		: (0, 						GAMEMAP_TILES_HIGH//2),
	ExitDirection.BUILDING 	: (GAMEMAP_TILES_WIDE//2, 	GAMEMAP_TILES_HIGH//2-1)
}

EXIT_TILEBOX = Rect((0, 0), (TILE_WIDTH, TILE_WIDTH))
def get_exittilebox(exitdirection):
	result = EXIT_TILEBOX.translate(v2_mult(EXIT_TILES[exitdirection], TILE_WIDTH))
	return result

class TileLayer(IntEnum):
	BG 		= 0
	MG 		= 1
	FG 		= 2

class MapDataTile(IntEnum):
	BLANK		= 0
	# ground array tiles
	GROUND1		= 1
	GROUND2		= 2
	IMPGROUND	= 3
	# block array tiles
	WALL		= 4
	STRUCTURE	= 5
	DECORATION	= 6
	SPECIAL1	= 7
	SPECIAL2	= 8

class RegionMap:
	def __init__(self):
		self.tile_layers = [[]] * 3
		self.tile_layers[TileLayer.BG] = [0] * GAMEMAP_SIZE
		self.tile_layers[TileLayer.MG] = [0] * GAMEMAP_SIZE	
		self.tile_layers[TileLayer.FG] = [0] * GAMEMAP_SIZE
		self.collisionmap = [0] * GAMEMAP_SIZE
		self.burningmap = [0] * GAMEMAP_SIZE # burningmap OR collisionmap == collisionmap

	'''
	MapData:

		self.regionindex = regionindex

		# exits (index in allmaps of connected map)
		self.exits = [None] * ExitDirection.TOTAL

		# tiles
		self.groundarray = None
		self.blockarray = None

	'''

	def load_mapdata(self, mapdata, coldata):
		self.tile_layers[TileLayer.BG] = [0] * GAMEMAP_SIZE
		self.tile_layers[TileLayer.MG] = [0] * GAMEMAP_SIZE	
		self.tile_layers[TileLayer.FG] = [0] * GAMEMAP_SIZE

		# TODO: eventually use MapDataTile to load proper sprite indices from tilemap
		SOLOWALLSPRITEINDEX = 48
		GROUNDTILES = [2, 3, 4, 5]

		for i in range(GAMEMAP_SIZE):
			self.tile_layers[TileLayer.BG][i] = choice(GROUNDTILES)

		for k in range(GAMEMAP_SIZE):
			if (mapdata.blockarray[k] == MapDataTile.WALL):
				self.tile_layers[TileLayer.MG][k] = SOLOWALLSPRITEINDEX

		self.collisionmap = self.load_collisionmap(coldata)

	def get_spawntiles(self, entrancedir):
		offsetvec = None
		if (entrancedir == ExitDirection.SOUTH):
			offsetvec = (0, -1)
		elif (entrancedir == ExitDirection.NORTH):
			offsetvec = (0, 1)
		elif (entrancedir == ExitDirection.WEST):
			offsetvec = (1, 0)
		elif (entrancedir == ExitDirection.EAST):
			offsetvec = (-1, 0)
		elif (entrancedir == ExitDirection.BUILDING):
			offsetvec = (0, 1)

		edgetile = EXIT_TILES[entrancedir]
		
		return (
			v2_add(edgetile, v2_mult(offsetvec, SPAWNTILES_FROM_EDGE)),
			v2_add(edgetile, v2_mult(offsetvec, SPAWNTILES_FROM_EDGE-2))
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

		for i in range(GAMEMAP_SIZE):
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
		self.name = REGIONNAMESTEXT[RegionName[name]]
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
		self.exits = [None] * ExitDirection.TOTAL

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
	mapdata.groundarray = [MapDataTile.GROUND1] * GAMEMAP_SIZE
	mapdata.blockarray = [MapDataTile.BLANK] * GAMEMAP_SIZE

	# frame map with blockers, skipping exit squares
	for j in range(GAMEMAP_TILES_HIGH):
		for i in range(GAMEMAP_TILES_WIDE):

			if i==1:
				if mapdata.exits[ExitDirection.WEST] == None or j!=GAMEMAP_TILES_HIGH//2:
					mapdata.blockarray[i+j*GAMEMAP_TILES_WIDE] = MapDataTile.WALL
					continue
			if i==GAMEMAP_TILES_WIDE-2:
				if mapdata.exits[ExitDirection.EAST] == None or j!=GAMEMAP_TILES_HIGH//2:
					mapdata.blockarray[i+j*GAMEMAP_TILES_WIDE] = MapDataTile.WALL
					continue
			if j==1:
				if mapdata.exits[ExitDirection.NORTH] == None or i!=GAMEMAP_TILES_WIDE//2:
					mapdata.blockarray[i+j*GAMEMAP_TILES_WIDE] = MapDataTile.WALL
					continue
			if j==GAMEMAP_TILES_HIGH-2:
				if mapdata.exits[ExitDirection.SOUTH] == None or i!=GAMEMAP_TILES_WIDE//2:
					mapdata.blockarray[i+j*GAMEMAP_TILES_WIDE] = MapDataTile.WALL
					continue

			if mapdata.exits[ExitDirection.BUILDING]:
				if i >= GAMEMAP_TILES_WIDE//2-2 and i <= GAMEMAP_TILES_WIDE//2+2:
					if j >= GAMEMAP_TILES_HIGH//2-2 and j <= GAMEMAP_TILES_HIGH//2:
						if i == GAMEMAP_TILES_WIDE//2 and j != GAMEMAP_TILES_HIGH//2-2:
							continue
						else:
							mapdata.blockarray[i+j*GAMEMAP_TILES_WIDE] = MapDataTile.WALL
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
			potentialedges.append((ExitDirection.WEST, 	v2_add(nodexy, (-1, 0))))
		if (nodexy[1] > 0):
			potentialedges.append((ExitDirection.NORTH, v2_add(nodexy, (0, -1))))
		if (nodexy[0] < width-1):
			potentialedges.append((ExitDirection.EAST, 	v2_add(nodexy, (1,  0))))
		if (nodexy[1] < height-1):
			potentialedges.append((ExitDirection.SOUTH, v2_add(nodexy, (0,  1))))

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

		if direction == ExitDirection.WEST:
			nodes[ogindex].west = edgeindex
			nodes[edgeindex].east = ogindex
		elif direction == ExitDirection.NORTH:
			nodes[ogindex].north = edgeindex
			nodes[edgeindex].south = ogindex
		elif direction == ExitDirection.EAST:
			nodes[ogindex].east = edgeindex
			nodes[edgeindex].west = ogindex
		elif direction == ExitDirection.SOUTH:
			nodes[ogindex].south = edgeindex
			nodes[edgeindex].north = ogindex

class MapGenerator:
	def __init__(self):
		self.allregions = []
		self.allmaps = []

		# gameplay per map
		self.map_combatcompleted = []
		self.map_dialogueevents = []

		# collision data for tilemaps (same for all tilemaps, as long as they follow the template)
		colfin = open(PATH_TO_COLLISIONDATA, 'r')
		self.tilemap_coldata = [int(i) for i in colfin.read().split(' ')]
		colfin.close()

		self.curr_regionmap = RegionMap()
		self.curr_mapindex = -1

	def get_currmap(self):
		return self.curr_regionmap

	def get_regionname(self):
		return self.allregions[self.allmaps[self.curr_mapindex].regionindex].name

	def load_regionmaps_fromindex(self, mapdata_index=None):
		if mapdata_index == None:
			mapdata_index = self.allregions[RegionName.TESTROAD].mapindex

		mapdata = self.allmaps[mapdata_index]
		self.curr_regionmap.load_mapdata(mapdata, self.tilemap_coldata)
		self.curr_mapindex = mapdata_index

		exits2activate = [False] * ExitDirection.TOTAL
		for i in range(ExitDirection.TOTAL):
			exit_mapindex = mapdata.exits[i]
			if exit_mapindex != None:
				exits2activate[i] = True

		return exits2activate

	def load_adjacentregionmap(self, exitdirection):
		return self.load_regionmaps_fromindex(self.allmaps[self.curr_mapindex].exits[exitdirection])

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
					self.allmaps[mapindex].exits[ExitDirection.NORTH] = connmapindex
				elif (conndata['exit'] == "south"):
					self.allmaps[mapindex].exits[ExitDirection.SOUTH] = connmapindex
				elif (conndata['exit'] == "east"):
					self.allmaps[mapindex].exits[ExitDirection.EAST] = connmapindex
				elif (conndata['exit'] == "west"):
					self.allmaps[mapindex].exits[ExitDirection.WEST] = connmapindex
				elif (conndata['exit'] == "building"):
					self.allmaps[mapindex].exits[ExitDirection.BUILDING] = connmapindex

			# exits within regions (maze algo)
			mazenodes = [MazeNode() for n in range(region.nummaps)]
			maze_generator(region.width, region.height, mazenodes)
			for i in range(len(mazenodes)):
				mapindex = region.mapindex + i
				mazenode = mazenodes[i]
				if mazenode.north != None:
					self.allmaps[mapindex].exits[ExitDirection.NORTH] = mazenode.north + region.mapindex
				if mazenode.south != None:
					self.allmaps[mapindex].exits[ExitDirection.SOUTH] = mazenode.south + region.mapindex
				if mazenode.east != None:
					self.allmaps[mapindex].exits[ExitDirection.EAST] = mazenode.east + region.mapindex
				if mazenode.west != None:
					self.allmaps[mapindex].exits[ExitDirection.WEST] = mazenode.west + region.mapindex

		# generate tiles in each map
		for mapindex in range(len(self.allmaps)):
			self.map_combatcompleted.append(False)
			self.map_dialogueevents.append(False)
			setup_tilearrays(self.allmaps[mapindex])
			# TODO: generate more detail specific to each region

		self.map_combatcompleted[self.allregions[RegionName.TESTROAD].mapindex] = True



##########################################################################################################
## TEST ##################################################################################################
##########################################################################################################

'''
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

				if node.exits[ExitDirection.WEST] != None:
					newnodestr += '<'

				if node.exits[ExitDirection.NORTH] != None:
					newnodestr += '^'

				if node.exits[ExitDirection.BUILDING] != None:
					newnodestr += 'B'

				if node.exits[ExitDirection.SOUTH] != None:
					newnodestr += 'v'

				if node.exits[ExitDirection.EAST] != None:
					newnodestr += '>'

				newnodestr += ' '*(len(newnodestr)-5)

				line.append(newnodestr)
			print(' ' + '\t'.join(line))
			print()		
'''

if __name__=='__main__':
	test()