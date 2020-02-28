import cv2, math, sys
import numpy as np

def add_to_filename(filename, add):
	period = filename.find('.')
	return filename[:period] + add  + filename[period:]

# Buffers array with infinity to prevent range errors in energy calculation
def buffer(a):
	return np.concatenate(([np.inf], a, [np.inf]))

# Finds the minimum energy seam in an image
# Moves down row by row using dynamic programming to calculate minimum energy at each pixel
def min_energy(img):
	W = energy_matrix(img)
	height, width = W.shape
	for y in range(height):
		above = W[0].copy()
		if y > 0:
			left = np.roll(W[y-1], -1)
			right = np.roll(W[y-1], 1)
			left[-1], right[0] = np.inf, np.inf
			above = np.minimum(left, right)
			above = np.minimum(above, W[y-1])
		W[y] += above
	return W

# Given the minimum energy of a seam, backtrace to determine the pixels included
def min_seam(W):
	height, width = W.shape
	seam = np.zeros(height, dtype=np.int)
	seam[-1] = np.argmin(W[-1])
	for y in range(height -2, -1, -1):
		last = seam[y + 1]
		b = buffer(W[y])
		seam[y] = last + np.argmin(b[(last):(last+3)]) - 1
	return seam

# Calculate Sobel energy matrix of image, sum of xy derivatives
def energy_matrix(img):
	dx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
	dy = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
	return abs(dx) + abs(dy)

# Removes a given seam from the image and smooths borders
def remove_seam(img, seam, rotated):
	height, width, channels = img.shape
	keep_pixels = np.ones((height, width), dtype=np.bool)

	# Flag pixels for removal
	for y in range(height -1, -1, -1):
		keep_pixels[y, seam[y]] = False

	keep_pixels = np.stack([keep_pixels] * channels, axis=2)
	img = img[keep_pixels].reshape((height, width - 1, channels))

	return img

# Content aware image resizing from any aspect ratio to square
def seam_carve_square(in_file):
	color_img = cv2.imread(in_file)
	height, width, channels = color_img.shape

    # rotate if taller than wide, so crop is always done on width
	rotated = height > width
	if rotated:
		color_img = np.flipud(np.rot90(color_img))

	gray_img = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)
	height, width = gray_img.shape

	# For the number of rows to be removed...
	removed_cols = width-height
	for i in range(removed_cols):
		W = min_energy(gray_img)
		seam = min_seam(W)
		color_img = remove_seam(color_img, seam, rotated)
		gray_img = cv2.cvtColor(color_img.astype('float32'), cv2.COLOR_BGR2GRAY)

	if rotated:
		color_img = np.rot90(np.flipud(color_img), k = 3)
	cv2.imwrite(add_to_filename(in_file, '_square'), color_img)

if __name__ == "__main__":
	seam_carve_square(sys.argv[1])
