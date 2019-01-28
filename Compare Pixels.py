'''
Oliver Nickalls, Jan 2019


Short app to compare _pixel_ data between pre and post-anon DICOMs.
To flag a warning if the pixel data is different.

It should take 2 arguments - the names (including paths) of the two DICOM files to compare.

It can return an error if they are non-identical, or if pyDICOM fails to open/compare for whatever reason.

'''


import sys
import pydicom
#import subprocess as subp
import numpy as np

dcmFiles = sys.argv[1:]
#print('len( sys.argv ) = ' + str(len( sys.argv )) )

if len( dcmFiles ) != 2:

    print('Incorrect number of cmd line arguments found.')
    print('Two filenames are required as arguments.')
    
    if len( dcmFiles ) == 1:
        print('No arguments supplied.')
    else:
        print('Found:')
        for line in dcmFiles:
            print(f'\t{line}')

    # Wrong number of arguments - therefore we cannot continue.
    exit()

print('Comparing:')

count=0
for line in dcmFiles:
	print(f'\tFile {count}:\t{line}')
	count += 1

print('\n')
# There must be 2 cmd line arguments - 2 files for comparison.


 
FileNumber = 0
dcmFO = []

for dcmFileName in dcmFiles:
	
	try:
		#print(f'Trying to open {dcmFileName}')
		dcmFO.append( pydicom.filereader.dcmread( dcmFileName ) )
	except:
		print(f'Fatal Error: Failed to open {dcmFileName}' )
		exit()
	else:
		#print(f'Opened {dcmFileName} OK' )
		pass


# Compare Images
#  also get some basic stats while we are here.
#
# pyDICOM uses the dataset method .pixel_array[] to reveal data
# This exposes a NumPy object (?) and maybe a numpy method to compare would be fater


# Using the numpy array compare function - this is FAST
if np.array_equal( dcmFO[0].pixel_array, dcmFO[1].pixel_array ):
	print('Numpy finds no difference between the pixel data')
	#exit()

else:
	print('\t**** Numpy finds a difference between pixel data sets. ****\n')

# Manually checking the array shapes
if (dcmFO[0].Rows == dcmFO[1].Rows) and  (dcmFO[0].Columns == dcmFO[1].Columns):
	print(f'Header data image shapes match:\t{dcmFO[0].Rows} x {dcmFO[0].Columns}')

if np.array_equal(dcmFO[0].pixel_array.shape,  dcmFO[1].pixel_array.shape):
	print(f'Pixel data image array shapes match:\t{dcmFO[0].pixel_array.shape}')

# Go pixel by pixel and show the differences
# also grab some max & min data at the same time
print('\nComparing pixel data...  Please wait...\n')


mismatches = 0
pixelCount = 0
max_0intensity = dcmFO[0].pixel_array[0,0]
min_0intensity = dcmFO[0].pixel_array[0,0]
max_1intensity = dcmFO[1].pixel_array[0,0]
min_1intensity = dcmFO[1].pixel_array[0,0]

for r in range(0, dcmFO[0].pixel_array.shape[0]):
	for c in range(0,dcmFO[0].pixel_array.shape[1]):

		pixelCount += 1

		if max_0intensity < dcmFO[0].pixel_array[r,c]:
			max_0intensity = dcmFO[0].pixel_array[r,c]

		elif min_0intensity > dcmFO[0].pixel_array[r,c]:
			min_0intensity = dcmFO[0].pixel_array[r,c]

		if max_1intensity < dcmFO[1].pixel_array[r,c]:
			max_1intensity = dcmFO[1].pixel_array[r,c]

		elif min_1intensity > dcmFO[1].pixel_array[r,c]:
			min_1intensity = dcmFO[1].pixel_array[r,c]

		if dcmFO[0].pixel_array[r,c] != dcmFO[1].pixel_array[r,c]:

			mismatches += 1
			print(f'Pixel data mismatch: ( {r}, {c} ) --> {dcmFO[0].pixel_array[r,c]} & {dcmFO[1].pixel_array[r,c]}')


print(f'\nDirectly compared {pixelCount} pixels in each image.')
print(f'Found {mismatches} pixel data differences between the 2 DCM files.')
print(f'File 1:\tMax: {max_0intensity}\tMin: {min_0intensity}')
print(f'File 2:\tMax: {max_1intensity}\tMin: {min_1intensity}')



