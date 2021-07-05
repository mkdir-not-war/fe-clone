def dot(v1, v2):
	result = 0
	for i in list(range(v1)):
		result += v1[i] * v2[i]
	return result

def norm_dot(v1, v2, length=-1):
	if (length < 0):
		length = len(v1)
	result = dot(v1, v2)
	result /= length
	return result