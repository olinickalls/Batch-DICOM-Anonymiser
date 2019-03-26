'''
Class definitions for 'Study' Class
encomapsses:
	openpyxl and pydicom objects
	simple variables (like cell and column definitions)
	methods:

'''
import pydicom
import openpyxl
import random
import getpass
import os
from datetime import date, time, datetime



alphalistboth = ['a','b','c','d','e','f','g','h','i','j','k','l','m','o','n','p','q','r',
								's','t','u','v','w','x','y','z','A','B','C','D','E','F','G','H','I','J',
								'K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
alphalistupper = ['A','B','C','D','E','F','G','H','I','J',
									'K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
alphalistlower = ['a','b','c','d','e','f','g','h','i','j','k','l','m','o','n','p','q','r',
									's','t','u','v','w','x','y','z' ]

digitlist = [ '0','1','2','3','4','5','6','7','8','9' ]


class Study_Class( ):
	# Some constants to use in this library - needs to replace much of the static parts of the XLS creation:
	# These are column or cell references prefixed with which sheet they belong in
	xlsPage_Title              = 'A1'

	xlsFront_study_title_cell    = 'B2'
	xlsFront_PI_cell             = 'B3'
	xlsFront_IRB_code_cell       = 'B4'
	xlsFront_number_of_study_IDs_cell = 'B5' 

	xlsData_study_IDs          = 'B'
	xlsData_date_added         = 'C'
	xlsData_time_added         = 'D'
	xlsData_patient_name       = 'G'
	xlsData_patient_ID         = 'I'
	xlsData_accession_number   = 'K'
	xlsData_study_date         = 'M'
	xlsData_study_time         = 'N'
	xlsData_study_UID          = 'P'
	xlsData_study_description  = 'R'

	xlsLog_date                = 'B'
	xlsLog_time                = 'C'
	xlsLog_activity            = 'E'
	xlsLog_user                = 'G'
	xlsLog_computer            = 'H'

	xls_UID_lookup             = {}
	test_study_UID             = ''
	# xlsLog_next_log_row        = 0
	next_log_row               = 0

	next_studyID_row           = 0


	frontsheet                 = 0
	datasheet                  = 0
	logsheet                   = 0

	# log levels: debug = 3, high = 2, normal = 1
	# This should reflect the default, then over-ridden by cmd line options. 
	loglevel_normal  = 1
	loglevel_high    = 2
	loglevel_debug   = 3
	global_log_level = 1
	loglevel_txt = { loglevel_normal: '', loglevel_high: 'High', loglevel_debug: 'DEBUG' }

	# Get these only once at the start of runtime.  No need to repeat for every new log entry.
	log_username     = getpass.getuser()
	log_computername = os.environ['COMPUTERNAME']


	# List of filenames to ignore. These will be skipped and not copied.
	skip_list = [ 'DICOMDIR',
				  'VERSION',
				  'LOCKFILE']

	# List of tags to raise warnings for if they are not present in loaded DCM files.
	dcm_tag_checklist       = [ 'PatientID',
								'PatientName',
								'AccessionNumber',
								'StudyInstanceUID',
								'StudyDate' ]



	# Assign the pydicom and openpyxl objects at start.  Some pylint warning were raised when DCM was set to 'False' rather than an object
	DCM = pydicom.Dataset()
	XLS = openpyxl.Workbook()


	# *****************************************************************************************************************************************
	# *                                                                                                                                       *
	# *                                           Start of Methods                                                                            *
	# *                                                                                                                                       *
	# *                                                                                                                                       *
	# *****************************************************************************************************************************************


	def load_xls( self, xls_filename ):
		"""
		Loads study XLS file, and does basic checking to make sure that it is actually a valid XLS sheet with check_xls_is_valid().
		Usage: study_workbook = load_study_xls( <filename> )
		Returns: openpyxl XLS workbook object
		"""
		# This is a mini-__init__
		self.global_log_level = self.loglevel_debug

		# back to the normal code
		self.xls_UID_lookup = {}
		valid = True
		validity_msg = ""

		try:
			self.XLS = openpyxl.load_workbook( xls_filename )
		except:
			#self.log_message( f'load_xls: {xls_filename} failed to load.', self.loglevel_normal )
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
			self.datasheet  = self.XLS['Data']
			self.logsheet   = self.XLS['Log']

			# Identify the first available log row
			self.find_first_available_log_row()
			self.log_message( f'<study_obj>.load_xls: xlsLog_next_log_row has been set and is {self.next_log_row}', self.loglevel_debug )

			# Load the existing UIDs into the dict cache
			# self.xls_UID_lookup = cache_existing_xls_UIDs( new_workbook )
			self.cache_existing_xls_UIDs( )


			# Identify row of the first available new studyID
			self.next_studyID_row = self.first_available_studyID_row( )


			self.log_message( f'load_xls: Complete OK. loaded {xls_filename} OK', self.loglevel_debug )

			return True

		else:
			#self.log_message( f'load_xls: {xls_filename} is not valid: {validity_msg}', self.loglevel_normal )
			print(f'load_xls: {xls_filename} failed to pass the checks. Did you edit it? FATAL ERROR')
			return False


# -----------------------> Create new 'blank' XLS from scratch. Does not load a blank XLS to do this.

	def new_XLS( self ):
		self.XLS = openpyxl.Workbook()
		self.xls_repopulate_attribs()



	def xls_repopulate_attribs( self ):
		'''
		Used in Init_Study.py after creating a new [blank] XLS file object
		Re-apply the basic attributes - populating things like shortcuts to the workbook sheets etc.
		This is essentially copied from the load_xls method.
		Re-opening and running the validation (in the .load_xls() method) should be done separately once the XLS has been saved.
		'''

		self.frontsheet = self.XLS['Front']
		self.datasheet  = self.XLS['Data']
		self.logsheet   = self.XLS['Log']

		# Identify the first available log row
		self.find_first_available_log_row()

		# Load the existing UIDs into the dict cache
		# self.xls_UID_lookup = cache_existing_xls_UIDs( new_workbook )
		self.cache_existing_xls_UIDs( )

		# Identify row of the first available new studyID
		self.next_studyID_row = self.first_available_studyID_row( )

		self.log_message( f'xls_repopulate_attribs: Completed OK.', self.loglevel_debug )













	def write_xls_to_disc ( self, filename ):

		self.XLS.save( filename )




	def cache_existing_xls_UIDs ( self ):
		"""
		Identifies each stored study UID and caches it and the corresponding row number in a dict\n
		Returns the absolute row number - not relative, so starts at 2 (as does the data) and ends at total_studyIDs + 1\n
		Usage: Study_Class.cache_existing_xls_UIDs ( )\n
		Returns:  True (no probs), False (error)  
		"""
		self.log_message( '<obj>.cache_existing_xls_UIDs(): Started.', self.loglevel_debug )
		
		self.xls_UID_lookup = {}

		row = 2
		max_row = int( self.frontsheet[ self.xlsFront_number_of_study_IDs_cell ].value ) + 1  # +1 as the data-containing rows start at row 2, not 1

		check_ptID      = self.datasheet[ self.xlsData_patient_ID + str(row) ].value
		check_studyID   = self.datasheet[ self.xlsData_study_IDs  + str(row) ].value
		check_study_UID = self.datasheet[ self.xlsData_study_UID  + str(row) ].value

		while (check_studyID != None ) and (check_ptID != None ) and (row <= max_row ) and (check_study_UID != None ):
			self.xls_UID_lookup[ check_study_UID ] = row
			row += 1
			check_ptID      = self.datasheet[ self.xlsData_patient_ID + str(row) ].value
			check_studyID   = self.datasheet[ self.xlsData_study_IDs  + str(row) ].value
			check_study_UID = self.datasheet[ self.xlsData_study_UID  + str(row) ].value

		self.log_message( f'self.cache_existing_xls_UIDs: Completed OK. Found&cached {len(self.xls_UID_lookup)} existing UIDs.  Final row={row}', self.loglevel_high )
		return True



	def find_first_available_log_row( self ):
		'''
		Identify the 1st free log row into which to write new messages\n
		Usage: Study_Class.find_first_available_log_row( )\n
		Returns: Int row number
		'''
		#self.log_message( f'find_first_available_log_row: Starting', self.loglevel_debug )
		
		row = 2   # This is the first logging row

		check_log_activitymsg = self.logsheet[ self.xlsLog_activity + str(row) ].value
	
		# if there is an activity msg (ie != None) then go to the next row and check again
		
		print(f'<study_obj>.find_first_available_log_row: start row = {row}')

		while (check_log_activitymsg != None ):
			#print(f'row {row} != None. Incrementing. Contains:\"{check_log_activitymsg}\"')
			row += 1
			check_log_activitymsg = self.logsheet[ self.xlsLog_activity + str(row) ].value


		self.next_log_row = row
		self.log_message( f'find_first_available_log_row: Completed. next_log_row = {self.next_log_row}', self.loglevel_debug )
		return row




	#------------------------------------------------------------------------------------------------------

	def log_message( self, message_str, msg_log_level = loglevel_normal ):
		'''
		This is supposed to add a new line to the log page in the XLS file, describing a change.
		Perhaps this is a good place to set log level...
		log levels: debug = 3, high = 2, normal = 1
		'''
		# Only logs messages that are at or below the global log level. 
		# So debug msgs will bot be logged in high or normal logging
		if ( msg_log_level > self.global_log_level ):
			return False

		# log date, time, activity, user, computer
		row_text = str( self.next_log_row )
		
		self.logsheet[ self.xlsLog_activity + row_text ] = f'({ self.loglevel_txt[ msg_log_level ] }): { message_str }'

		dateobject = datetime.now()

		self.logsheet[ self.xlsLog_date     + row_text ] = dateobject.strftime('%d-%m-%Y') # date  
		self.logsheet[ self.xlsLog_time     + row_text ] = dateobject.strftime('%H:%M:%S') # timenow
		self.logsheet[ self.xlsLog_user     + row_text ] = self.log_username               # username
		self.logsheet[ self.xlsLog_computer + row_text ] = self.log_computername           # compname

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
		max_row = self.frontsheet[ self.xlsFront_number_of_study_IDs_cell ].value + 1  # +1 as the data-containing rows start at row 2, not 1

		check_ptID    = self.datasheet[ self.xlsData_patient_ID + str(row)].value
		check_studyID = self.datasheet[ self.xlsData_study_IDs  + str(row)].value
	
		while (check_studyID != None ) and (check_ptID != None ) and (row <= max_row ):
			row += 1
			check_ptID    = self.datasheet[ self.xlsData_patient_ID + str(row)].value
			check_studyID = self.datasheet[ self.xlsData_study_IDs  + str(row)].value

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
		
		self.log_message( 'running: assign_next_free_studyID()', self.loglevel_debug )

		# If this is the 1st time running then do this
		if self.next_studyID_row == 0:
			self.next_studyID_row = self.first_available_studyID_row( )
		

		new_studyID    = self.datasheet[ self.xlsData_study_IDs + str( self.next_studyID_row ) ].value
		new_UID        = self.DCM.StudyInstanceUID
		no_of_studyIDs = self.frontsheet[ self.xlsFront_number_of_study_IDs_cell ].value


		# Check to see if we have exceeded available StudyIDs
		if self.next_studyID_row > ( no_of_studyIDs + 1) and new_studyID == None:
			#This will happen if we have run out of possible studyIDs
			# Actually, this 'else' statement is redundant but makes the code clearer to me.
			self.log_message( '<obj>.assign_next_free_studyID: Run out of Study IDs in the xls file!!!', self.loglevel_normal)
			return False
		elif self.next_studyID_row > ( no_of_studyIDs + 1) and new_studyID != None:
			# there is a mismatch- my code thinks we have exceeded the number of used studyIDs
			# However, new_studyID != None -ie the datacell in the XLS is not empty. We presume this cell contains a valid studyID...
			# A warning is logged however.
			self.log_message(f'<>.assign_next_free_studyID: WARNING -- next_studyID_row ({self.next_studyID_row}) is more than no_of_studyIDs ({no_of_studyIDs}) but XLScell is non-empty ({new_studyID}). Assuming it contains a valid studyID', self.loglevel_normal)


		#next_study_ID_generator = studytools.next_XLSrow_gen( starting_row, no_of_studyIDs, self.datasheet, self.xlsData_study_IDs )


		# Populate current pt data into XLS datasheet studyID into 
		dateobject = datetime.now()
		current_row_str = str( self.next_studyID_row )

		self.datasheet[ self.xlsData_date_added        +  current_row_str ] = str( dateobject.strftime('%d-%m-%Y') )
		self.datasheet[ self.xlsData_time_added        +  current_row_str ] = str( dateobject.strftime('%H:%M:%S') )

		self.datasheet[ self.xlsData_patient_ID        +  current_row_str ] = str( self.try_dcm_attrib( 'PatientID',        'Nil' ) )
		self.datasheet[ self.xlsData_patient_name      +  current_row_str ] = str( self.try_dcm_attrib( 'PatientName',      'Nil' ) )
	
		self.datasheet[ self.xlsData_accession_number  +  current_row_str ] = str( self.try_dcm_attrib( 'AccessionNumber',  'Nil' ) )
		self.datasheet[ self.xlsData_study_date        +  current_row_str ] = str( self.try_dcm_attrib( 'StudyDate',        'Nil' ) )
		self.datasheet[ self.xlsData_study_time        +  current_row_str ] = str( self.try_dcm_attrib( 'StudyTime',        'Nil' ) )
		self.datasheet[ self.xlsData_study_UID         +  current_row_str ] = str( self.try_dcm_attrib( 'StudyInstanceUID', 'Nil' ) )
		self.datasheet[ self.xlsData_study_description +  current_row_str ] = str( self.try_dcm_attrib( 'StudyDescription', 'Nil' ) )
		
		# insert Logging message(s) here. Only 1 will be sent- depending on global_log_level
		if self.log_message( 'running: assign_next_free_studyID() in generator loop', self.loglevel_debug ):
			pass
		elif self.log_message( f'Assigned { new_studyID } to { self.try_dcm_attrib(  "PatientID", "No_ID" ) }', self.loglevel_high ):
			pass
		else:
			self.log_message( f'Assigned new StudyID to {new_UID}', self.loglevel_normal )


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
		self.frontsheet['A' + str( self.xlsFront_study_title_cell[-1] ) ]         = 'Study Title:'          # data held in xlsFront_study_title_cell
		self.frontsheet['A' + str( self.xlsFront_PI_cell[-1] )          ]         = 'Primary Investigator:' # data held in xlsFront_PI_cell
		self.frontsheet['A' + str( self.xlsFront_number_of_study_IDs_cell[-1] ) ] = 'No of Study IDs'       # data held in xlsFront_number_of_study_IDs_cell
		self.frontsheet['A' + str( self.xlsFront_IRB_code_cell[-1] )    ]         = 'Study IRB Code'        # data held in xlsFront_IRB_code_cell

		self.frontsheet[ self.xlsFront_study_title_cell         ] = new_study_title
		self.frontsheet[ self.xlsFront_PI_cell                  ] = new_primary_investigator
		self.frontsheet[ self.xlsFront_number_of_study_IDs_cell ] = new_number_of_study_IDs
		self.frontsheet[ self.xlsFront_IRB_code_cell            ] = 'IRBcode1234'	

		# Row 1 is the column title row
		self.datasheet['A1']  = 'Data Page'
		self.datasheet[ self.xlsData_study_IDs  + '1']  = 'Study IDs'
		self.datasheet[ self.xlsData_date_added + '1']  = 'Date Added'
		self.datasheet[ self.xlsData_time_added + '1']  = 'Time Added'

		self.datasheet[ self.xlsData_patient_name  + '1'] = 'Patient Name'
		#self.datasheet[ self.xlsData_patient_firstname + '1'] = 'First Name'

		self.datasheet[ self.xlsData_patient_ID        + '1'] = 'Patient ID'
		self.datasheet[ self.xlsData_accession_number  + '1'] = 'Accession No.'
		self.datasheet[ self.xlsData_study_date        + '1'] = 'Study Date'
		self.datasheet[ self.xlsData_study_time        + '1'] = 'Study Time'
		self.datasheet[ self.xlsData_study_UID         + '1'] = 'Study UID'
		self.datasheet[ self.xlsData_study_description + '1'] = 'Study Description'

		self.logsheet['A1']   = 'Log Page'

		self.logsheet[ self.xlsLog_date + '1']   = 'Date'
		self.logsheet[ self.xlsLog_time + '1']   = 'Time'
		self.logsheet[ self.xlsLog_activity + '1']   = 'Log Activity'
		self.logsheet[ self.xlsLog_user + '1']   = 'User'
		self.logsheet[ self.xlsLog_computer + '1']   = 'Computer'

		
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

