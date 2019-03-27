'''
Init_Study.py

Experimenting with openpyxl to read/edit/save .XLSX files

'''

#Try creating a template .XLSX file for the study.
#Then try loading and verifying it is what is expected for the study & can be used.

import os
import argparse

import openpyxl
from console_progressbar import ProgressBar
import study_modules

#--------------------> Parsing Options & Setup <-------------------------------


parser = argparse.ArgumentParser(
	                 description='Create a XLS deidentification file for your study.')

parser.add_argument('filename', metavar='<filename>', 
                     type=str, 
					 default="template",
	                 help='Template <filename>.xlsx to create (no spaces allowed)')

parser.add_argument('-title', metavar='<Study Title>', 
	                 type=str, 
	                 default='Default Study Title',
	                 help='Title of Study')

parser.add_argument('-PI', metavar='<PI name>', 
	                 type=str, 
	                 default='<PI name here>', 
                     help='Primary Investigator (PI) name')

parser.add_argument('-n', metavar='<No. of StudyIDs>', 
	                 type=int, 
	                 default=1000, 
                     help='Number of Study IDs to create (default = 1000)')

parser.add_argument('-format', 
	                 metavar='<SID format>', 
	                 type=str, 
	                 default='uudddd',
	                 help='Study ID Format (default = \"uudddd\") (U)pper, (L)ower, (C)har of either case, (D)igit')

parser.add_argument('-prefix', 
	                 metavar='<StudyID prefix>', 
	                 type=str, 
	                 default='',
	                 help='Study ID Prefix (default = blank)')

args = parser.parse_args()

'''

class Thing():
	title = ""
	format = ""
	prefix = ""
	n = 0
	filename = ""
	PI = ""

args = Thing()


#-- test params
# simulates the test bat file:
# python Init_Study.py "test file" -t "study to look at stuff" -n 50 -prefix TEST- -format ldd

args.title    = "My DeIdentifed Study"
args.format   = "cdd"
args.prefix   = "TEST-"
args.n        = 5199
args.filename = 'test file'
args.PI       = 'Big PI Person'
'''
#-------------------------------------------------------------
#------------->      Validate Input Data    <-----------------
#-------------------------------------------------------------


if (args.title == 'Default Study Title' ):
	print('No title given')

args.format = args.format.lower().strip('\n')  #strip off the <cr> and force .lower()

for letter in args.format:
	# Digit, Lower, Upper, Char (either upper or lower)
	if letter not in ['d','l','u','c']: 
		print(f'Fatal Error: Incorrect StudyID format: \"{args.format}\"')
		print('Please use only \"d\",\"l\",\"u\",\"c\"')
		exit()


#--------------------> Validate Filename <-------------------------------

# Remove spaces from filename
if " " in args.filename:
	print(f'\tWarning: Replacing spaces in \"{args.filename}\" with \"_\"')
	args.filename = args.filename.replace(" ", "_")

if "." in args.filename:
	print(f'\tWarning: Removing \".\" in \"{args.filename}\"')
	args.filename = args.filename.replace(".", "")

xls_Filename = args.filename + '.xlsx'

#---------------------> Housekeeping <----------------------------

number_of_study_IDs = args.n


study = study_modules.Study_Class()


#-------------------------------------------------------------
#------------->      Create XLS workbook    <-----------------
#-------------------------------------------------------------


# replaced by:
# studytools.

#study.XLS = studytools.create_new_study_xls_file( xls_Filename,
#                               args.title,
#	    					   args.PI,
#							   number_of_study_IDs )


study.create_new_study( xls_Filename,
                               args.title,
	    					   args.PI,
							   number_of_study_IDs )


study.xls_populate_attribs()


#--------------------->  Create Study IDs  <-------------------------

IDsCreated = 0
StudyIDs = []


# create LIST item of created study IDs
# Each needs to be unique
# Each need to be created according to the template

# I understand this method is not the most performant
# Pandas could be faster using dataframes and the 'duplicated' method
# but why involve pandas in such a small script that is not time-sensitive?


print('\nCreating Study IDs.')
print(f'Format={args.format}, prefix=\"{args.prefix}\"')

sample_format = study_modules.create_rnd_studyID( args.format, args.prefix )
print(f'Example format: { sample_format }\n')

# Protect against div by zero error from ProgressBar when n<number of intervals
if args.n >= 50:
	progressintervals = 50
else:
	progressintervals = args.n
print(f'progressintervals = {progressintervals}')

pb = ProgressBar(total=progressintervals,
	             prefix='Generating Study IDs', 
	             suffix='Complete', 
	             decimals=0, 
	             length=progressintervals, 
	             fill='X', 
	             zfill='-')
ProgressStep = int( number_of_study_IDs / progressintervals )
Next_Progress_Step = 0
collisions = 0

#print(f'n = {number_of_study_IDs}')
#print(f'ProgressStep = {ProgressStep}')
#print(f'Next_Progress_Step = {Next_Progress_Step}')

# needs a sanity check - are there enough possible StudyIDs available with the requested format?

max_no_IDs = study_modules.number_possible_IDs( args.format )
percent_of_max = ((number_of_study_IDs/max_no_IDs)*100)

print(f'Generating {number_of_study_IDs} out of possible maximum of {max_no_IDs} (with current format)')

if  number_of_study_IDs > max_no_IDs:
	print(f'\n\tFatal Error: Impossible to create {number_of_study_IDs} Study IDs with current ID format: \'{args.format}\'.')
	print('\tPlease try again with revised ID format or create fewer IDs.')
	exit()
elif number_of_study_IDs > (0.98 * max_no_IDs ):
	print(f'\n\tWarning: Creating {percent_of_max}% of possible Study IDs available in current format: \'{args.format}\'.')
	print('\tThis may be slow.  \n\tConsider reducing no. of study IDs, or changing format')

while IDsCreated < number_of_study_IDs:
	#Get new randomly created study ID in the correct format
	# This could be replaced by a generator but a fn will do for now

	newID = study_modules.create_rnd_studyID( args.format, args.prefix )

	#Compare with the existing list StudyIDs
	# Only add to list if it is unique
	if newID not in StudyIDs:
		StudyIDs.append( newID )
		IDsCreated += 1

		#Advance Progress Bar if reached the next threshold step
		if IDsCreated >= Next_Progress_Step:
			pb.print_progress_bar( int(IDsCreated / ProgressStep) )
			Next_Progress_Step += ProgressStep
	else:
		collisions += 1

print(f'{collisions} collision(s).\n\n')




#--------------------->  Copy into Data Worksheet  <-------------------------

#wsData = study_wb[ 'Data' ]
row = 2
for ID in StudyIDs:
	study.datasheet[ study.XLSDATA_STUDYIDS +str(row) ] = ID
	row += 1

#----------------------> Log the creation <-----------------------

study.log( f'New Study Created. Title: {args.title}, PI: {args.PI}', study.LOGLEVEL_NORMAL)
study.log( f'Number of studyIDs:{args.n} Prefix: \"{args.prefix}\" Format: \"{args.format}\"', study.LOGLEVEL_NORMAL)

#log_xls_creation( study.XLS, number_of_study_IDs, args.prefix, args.format )


#--------------------->  Save XLSX file  <-------------------------

print(f'Saving \"{xls_Filename}\"...')
try:
	study.XLS.save( xls_Filename )
except:
	print(f'Fatal Error: Failed to save \"{ xls_Filename }\"')
	raise
else:
	print(f'Successfully saved \"{ xls_Filename }\"')

print(f'\nProcess complete. Created {args.n} studyIDs of format ')
print(f'\"{args.prefix}\"+\"{args.format}\" and saved to \"{xls_Filename}\"')
