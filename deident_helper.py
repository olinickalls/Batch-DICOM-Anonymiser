# deident_helper.py
# Helper functions etc. for batch deident_helper

import pydicom
import openpyxl
import os


#####################################################################
#                           Ops class                               #
#####################################################################

class Ops_Class( ):
    QUIET = False
    VERBOSE = False
    DEBUG = False


    def msg(self, message, level = 'NORMAL', endstr = '\n' ):
		# level should correlate with Quiet/Normal/Verbose string
		# if level arg is omitted, it will default to 'NORMAL'
        if self.QUIET:  # Quiet prints nothing
            return
        if self.VERBOSE or self.DEBUG:  # verbose prints everything
            print( message, end = endstr )
            return
        # Only not QUIET or VERBOSE reaches this point.
        if level == 'NORMAL':
            print( message )




#####################################################################
#                         PROCESS_FILE                              #
#####################################################################

def process_file( study, filename, stats ):
	# ----------- Try to open with pydicom
	try:
		study.DCM = pydicom.filereader.dcmread( filename, force=True)
		# Blank the preamble.
		study.DCM.preamble = b'\x00' * 128
		
		load_warning = ''
		
		for tag in study.DCM_TAG_CHECKLIST:
            # this fn. returns '-blank' (as supplied failure string) if the 
            # queried tag is not present.
			if study.try_dcm_attrib( tag, '-blank-') == '-blank-':
				load_warning += (tag + ' ')

		if load_warning != '':
			tag_warning.append( f'{filename} : {load_warning}' )

	except:  # If exception on loading the file is prob non-DICOM
		print('\t-pydicom load failed -skipping file-')
		stats.not_DCM_filenames.append(f'{filename}: pydicom load failed- non-dicom')
		return False

	else:  # If no exception on loading, this code runs.
		stats.valid_DCM_file += 1
		print('\t-DICOM- De-identify', end='')

		# this returns False if there is no StudyInstanceUID tag
		study.test_study_UID = study.get_DCM_StudyInstanceUID( )

        # Maybe redundant after the 'for tag in study.DCM_TAG_CHECKLIST:' loop above
		if not study.test_study_UID:
			stats.skipped_dcm_filenames.append(f'{filename} -No studyUID')
			print(' -No StudyInstanceUID tag  -skipped file-')
			return False

		# Check if StudyInstanceUID has match in cache
		if study.test_study_UID in study.xls_UID_lookup:
			# retrieve the previous studyID linked to the UID
			AnonID = study.get_old_study_attrib_from_UID(
				study.XLSDATA_STUDYIDS,
				study.test_study_UID
				)
			print(f' - Known UID, using {AnonID}')
		else:
			# If UNIQUE study UID ie. not in cache
			AnonID = study.assign_next_free_studyID( )
			print(f' - Unique UID - Assigning {AnonID}')
			
		# Perform deidentification on loaded DICOM data
		study.deidentifyDICOM(study.CurrStudy.AnonName, AnonID )

		# Write de-identified DICOM to disc
		study.DCM.save_as(study.CurrStudy.savefilename, write_like_original=True)


#---------------------------------------------------------------------------



def create_dir( dir_name, verbose=True ):
	try: 
		os.makedirs( dir_name )
	except OSError:
		if not os.path.isdir( dir_name ):
			print(f'Fatal Error: Failed to create dir: {dir_name}')
			raise
	else:
		if verbose:
			print(f'\n\t{dir_name} created OK')
		return True

def check_DICOM_fourCC( filename ):
	with open( filename, "r", encoding="Latin-1") as file:
		file.seek(128,0)
		line = file.read(4)
	if line == "DICM":
		return True
	else:
		print('\tfourcc says not DICOM -skipping file-')
		return False


	

