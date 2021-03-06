'''
Oliver Nickalls, Jan 2019

Simple script to dump the entire header of a single DICOM file to screen. 
A .bat file will pipe into a txt file

'''

import sys
import pydicom
import subprocess as subp
#import matplotlib.pyplot as plt


if len( sys.argv ) == 1:
    print('No cmd line arguments found.  Adding a default  CR-MONO1-10-chest...')
    sys.argv.append( 'CR-MONO1-10-chest')

#Assign the rest of the given list to dcm-files
dcmFiles = sys.argv[1:]  # the first argument is the script itself


# print no. of lines received - note these are not necessarily files
print( '\n' + str(len(dcmFiles)) + ' line(s) received from cmd line') 

# Iterate through all cmd line arguments received and print them to screen
line_count = 1
for p in dcmFiles:
    print( f'{line_count}\t{p}' )
    line_count += 1

print('\n')


for dcmFileName in dcmFiles:
	try:
		dcmFileobject = pydicom.filereader.dcmread( dcmFileName, force = True )
	except:
		print(f'Failed to open {dcmFileName}')
		continue
		
		
	#try:
	logfileName = dcmFileName + '.hdr.txt'
	print(f'logging to {logfileName}')
	logfile = open( logfileName, 'w')
	logfile.write( str(dcmFileobject) )
	logfile.close()
	#subp.call(f'start \"{logfileName}\"', shell=True)
	#subp.call(f'start \"{logfileName}\"' )
	#except:
	#	pass

# plt.imshow(dcmFileName.pixel_array, cmap=plt.cm.bone) 


