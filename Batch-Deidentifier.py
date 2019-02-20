'''
*****************************
By Oliver Nickalls Jan 2019

Enter 1 or more directories as cmd line arguments to create duplicate directories, containing copies of original non-DICOM files too.


This expands on the previous version 'recurseDIR.py' that only takes a single directory as an argument.

Much borrowed from the pyDICOM anonymiser example from the userguide
# https://pydicom.github.io/pydicom/dev/auto_examples/metadata_processing/plot_anonymize.html
PyDICOM Version 1.2.1

=====================
Planned enhancements:
=====================
-Logging with variable on-screen verbosity
-Support taking IDs/Name from an external list to allow reversible anonymisation
	the user may or may not be blinded to the process
-?encrypt / scramble log output?


'''


import os         # for os.walk() primarily
import sys        # cmd line arguments
import pydicom    # DICOM - obviously...
import shutil     # used for just file copying.


from BAModules import *

##### This code is largely lifted from the pyDICOM userguide
# https://pydicom.github.io/pydicom/dev/auto_examples/metadata_processing/plot_anonymize.html
# additions to blank all date and time values.


print( os.path.basename(__file__) )


print('Formatting input files...')

file_paths = sys.argv[1:]  # the first argument is the script itself



if len(file_paths) == 0:
	print('No input found. Defaulting to test string.')
	#file_paths.append( 'C:\\Users\\oliver\\Documents\\pycode\\dropscript\\DVD 6- Volunteer 60' )
	print('No cmd line arguments found.\n\nSyntax:\n\tBatch-Anonymiser <dir1> [<dir2> <dir3>...]')
	print('\n\twhere <dir_> is the base directory of DICOM files')
	print('BatchAnonymiser will change the patient name to the \'base\' directory name.')
	print('e.g. BatchAnonymiser c:\\myfiles\\patient-zero')
	print('\n\t will:')
	print('\t\t-Duplicate the directory tree into c:\\myfiles\\patient-zero-anon (including non-DICOM files and empty directories)')
	print('\t\t-Anonymise all DICOM files')
	print('\t\t-Change the patient name in all DICOM files to \'patient-zero\'.')
	exit()

print( '\n' + str(len(file_paths)) + ' line(s) received from cmd line') # print no. of lines received

# Iterate through all lines received from the cmd line and print them to screen
line_count = 1
for p in file_paths:
	print( str(line_count) + '\t' + p)
	line_count += 1

#print('File List complete.')

'''
# warning msg if more than 1 cmd line argument
if len(file_paths) > 1:
	print('Multiple lines received from cmd line. Those after the 1st will be ignored.\n')
'''    
print('\n')


#Beginning of loop for multiple directories

# Count some dir and file stats
all_dir_count = 0
all_file_count = 0
all_valid_DCM_file = 0
all_copyOK = 0
all_copyfailed = 0
all_anonok = 0
all_anonfailed = 0


#loop through all the folders/files in file_paths[] 

for rootDir in file_paths:
	
	print(f'rootDir = {rootDir}')
	#The old line for just a single directory 
	#rootDir = file_paths[0] # Pass the 1st directory listed as 'root' for iteration.
	
	# This takes the characters to the right of the last '\\' in the path
	#  and makes it the new anonymised pt name
	#  e.g. if rootDir = 'c:\stuff\mydicim\ptZERO' then AnonName becomes 'ptZERO' 
	AnonName = rootDir[ -rootDir[-1::-1].find('\\') : ] 
	
	AnonID = 'RESEARCH'
	
	
	
	# Count some dir and file stats
	dir_count = 0
	file_count = 0
	valid_DCM_file = 0
	copyOK = 0
	copyfailed = 0
	anonok = 0
	anonfailed = 0
	
	
	#small bit of code to strip the deepest dir tree from rootDir
	# then append with '-anon'
	#
	# e.g. from C:\mystuff\sub\dcmfiles
	#      to   C:\mystuff\sub\dcmfiles_anon
	#
	#  needs to work within the os.walk() loop below.
	# 1- strip the rootDir from the left of the string
	# 2- insert the anonymised root in that space   
	# This can only work because the final \ is not present at the end of the paths presented by os.walk 
	
	
	for dirName, subdirList, fileList in os.walk(rootDir):
		dir_count += len( subdirList )
		file_count += len( fileList )
	
		dirNameAnon = rootDir + '-anon' + dirName[ len(rootDir): ]
	
		# Create the directories as we come across them.
		# I am not going to check if empty, just blindly re-create the same dir structure
	
		try: 
			os.makedirs( dirNameAnon )
		except OSError:
			if not os.path.isdir( dirNameAnon ):
				print(f'Fatal Error: Failed to create directory: {dirNameAnon}')
				raise
		else:
			print(f'\t{dirNameAnon} created OK')
			dir_count += 1

	


		#    print('Found directory: %s' % dirName)
		for fname in fileList:
			testfilename = dirName + '\\' + fname
			savefilename = dirNameAnon + '\\' + fname


			# print each file namejust  before testing - end='' to prevent the \n & flush to push to screen
			print( f'\ttest {testfilename}', end='', flush=True )


			# Try to open each file with pydicom to validate it.
			# print '--OK--' if successful, '--FAILED--' if not then move on.

			try:  # Try opening each file as a DICOM file with pyDICOM
				testdcmobj = pydicom.filereader.dcmread( testfilename, force=True)

			except:  # If it fails (ie raises an exception) count it as non-DICOM
				print('\t-NonDICOM- Copying', end='')

				try:  # Do this with Non-DICOM files. Just copy across.
					shutil.copy(testfilename, savefilename )

				except:  #Copy failed msg - this can be improved to pass on the error msg/code
					print(' FAILED ***')
					copyfailed += 1

				else:   # No error - assume success
					print(' OK')
					copyOK += 1


			else:  # Do this if the files is DICOM
				valid_DCM_file += 1
				print('\t-DICOM- Anonymise', end='')

				try:  # the actual anonymisation
					anonymiseDICOM( testdcmobj, AnonName, AnonID )   # anonymiseDICOM ( file-like object, name string, ID string )
					testdcmobj.save_as( savefilename, write_like_original=True)

				except:
					print('\t++FAILED++')
					anonfailed += 1

				else:
					print('\tOK')
					anonok += 1



	# Stats on exit
	all_dir_count += dir_count
	all_file_count += file_count
	all_valid_DCM_file += valid_DCM_file
	all_copyOK += copyOK
	all_copyfailed += copyfailed
	all_anonok += anonok
	all_anonfailed += anonfailed


	#print('Found ' + str(valid_DCM_file) + ' valid DICOM files')
	#print('New pt name is\t\'' + AnonName + '\'' )
	#print('New pt ID is:\t\'' + AnonID + '\'' )
	
	print(f'Anonymised: {rootDir}')
	print(f'DICOMs Anonymised:\t{anonok} OK, {anonfailed} failed' )
	print(f'Non-DICOMs Copied:\t{copyOK} OK, {copyfailed} failed' )


if all_dir_count > 1:
	print('\nFinished Batch Job.')
else:
	print('\nFinished Job.')

print(f'all_dir_count \t{all_dir_count}')
print(f'all_file_count \t{all_file_count}')
print(f'all_valid_DCM_file \t{all_valid_DCM_file}')
print(f'all_copyOK \t{all_copyOK}')
print(f'all_copyfailed \t{all_copyfailed}')
print(f'all_anonok \t{all_anonok}')
print(f'all_anonfailed \t{all_anonfailed}')

