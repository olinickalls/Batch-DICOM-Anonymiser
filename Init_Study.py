'''
Init_Study.py

Experimenting with openpyxl to read/edit/save .XLSX files

'''

#Try creating a template .XLSX file for the study.
#Then try loading and verifying it is what is expected for the study & can be used.

import os
import argparse
from datetime import date, time, datetime
import openpyxl
from console_progressbar import ProgressBar
import studytools



#--------------------> Parsing Options & Setup <-------------------------------

parser = argparse.ArgumentParser(description='Create a template .xlsx anonymisation file for your study.')

parser.add_argument('filename', metavar='<filename>', 
                     type=str, default="template",
	                 help='Template <filename>.xlsx to create (no spaces allowed)')

parser.add_argument('-title', metavar='<Study Title>', 
	                 type=str, default='Default Study Title',
	                 help='Title of Study')

parser.add_argument('-PI', metavar='<PI name>', 
	                 type=str, default='<PI name here>', 
                     help='Primary Investigator (PI) name')

parser.add_argument('-n', metavar='<No. of StudyIDs>', 
	                 type=int, default=1000, 
                     help='Number of Study IDs to create (default = 1000)')

parser.add_argument('-format', metavar='<SID format>', 
	                 type=str, default='uudddd',
	                 help='Study ID Format (default = \"uudddd\") (U)pper, (L)ower, (C)har of either case, (D)igit')

parser.add_argument('-prefix', metavar='<StudyID prefix>', 
	                 type=str, default='',
	                 help='Study ID Prefix (default = blank)')

args = parser.parse_args()



#-------------------------------------------------------------
#------------->      Validate Input Data    <-----------------
#-------------------------------------------------------------


if (args.title == 'Default Study Title' ):
	print('No title given')

args.format = args.format.lower().strip('\n')  #strip off the <cr> and force .lower()

for letter in args.format:
	if letter not in ['d','l','u','c']: # Digit, Lower, Upper, Char (either upper or lower)
		print(f'Fatal Error: Incorrect StudyID format: \"{args.format}\"')
		print('Please use only \"d\",\"l\",\"u\",\"c\"')
		raise


#--------------------> Validate Filename <-------------------------------

# Remove spaces from filename
if " " in args.filename:
	print(f'\tWarning: Replacing spaces in \"{args.filename}\" with \"_\"')
	args.filename = args.filename.replace(" ", "_")

if "." in args.filename:
	print(f'\tWarning: Removing \".\" in \"{args.filename}\"')
	args.filename = args.filename.replace(".", "")

XLSFilename = args.filename + '.xlsx'

#---------------------> Housekeeping <----------------------------

number_of_study_IDs = args.n



#-------------------------------------------------------------
#------------->      Create XLS workbook    <-----------------
#-------------------------------------------------------------


#-------------------> Create XLS workbook & config sheets <----------------------------
# wb = workbook
# ws = worksheet

wb = openpyxl.Workbook()

try:
	wb.save(XLSFilename)
except:
	print(f'Fatal Error: Failed to save \"{XLSFilename}\"')
	raise
else:
	print(f'Created blank template file \"{XLSFilename}\" OK')


wsFront       = wb.active
wsFront.title = 'Front'

wsData = wb.create_sheet('Data') # insert log sheet at the end
wsLog  = wb.create_sheet('log')   # insert log sheet at the end

#--------------------->  Add in basic data  <-------------------------

wsFront['A1'] = 'Front Page'

wsFront['A2'] = 'Study Title:'
wsFront['B2'] = args.title

wsFront['A3'] = 'Primary Investigator:'
wsFront['B3'] = args.PI

wsFront['A4'] = 'No of Study IDs'
wsFront['B4'] = number_of_study_IDs

wsData['A1']  = 'Data Page'
wsData['B1']  = 'Study IDs'
wsData['C1']  = 'Date Added'
wsData['D1']  = 'Time Added'
wsData['E1']  = 'Batch'

wsData['F1']  = 'Patient Real IC'
wsData['G1']  = 'Accession No.'
wsData['H1']  = 'Study Date'

wsLog['A1']   = 'Log Page'

wsLog['B1']   = 'Date'
wsLog['C1']   = 'Time'
wsLog['D1']   = 'Log Activity'
wsLog['E1']   = 'User'
wsLog['F1']   = 'Computer'

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
print(f'Example format: {studytools.create_rnd_studyID( args.format, args.prefix )}\n')

pb = ProgressBar(total=50,
	             prefix='Generating Study IDs', 
	             suffix='Complete', 
	             decimals=0, 
	             length=50, 
	             fill='X', 
	             zfill='-')
ProgressStep = int( number_of_study_IDs / 50 )
Next_Progress_Step = 0
collisions = 0

#print(f'n = {number_of_study_IDs}')
#print(f'ProgressStep = {ProgressStep}')
#print(f'Next_Progress_Step = {Next_Progress_Step}')

# needs a sanity check - are there enough possible StudyIDs available with the requested format?

max_no_IDs = studytools.number_possible_IDs( args.format )
print(f'Total IDs possible with current format: {max_no_IDs}')

if max_no_IDs > number_of_study_IDs:
	print(f'Fatal Error: Impossible to create {number_of_study_IDs} Study IDs with current ID format.')
	print('Please try again with revised ID format or create fewer IDs.')
elif max_no_IDs > (0.9 * number_of_study_IDs):
	print(f'Warning: Creating {((number_of_study_IDs/number_possible_IDs)*100)}% of possible Study IDs in current format.')
	print('This may be slow.')

while IDsCreated < number_of_study_IDs:
	#Get new randomly created study ID in the correct format
	# This could be replaced by a generator but a fn will do for now

	newID = studytools.create_rnd_studyID( args.format, args.prefix )

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

print(f'{collisions} collisions.\n\n')




#--------------------->  Copy into Data Worksheet  <-------------------------

row = 2
for ID in StudyIDs:
	wsData['B'+str(row)] = ID
	row += 1

#----------------------> Log the creation <-----------------------

import getpass

username = getpass.getuser()
compname = os.environ['COMPUTERNAME']
dateobject = datetime.now()
date = dateobject.strftime('%d-%m-%Y')
timenow = dateobject.strftime('%S:%M:%H')


wsLog['B2']   =  date  #'Date'
wsLog['C2']   =  timenow  #'Time'
wsLog['D2']   =  f'Created XLSX file (n={number_of_study_IDs}, format={args.prefix}{args.format})'  #'Log Activity'
wsLog['E2']   =  username  #'User'
wsLog['F2']   =  compname  #'Computer'

#--------------------->  Save XLSX file  <-------------------------

try:
	wb.save(XLSFilename)
except:
	print(f'Fatal Error: Failed to save \"{XLSFilename}\"')
	raise
else:
	print(f'Successfully saved \"{XLSFilename}\"')


