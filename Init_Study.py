'''
Init_Study.py

Create a template 'study' XLS file with pre-generated anonymised IDs
DeIdentifier reads this XLS and uses the list to assign anonymised IDs
during the anonymisation/deidentification process.

It also serves as a log.  
Re-Identification can be performed with this XLS
'''

import os
import argparse
import openpyxl
from console_progressbar import ProgressBar
import study_modules
from gooey import Gooey

@Gooey(progress_regex=r"^progress: (\d+)%$")
def main():

	default_title = 'Default Study Title'
	#--------------------> Parsing Options & Setup <-------------------------
	parser = argparse.ArgumentParser(
		description='Create a XLS deidentification file for your study.'
		)
	parser.add_argument('filename', 
		metavar='<filename>', 
		type=str, 
		default="template",
		help='Template <filename>.xlsx to create (no spaces allowed)'
		)
	parser.add_argument('-title', 
		metavar='<Study Title>', 
		type=str, 
		default='Default Study Title',
		help='Title of Study'
		)
	parser.add_argument('-PI', 
		metavar='<PI name>', 
		type=str, 
		default='<PI name here>', 
		help='Primary Investigator (PI) name'
		)
	parser.add_argument('-n', 
		metavar='<No. of StudyIDs>', 
		type=int, 
		default=1000, 
		help='Number of Study IDs to create (default = 1000)'
		)
	parser.add_argument('-format', 
		metavar='<SID format>', 
		type=str, 
		default='uudddd',
		help='StudyID Format (default = \"uudddd\") (U)pper, (L)ower,'
			 + ' (C)har of either case, (D)igit'
		)
	parser.add_argument('-prefix', 
		metavar='<StudyID prefix>', 
		type=str, 
		default='',
		help='Study ID Prefix (default = blank)'
		)
	parser.add_argument('-suffix', 
		metavar='<StudyID prefix>', 
		type=str, 
		default='',
		help='Study ID suffix (default = blank)'
		)
	args = parser.parse_args()

	#-------------------------------------------------------------
	#------------->      Validate Input Data    <-----------------
	#-------------------------------------------------------------
	args.format = args.format.lower().strip('\n')
	for letter in args.format:
		# Digit, Lower, Upper, Char (either upper or lower)
		if letter not in ['d','l','u','c']: 
			print(f'Fatal Error: Incorrect StudyID format: \"{args.format}\"')
			print('Please use only \"u\",\"l\",\"c\",\"d\"')
			print('(U)pper, (L)ower, (C)har of either case, (D)igit')
			exit()

	#--------------------> Validate Filename <-------------------------------
	if " " in args.filename:
		print(f'\tReplacing spaces in \"{args.filename}\" with \"_\"')
		args.filename = args.filename.replace(" ", "_")
	if "." in args.filename:
		print(f'\Removing \".\" in \"{args.filename}\"')
		args.filename = args.filename.replace(".", "")
	xls_Filename = args.filename + '.xlsx'

	#---------------------> Housekeeping <----------------------------
	number_of_study_IDs = args.n

	#------------->      Create XLS workbook    <-----------------
	study = study_modules.Study_Class()
	study.create_new_study( xls_Filename,
		args.title,
		args.PI,
		number_of_study_IDs )
	study.xls_populate_attribs()

	#------------->      Create Study IDs       <-----------------
	# create LIST item of created study IDs
	# --Each needs to be unique
	# --Each needs to be created according to the template

	# I understand this method is not the most performant
	# Pandas could be faster using dataframes and the 'duplicated' method
	# but this works and does not need to be so performant.
	IDsCreated = 0
	StudyIDs = []

	print('\nCreating Study IDs.')
	print(f'Format={args.format}, prefix=\"{args.prefix}\"')

	sample_format = study_modules.create_rnd_studyID(args.format, args.prefix)
	print(f'Example format: {sample_format}\n')

	# Protect against div by zero error from ProgressBar
	# when n < number of intervals
	if args.n >= 50:
		progressintervals = 50
	else:
		progressintervals = args.n
	pb = ProgressBar(total=progressintervals,
		prefix='Generating Study IDs', 
		suffix='Complete', 
		decimals=0, 
		length=progressintervals, 
		fill='X', 
		zfill='-')
	ProgressStep = int( number_of_study_IDs / progressintervals )
	Next_Landmark = 0
	collisions = 0

	# sanity check - are there enough possible StudyIDs available 
	# with the requested format?
	max_no_IDs = study_modules.number_possible_IDs( args.format )
	percent_of_max = ( (number_of_study_IDs/max_no_IDs) * 100)

	print(f'Generating {number_of_study_IDs} out of a possible {max_no_IDs}')

	if  number_of_study_IDs > max_no_IDs:
		print(f'\n\tImpossible to create {number_of_study_IDs} Study IDs with current format.')
		print('\tTry again with revised ID format, or create fewer IDs.')
		exit()
	# If creating almost all possible IDs (>98% here) then warn- Collisions++
	# There is a faster way to do this with a list of all possible IDs
	# then randomly choose and remove from the list. ?Dict may be faster.
	elif number_of_study_IDs > (0.98 * max_no_IDs ):
		print(f'\n\tWarning:')
		print(f'\t\tCreating {percent_of_max}% of possible {max_no_IDs}.')
		print('\tThis may be slow.')
		print('\tConsider reducing no. of study IDs, or changing format.')

	while IDsCreated < number_of_study_IDs:
		#Get new randomly created study ID in the correct format
		# This could be replaced by a generator but a fn will do for now

		newID = study_modules.create_rnd_studyID( args.format, args.prefix, args.suffix )

		#Compare with the existing list StudyIDs
		# Only add to list if it is unique
		if newID not in StudyIDs:
			StudyIDs.append( newID )
			IDsCreated += 1

			#Advance Progress Bar if reached the next threshold step
			if IDsCreated >= Next_Landmark:
				print(f"progress: {int( (IDsCreated / max_no_IDs) * 100 )}%")
				#pb.print_progress_bar( int(IDsCreated / ProgressStep) )
				Next_Landmark += ProgressStep
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
	study.log( f'Number of studyIDs:{args.n} Prefix: \"{args.prefix}'
				+ '\" Format: \"{args.format}\"' + '{args.suffix}', study.LOGLEVEL_NORMAL)


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



if __name__ == '__main__':
    main()
