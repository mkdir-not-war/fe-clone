from random import random

TOTALRANDSIZE = 10000
RANDSPERLINE = 10

def save(filelines):
	fin = open('./myrandarray.py', 'w')
	for line in filelines:
		fin.write('%s\n' % line)
	fin.close()

def gen():
	filelines = []
	
	filelines.append('TOTALRANDSIZE = %d' % TOTALRANDSIZE)
	filelines.append('RANDARRAY = [')

	i = 0
	while (i < TOTALRANDSIZE):
		nums = [str(random()) for j in range(RANDSPERLINE)]
		newline = '\t' + ', '.join(nums)
		i += RANDSPERLINE
		if (i < TOTALRANDSIZE):
			newline = newline + ','
		filelines.append(newline)

	filelines.append(']')

	return filelines

if __name__=='__main__':
	filelines = gen()
	save(filelines)