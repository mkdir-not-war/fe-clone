from enum import IntEnum
import json

GAMEMAP_TILES_WIDE = 19
GAMEMAP_TILES_HIGH = 15
GAMEMAP_SIZE = GAMEMAP_TILES_HIGH * GAMEMAP_TILES_WIDE

PATH_TO_REGIONDATA = './data/maps/testregionsdata.json'

class RegionName(IntEnum):
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
	# Rossbother		
	ROSSBOTHER 			= 26
	PILGRIMROAD			= 27

	TOTALREGIONS		= 28

class RegionData:
	def __init__(self):
		self.width 		= 0
		self.height 	= 0
		self.nummaps 	= 0

		self.northconnections = []
		self.southconnections = []
		self.eastconnections = []
		self.westconnections = []

class MapData:
	def __init__(self):
		# exits
		self.northexit = None
		self.eastexit = None
		self.westexit = None
		self.southexit = None

		# tiles
		self.groundarray = None
		self.blockarray = None

	def print(self):
		print()
		printlist = [str(i) for i in self.blockarray]
		for j in range(1, GAMEMAP_TILES_HIGH+1):
			print(' '.join(printlist[(j-1)*GAMEMAP_TILES_WIDE:j*GAMEMAP_TILES_WIDE]))
		print()

def load_regiondata(allregions):
	fin = open(PATH_TO_REGIONDATA, 'r')
	rawregiondata = json.load(fin)
	fin.close()

	for region in rawregiondata:
		print(region)

def print_regionconnections(allregions):
	pass

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

def generate_all_maps():
	pass

def gen_basic():
	pass




##########################################################################################################
## TEST ##################################################################################################
##########################################################################################################

def test():
	allregions = [RegionData()] * 4
	load_regiondata(allregions)
	print_regionconnections(allregions)

if __name__=='__main__':
	test()