'''
Class definitions for 'Study' Class
encomapsses:
	openpyxl and pydicom objects
	simple variables (like cell and column definitions)
	methods:
'''

# PEP 8 compliance is a work in progress... sigh 


import pydicom
import openpyxl
import random
import getpass
import os
from datetime import date, time, datetime



alphalistboth = ['a','b','c','d','e','f','g','h','i','j','k','l','m','o','n',
                 'p','q','r','s','t','u','v','w','x','y','z','A','B','C','D',
				 'E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S',
				 'T','U','V','W','X','Y','Z'
				]
alphalistupper = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N',
                  'O','P','Q','R','S','T','U','V','W','X','Y','Z'
				 ]
alphalistlower = ['a','b','c','d','e','f','g','h','i','j','k','l','m','o',
                  'n','p','q','r','s','t','u','v','w','x','y','z' 
				 ]

digitlist = [ '0','1','2','3','4','5','6','7','8','9' ]


class Study_Class( ):
	# Some constants to use in this library
	# These are column or cell references prefixed by the sheet they belong in
	# The constants could be moved into a separate 'from _ import *' as they
	# don't, need to be accessed through the class -I just want them global

	XLSPAGE_TITLE = 'A1'

	XLSFRONT_STUDYTITLE_CELL = 'B2'
	XLSFRONT_PI_CELL = 'B3'
	XLSFRONT_IRB_CODE_CELL = 'B4'
	XLSFRONT_NUMBER_OF_STUDYIDS_CELL = 'B5' 

	XLSDATA_STUDYIDS = 'B'
	XLSDATA_DATEADDED = 'C'
	XLSDATA_TIMEADDED = 'D'
	XLSDATA_PATIENTNAME = 'G'
	XLSDATA_PATIENTID = 'I'
	XLSDATA_ACCESSIONNUMBER = 'K'
	XLSDATA_STUDYDATE = 'M'
	XLSDATA_STUDYTIME = 'N'
	XLSDATA_STUDYUID = 'P'
	XLSDATA_STUDYDESCRIPTION = 'R'

	XLSLOG_DATE = 'B'
	XLSLOG_TIME = 'C'
	XLSLOG_ACTIVITY = 'E'
	XLSLOG_USER = 'G'
	XLSLOG_COMPUTER = 'H'

	xls_UID_lookup             = {}
	test_study_UID             = ''
	
	next_log_row               = 0
	next_studyID_row           = 0

	# These will have values assigned after the workbook is opened
	frontsheet = None
	datasheet = None
	logsheet = None

	# log levels: debug = 3, high = 2, normal = 1
	# This should reflect the default, then over-ridden by cmd line options.
	LOGLEVEL_NORMAL = 1
	LOGLEVEL_HIGH = 2
	LOGLEVEL_DEBUG = 3
	GLOBAL_LOGLEVEL = 1
	LOGLEVEL_TXT = {LOGLEVEL_NORMAL: '',
	                LOGLEVEL_HIGH: 'High', 
					LOGLEVEL_DEBUG: 'DEBUG'
				   }

	# Get these only once at the start of runtime.
	log_username = getpass.getuser()
	log_computername = os.environ['COMPUTERNAME']

	# List of filenames to ignore. These will be skipped and not copied.
	SKIP_LIST = ['DICOMDIR',
				 'VERSION',
				 'LOCKFILE'
				]

	# List of tags to raise warnings for if they are not present
	# in the loaded DCM files.
	DCM_TAG_CHECKLIST = ['PatientID',
						 'PatientName',
						 'AccessionNumber',
						 'StudyInstanceUID',
						 'StudyDate'
						]

	# Assign the pydicom and openpyxl objects at start.
	# Some pylint warning were raised when DCM was set to 'False'
	DCM = pydicom.Dataset()
	XLS = openpyxl.Workbook()


	# *********************************************************************
	# *                                                                   *
	# *                     Start of Methods                              *
	# *                                                                   *
	# *                                                                   *
	# *********************************************************************


	def load_xls( self, xls_filename ):
		"""
		Loads study XLS file, and does basic checking to make sure that it
		is actually a valid XLS sheet with check_xls_is_valid().
		Usage: study_workbook = load_study_xls( <filename> )
		Returns: openpyxl XLS workbook object
		"""
		# This is a mini-__init__
		self.GLOBAL_LOGLEVEL = self.LOGLEVEL_DEBUG

		# back to the normal code
		self.xls_UID_lookup = {}
		valid = True
		validity_msg = ""

		try:
			self.XLS = openpyxl.load_workbook( xls_filename )
		except:
			print(f'load_xls: {xls_filename} failed to load. FATAL ERROR')
			exit()

		#********************   Validity Checks go here *********************

		if 'Front' not in self.XLS.sheetnames:
			valid = False
			validity_msg += "No \'Front\' sheet;"

		if 'Log' not in self.XLS.sheetnames:
			valid = False
			validity_msg += "No \'Log\' sheet;"

		if 'Data' not in self.XLS.sheetnames:
			valid = False
			validity_msg += "No \'Data\' sheet;"

		#*********************************************************************

		if valid:

			self.frontsheet = self.XLS['Front']
			self.datasheet = self.XLS['Data']
			self.logsheet = self.XLS['Log']

			# Identify the first available log row
			self.find_first_available_log_row()

			# Load the existing UIDs into the dict cache
			self.cache_existing_xls_UIDs( )

			# Identify row of the first available new studyID
			self.next_studyID_row = self.first_available_studyID_row( )

			self.log( f'load_xls: Complete OK. loaded {xls_filename} OK',
			         self.LOGLEVEL_DEBUG
					)

			return True

		else:
			print(f'load_xls: {xls_filename} failed checks. FATAL ERROR')
			return False


# Create new 'blank' XLS from scratch. Does not load a blank XLS to do this.

	def new_XLS( self ):
		self.XLS = openpyxl.Workbook()
		self.xls_populate_attribs()


	def xls_populate_attribs( self ):
		'''Used in Init_Study.py after creating a new [blank] XLS file object
		Populate things like shortcuts to the workbook sheets etc.
		This is essentially moved from the load_xls method.
		'''
		self.frontsheet = self.XLS['Front']
		self.datasheet = self.XLS['Data']
		self.logsheet = self.XLS['Log']

		self.find_first_available_log_row()
		self.cache_existing_xls_UIDs( )
		self.next_studyID_row = self.first_available_studyID_row( )

		self.log( f'xls_repopulate_attribs: Complete.', self.LOGLEVEL_DEBUG )


	def write_xls_to_disc(self, filename):
		'''Alternative route to the openpyxl .save method
		'''
		self.XLS.save( filename )


	def cache_existing_xls_UIDs(self):
		"""Identifies each stored study UID and caches both it and its row number
		in a dictionary object.\n
		Returns the absolute row number - not relative
		-so starts at 2 (as does the data) and ends at total_studyIDs + 1\n
		Usage: <obj>.cache_existing_xls_UIDs()\n
		Returns:  True (no probs), False (error)  
		"""
		self.log('.cache_existing_xls_UIDs(): Started.', self.LOGLEVEL_DEBUG )
		
		# Probably unnecessary re-definition
		self.xls_UID_lookup = {}

		row = 2
		max_row = int( self.frontsheet[ self.XLSFRONT_NUMBER_OF_STUDYIDS_CELL ].value ) + 1  # +1 as the data-containing rows start at row 2, not 1

		check_ptID      = self.datasheet[ self.XLSDATA_PATIENTID + str(row) ].value
		check_studyID   = self.datasheet[ self.XLSDATA_STUDYIDS  + str(row) ].value
		check_study_UID = self.datasheet[ self.XLSDATA_STUDYUID  + str(row) ].value

		while (check_studyID != None ) and (check_ptID != None ) and (row <= max_row ) and (check_study_UID != None ):
			self.xls_UID_lookup[ check_study_UID ] = row
			row += 1
			check_ptID      = self.datasheet[ self.XLSDATA_PATIENTID + str(row) ].value
			check_studyID   = self.datasheet[ self.XLSDATA_STUDYIDS  + str(row) ].value
			check_study_UID = self.datasheet[ self.XLSDATA_STUDYUID  + str(row) ].value

		self.log( f'self.cache_existing_xls_UIDs: Completed OK. Found&cached {len(self.xls_UID_lookup)} existing UIDs.  Final row={row}', self.LOGLEVEL_HIGH )
		return True



	def find_first_available_log_row( self ):
		'''
		Identify the 1st free log row into which to write new messages\n
		Usage: Study_Class.find_first_available_log_row( )\n
		Returns: Int row number
		'''
		row = 2   # This is the first possible logging row

		log_check = self.logsheet[ self.XLSLOG_ACTIVITY + str(row) ].value
	
		# if there is an activity msg (ie != None) 
		# then go to the next row and check again
		while (log_check is not None ):
			row += 1
			log_check = self.logsheet[ self.XLSLOG_ACTIVITY + str(row) ].value

		self.next_log_row = row
		self.log(f'find_first_available_log_row: row={self.next_log_row}',
		         self.LOGLEVEL_DEBUG
				)

		return row




	#------------------------------------------------------------------------------------------------------

	def log( self, message_str, msg_log_level=LOGLEVEL_NORMAL ):
		'''
		This is supposed to add a new line to the log page in the XLS file, describing a change.
		Perhaps this is a good place to set log level...
		log levels: debug = 3, high = 2, normal = 1
		'''
		# Only logs messages that are at or below the global log level. 
		# So debug msgs will bot be logged in high or normal logging
		if ( msg_log_level > self.GLOBAL_LOGLEVEL ):
			return False

		# log date, time, activity, user, computer
		row_text = str( self.next_log_row )
		
		self.logsheet[ self.XLSLOG_ACTIVITY + row_text ] = f'({ self.LOGLEVEL_TXT[ msg_log_level ] }): { message_str }'

		dateobject = datetime.now()

		self.logsheet[ self.XLSLOG_DATE     + row_text ] = dateobject.strftime('%d-%m-%Y') # date  
		self.logsheet[ self.XLSLOG_TIME     + row_text ] = dateobject.strftime('%H:%M:%S') # timenow
		self.logsheet[ self.XLSLOG_USER     + row_text ] = self.log_username               # username
		self.logsheet[ self.XLSLOG_COMPUTER + row_text ] = self.log_computername           # compname

		# Finally increment the Log row pointer
		self.next_log_row += 1

		return True





	def get_DCM_StudyInstanceUID( self ):
		'''
		Returns the Study Instance UID from the specified DICOM file object
		Usage:   string_variable = <object>.get_DCM_StudyInstanceUID( )
		Returns:  a string containing the study instance UID.
							returns FALSE if no StudyInstanceUID tag is found.
		This iterates through all tags until it finds the correct one.
			This bypasses the issue with DICOMDIR hiding it in a ?series?
			which is not visible to the standard dicom_object.StudyInstanceUID method.
		'''
		siUID = False

		for elem in self.DCM.iterall():
			if 'Study Instance UID' == elem.name:
				siUID = elem.value
				break   # Stops at 1st StudyInstanceUID

		# If no StudyInstanceUID tag is found, this returns False
		return siUID







	def get_old_study_attrib_from_UID( self, attribute, test_uid ):
		'''
		Returns string from relevent cell in Data sheet from the workbook.
		Takes the studyUID and str 'attribute' as reference
		Usage: get_old_study_attrib( <openpyxl workbook>, <existing study UID>, <str attribute> )
		'attribute' should be txt indicating the relevent data page column. Use the static xls_Data_... column values from studytools.py
		eg. xls_Data_study_UID
		'''

		old_study_ID = self.datasheet[ attribute + str( self.xls_UID_lookup[ test_uid ] )  ].value

		return old_study_ID
	







	def first_available_studyID_row ( self ):
		"""
		Identifies the FIRST available studyID in the XLS file
		This is slow, so separated from (but called by) the NEXT study ID generator
		Returns the absolute row number - not relative, so starts at 2 (as does the data) and ends at total_studyIDs + 1
		Usage: first_blank_ptID_row =  first_available_studyID_row ( <openpyxl xls workbook> )
		Returns: 1st free row where a studyID can be assigned. 
		"""

		row = 2
		max_row = self.frontsheet[ self.XLSFRONT_NUMBER_OF_STUDYIDS_CELL ].value + 1  # +1 as the data-containing rows start at row 2, not 1

		check_ptID    = self.datasheet[ self.XLSDATA_PATIENTID + str(row)].value
		check_studyID = self.datasheet[ self.XLSDATA_STUDYIDS  + str(row)].value
	
		while (check_studyID != None ) and (check_ptID != None ) and (row <= max_row ):
			row += 1
			check_ptID    = self.datasheet[ self.XLSDATA_PATIENTID + str(row)].value
			check_studyID = self.datasheet[ self.XLSDATA_STUDYIDS  + str(row)].value

		return row



	def try_dcm_attrib( self, attrib_str, failure_value ):
		'''
		PYDICOM crashes if the queried data element is not present. Often happens in some anonymised DICOMs.
		This is a quick & dirty but 'safe' method to query and return something.
		Usage: some_var = <>.try_dcm_attrib( <attribute string>, <failure string> )
		Returns: on success returns the value held in the DICOM object attribute provided.
			On failure, returns the failure string.
		'''
		try:
				value = self.DCM.data_element( attrib_str ).value
		except:
				value = failure_value

		return value
				







	## - This method is flawed. It does not work as intended- wrong use of generator.
	# - I expect it runs the whole method EVERY time its is run. This is slow.


	def assign_next_free_studyID ( self ):   #XLS openpyxl workbook object
		'''
		Returns the new studyID, populates current DCM data into corresponding datasheet row & logs made
		and iterates down the studyID list with each new call.
		Built-in check to see if exceeded number of valid studyIDs
		
		'''
		
		self.log( 'running: assign_next_free_studyID()', self.LOGLEVEL_DEBUG )

		# If this is the 1st time running then do this
		if self.next_studyID_row == 0:
			self.next_studyID_row = self.first_available_studyID_row( )
		

		new_studyID    = self.datasheet[ self.XLSDATA_STUDYIDS + str( self.next_studyID_row ) ].value
		new_UID        = self.DCM.StudyInstanceUID
		no_of_studyIDs = self.frontsheet[ self.XLSFRONT_NUMBER_OF_STUDYIDS_CELL ].value


		# Check to see if we have exceeded available StudyIDs
		if self.next_studyID_row > ( no_of_studyIDs + 1) and new_studyID == None:
			#This will happen if we have run out of possible studyIDs
			# Actually, this 'else' statement is redundant but makes the code clearer to me.
			self.log( '<obj>.assign_next_free_studyID: Run out of Study IDs in the xls file!!!', self.LOGLEVEL_NORMAL)
			return False
		elif self.next_studyID_row > ( no_of_studyIDs + 1) and new_studyID != None:
			# there is a mismatch- my code thinks we have exceeded the number of used studyIDs
			# However, new_studyID != None -ie the datacell in the XLS is not empty. We presume this cell contains a valid studyID...
			# A warning is logged however.
			self.log(f'<>.assign_next_free_studyID: WARNING -- next_studyID_row ({self.next_studyID_row}) is more than no_of_studyIDs ({no_of_studyIDs}) but XLScell is non-empty ({new_studyID}). Assuming it contains a valid studyID', self.LOGLEVEL_NORMAL)


		#next_study_ID_generator = studytools.next_XLSrow_gen( starting_row, no_of_studyIDs, self.datasheet, self.xlsData_study_IDs )


		# Populate current pt data into XLS datasheet studyID into 
		dateobject = datetime.now()
		current_row_str = str( self.next_studyID_row )

		self.datasheet[ self.XLSDATA_DATEADDED        +  current_row_str ] = str( dateobject.strftime('%d-%m-%Y') )
		self.datasheet[ self.XLSDATA_TIMEADDED        +  current_row_str ] = str( dateobject.strftime('%H:%M:%S') )

		self.datasheet[ self.XLSDATA_PATIENTID        +  current_row_str ] = str( self.try_dcm_attrib( 'PatientID',        'Nil' ) )
		self.datasheet[ self.XLSDATA_PATIENTNAME      +  current_row_str ] = str( self.try_dcm_attrib( 'PatientName',      'Nil' ) )
	
		self.datasheet[ self.XLSDATA_ACCESSIONNUMBER  +  current_row_str ] = str( self.try_dcm_attrib( 'AccessionNumber',  'Nil' ) )
		self.datasheet[ self.XLSDATA_STUDYDATE        +  current_row_str ] = str( self.try_dcm_attrib( 'StudyDate',        'Nil' ) )
		self.datasheet[ self.XLSDATA_STUDYTIME        +  current_row_str ] = str( self.try_dcm_attrib( 'StudyTime',        'Nil' ) )
		self.datasheet[ self.XLSDATA_STUDYUID         +  current_row_str ] = str( self.try_dcm_attrib( 'StudyInstanceUID', 'Nil' ) )
		self.datasheet[ self.XLSDATA_STUDYDESCRIPTION +  current_row_str ] = str( self.try_dcm_attrib( 'StudyDescription', 'Nil' ) )
		
		# insert Logging message(s) here. Only 1 will be sent- depending on global_log_level
		if self.log( 'running: assign_next_free_studyID() in generator loop', self.LOGLEVEL_DEBUG ):
			pass
		elif self.log( f'Assigned { new_studyID } to { self.try_dcm_attrib(  "PatientID", "No_ID" ) }', self.LOGLEVEL_HIGH ):
			pass
		else:
			self.log( f'Assigned new StudyID to {new_UID}', self.LOGLEVEL_NORMAL )


		# Update the dict_cache.  This is a hack. Better to use in a class probably.
		self.xls_UID_lookup[ new_UID ] = self.next_studyID_row


		# Increment next_studyID_row to point to the next row
		self.next_studyID_row += 1

		# return the new studyID string  
		
		return new_studyID
	




	#	These are fairly specific- taken from sample DICOM studies.

	def deidentifyDICOM( self, newPtName = 'Anon', newPtID = 'research' ):

		# print(f'deidentifyDICOM received newPtName={newPtName} \tnewPtID={newPtID} ')

		self.DCM.remove_private_tags()
		self.DCM.walk( tag_data_type_callback )
		self.DCM.walk( curves_callback )

		# (0008, ) tags

		self.DCM.AccessionNumber = ''  
		self.DCM.StudyID = ''           # Often contains the same data as AccessionNumber
		# DCOobj.StudyDescription = ''
		self.DCM.InstitutionalDepartmentName = 'St Elsewhere Radiology'
		self.DCM.InstitutionAddress = ''   # (0008, 0081) 

		# (0010, ) tags
		self.DCM.PatientID = newPtID   # (0008, 0020)
		self.DCM.PatientName = newPtName   # (0008, 0010)
		self.DCM.PatientBirthDate = ''   # (0008, 0030)
		self.DCM.InstitutionName = 'St Elsewhere'   # (0008, 0080)
		self.DCM.StationName = 'anon MRI Station'   # (0008, 1010)
		self.DCM.PerformedStationName	= 'anon MRI Station'   # (0008, 0242)
		self.DCM.PerformedLocation = 'anon MRI Station'	    # (0008, 0243)
		self.DCM.PerformedProcedureStepStartDate = ''	 
		self.DCM.PerformedProcedureStepStartTime = ''	 
		self.DCM.PerformedProcedureStepEndDate = 	''
		self.DCM.PerformedProcedureStepEndTime = ''
		self.DCM.PerformedProcedureStepID = ''
		self.DCM.PerformedProcedureStepDescription = ''
		self.DCM.ScheduledProcedureStepDescription = ''
		self.DCM.ScheduledProcedureStepID = ''
		self.DCM.RequestedProcedureID = ''
		self.DCM.DeviceSerialNumber = ''
		self.DCM.PlateID = ''
		self.DCM.DetectorDescription = ''
		self.DCM.DetectorID = ''

		if 'RequestAttributeSequence' in self.DCM:
			del self.DCM.RequestAttributesSequence
			print('Removing RequestAttributesSequence tag')


		#try:
		#	del DCOobj.RequestAttributesSequence
		#except Exception as e:
		#	pass

	# ---------------------> Moved from Init_Study
	# should return the openpyxl workbook object 
	def create_new_study( 	self, 
							new_xlsfilename,
							new_study_title,
							new_primary_investigator,
							new_number_of_study_IDs ):


		#new_study = Study_Class()
		self.XLS = openpyxl.Workbook()    # create new blank XLS
		
		try:
			self.XLS.save( new_xlsfilename )
		except:
			print(f'Fatal Error: Failed to save \"{ new_xlsfilename }\"')
			raise
		else:
			print(f'Created blank template file \"{ new_xlsfilename }\" OK')


		self.frontsheet       = self.XLS.active
		self.frontsheet.title = 'Front'

		self.datasheet = self.XLS.create_sheet('Data') # insert log sheet at the end
		self.logsheet  = self.XLS.create_sheet('Log' ) # insert log sheet at the end

		#--------------------->  Add in basic data  <-------------------------

		# Col A is the list of titles. Text info is in col B.
		self.frontsheet['A1']                                                     = 'Front Page'            
		self.frontsheet['A' + str( self.XLSFRONT_STUDYTITLE_CELL[-1] ) ]         = 'Study Title:'          # data held in xlsFront_study_title_cell
		self.frontsheet['A' + str( self.XLSFRONT_PI_CELL[-1] )          ]         = 'Primary Investigator:' # data held in xlsFront_PI_cell
		self.frontsheet['A' + str( self.XLSFRONT_NUMBER_OF_STUDYIDS_CELL[-1] ) ] = 'No of Study IDs'       # data held in xlsFront_number_of_study_IDs_cell
		self.frontsheet['A' + str( self.XLSFRONT_IRB_CODE_CELL[-1] )    ]         = 'Study IRB Code'        # data held in xlsFront_IRB_code_cell

		self.frontsheet[ self.XLSFRONT_STUDYTITLE_CELL         ] = new_study_title
		self.frontsheet[ self.XLSFRONT_PI_CELL                  ] = new_primary_investigator
		self.frontsheet[ self.XLSFRONT_NUMBER_OF_STUDYIDS_CELL ] = new_number_of_study_IDs
		self.frontsheet[ self.XLSFRONT_IRB_CODE_CELL            ] = 'IRBcode1234'	

		# Row 1 is the column title row
		self.datasheet['A1']  = 'Data Page'
		self.datasheet[ self.XLSDATA_STUDYIDS  + '1']  = 'Study IDs'
		self.datasheet[ self.XLSDATA_DATEADDED + '1']  = 'Date Added'
		self.datasheet[ self.XLSDATA_TIMEADDED + '1']  = 'Time Added'

		self.datasheet[ self.XLSDATA_PATIENTNAME  + '1'] = 'Patient Name'
		#self.datasheet[ self.xlsData_patient_firstname + '1'] = 'First Name'

		self.datasheet[ self.XLSDATA_PATIENTID        + '1'] = 'Patient ID'
		self.datasheet[ self.XLSDATA_ACCESSIONNUMBER  + '1'] = 'Accession No.'
		self.datasheet[ self.XLSDATA_STUDYDATE        + '1'] = 'Study Date'
		self.datasheet[ self.XLSDATA_STUDYTIME        + '1'] = 'Study Time'
		self.datasheet[ self.XLSDATA_STUDYUID         + '1'] = 'Study UID'
		self.datasheet[ self.XLSDATA_STUDYDESCRIPTION + '1'] = 'Study Description'

		self.logsheet['A1']   = 'Log Page'

		self.logsheet[ self.XLSLOG_DATE + '1']   = 'Date'
		self.logsheet[ self.XLSLOG_TIME + '1']   = 'Time'
		self.logsheet[ self.XLSLOG_ACTIVITY + '1']   = 'Log Activity'
		self.logsheet[ self.XLSLOG_USER + '1']   = 'User'
		self.logsheet[ self.XLSLOG_COMPUTER + '1']   = 'Computer'

		
	#------------------------------------------------------------------------------------------------------


############### END OF STUDY_CLASS DEFINITION ###################




#---------------------------------------------------------
#      Accessory functions related to deidentification
#---------------------------------------------------------


def tag_data_type_callback(dataset, data_element):

	# blank all person name ('PN') values
	if data_element.VR == 'PN':
		data_element.value = 'anonymous'

	# blank all date ('DA') values
	elif data_element.VR == 'DA':
		data_element.value = ''

	# blank all time ('TM') values
	elif data_element.VR == 'TM':
		data_element.value = ''




def curves_callback(dataset, data_element):
	if data_element.tag.group & 0xFF00 == 0x5000:
		del dataset[data_element.tag]





######################################################################

#---------------------------------------------------------
#      Accessory functions related to creating a new XLS (mostly for Init_Study.py)
#---------------------------------------------------------




# Console text input and return valid string 
def verify_txt_input( message = 'no argument supplied'):

	inputtext = input( message )

	while not inputtext.replace(' ','').isalpha():
		print('Invalid text entry. Please enter alphabetical characters only.')
		inputtext = input( message )

	return inputtext


def number_possible_IDs( format ):
	format = format.lower().strip()

	poss = 0
	if len(format) > 0:
		poss = 1

	for letter in format:
		if letter =='c': #if is character
			poss *= len(alphalistboth)
		elif letter =='u': #if is character
			poss *= len(alphalistupper)
		elif letter =='l': #if is character
			poss *= len(alphalistlower)
		elif letter =='d': #if is digit
			poss *= len(digitlist)

	return poss




def create_rnd_studyID( format = 'lldddd', prefix=''):

	# c = alphabetical char, d = digit

	# c can be anything from 'a' to 'Z'
	# d can be 0-9
	# Max studyID length = 16 chars (DICOM Limit for Pt ID)
	# prefix string inserted at the beginning

	# future implementation could apply upper/lower limits 
	#  to accommodate adding to an existing list of study IDs

	# Quick validation
	
	format = format.lower()
	newID = prefix

	#1 - check input - assume input has been validated in calling function
	#                  to prevent running same checks 1000s of times

	#2 - Step through format string and append ID string with appropriate random char/digit
	letter = ''

	for letter in format.strip():
		secure_random = random.SystemRandom()
		if letter =='c': #if is character
			newID += secure_random.choice(alphalistboth)
		elif letter =='u': #if is character
			newID += secure_random.choice(alphalistupper)
		elif letter =='l': #if is character
			newID += secure_random.choice(alphalistlower)

		elif letter =='d': #if is digit
			newID += secure_random.choice(digitlist)

	return newID




pass

