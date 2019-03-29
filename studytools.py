'''
StudyTools.py

Functions for use with Study anonymiser/Study ID generator

'''
import openpyxl
import random
import getpass
import os
from datetime import date, time, datetime


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
xlsData_patient_lastname   = 'G'
xlsData_patient_firstname  = 'H'
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
xlsLog_next_log_row        = 0

# log levels: debug = 3, high = 2, normal = 1
# This should reflect the default, then over-ridden by cmd line options. 
global_log_level = 1

alphalistboth = ['a','b','c','d','e','f','g','h','i','j','k','l','m','o','n','p','q','r',
								 's','t','u','v','w','x','y','z','A','B','C','D','E','F','G','H','I','J',
								 'K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
alphalistupper = ['A','B','C','D','E','F','G','H','I','J',
									'K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
alphalistlower = ['a','b','c','d','e','f','g','h','i','j','k','l','m','o','n','p','q','r',
									's','t','u','v','w','x','y','z' ]

digitlist = [ '0','1','2','3','4','5','6','7','8','9' ]


#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#---------------------------             Logging Related Code           -------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------


def first_available_log_row( wb ):
	'''
	Identify the 1st free log row into which to write new messages
	Usage: next_low_row = first_available_log_row( <workbook object> )
	Returns: Int
	'''
	
	row = 2   # This is the first logging row

	check_log_activitymsg = wb[ 'Log' ][ xlsLog_activity + str(row)].value
 
 # if there is an activity msg (ie != None) then go to the next row and check again
	
	print(f'First_available_log_row: start row = {row}')
	while (check_log_activitymsg != None ):
		print(f'row {row} != None. Incrementing. Contains:\"{check_log_activitymsg}\"')
		row += 1
		check_log_activitymsg = wb[ 'Log' ][ xlsLog_activity + str(row) ].value

	return row


#------------------------------------------------------------------------------------------------------

def log_xls_creation ( workbook,
											 no_of_studyIDs,
	          					 studyID_prefix,
						           studyID_format ):
	'''
	Create/Setup the basic 'Log' sheet within the XLS file.
	And enter basic ceator log info.
	Usage: log_xls_creation ( <openpyxl workbook>, <No. of StudyIDs>, <StudyID Prefix>, <StudyID Format> )
	Returns: Nil
	'''

	wsLog   = workbook[ 'Log' ]

	username   = getpass.getuser()
	compname   = os.environ['COMPUTERNAME']
	dateobject = datetime.now()
	date       = dateobject.strftime('%d-%m-%Y')
	timenow    = dateobject.strftime('%H:%M:%S')

	row_text = '2'  # This can be set firmly as it is a new XLS file

	wsLog[ xlsLog_date     + row_text ] =  date  #'Date'
	wsLog[ xlsLog_time     + row_text ] =  timenow  #'Time'
	wsLog[ xlsLog_activity + row_text ] =  f'Created XLSX file (n={ no_of_studyIDs }, format={ studyID_prefix }{ studyID_format })'  #'Log Activity'
	wsLog[ xlsLog_user     + row_text ] =  username  #'User'
	wsLog[ xlsLog_computer + row_text ] =  compname  #'Computer'

#------------------------------------------------------------------------------------------------------

def log_message( workbook, message_str, next_log_row, msg_log_level = 3 ):
	'''
	This is supposed to add a new line to the log page in the XLS file, describing a change.
	Perhaps this is a good place to set log level...
	log levels: debug = 3, high = 2, normal = 1
	'''
	return True # skip this while I get the class re-write done

	# Only logs messages that are of or below the global log level. 
	# So debug msgs will bot be logged in high or normal logging
	if msg_log_level > global_log_level:
		return False

	# log date, time, activity, user, computer
	row_text = str( next_log_row )

	workbook['Log'][ xlsLog_activity + row_text ] = f'({ msg_log_level }): { message_str }'

	

	dateobject = datetime.now()

	workbook['Log'][ xlsLog_date     + row_text ] = dateobject.strftime('%d-%m-%Y') # date  
	workbook['Log'][ xlsLog_time     + row_text ] = dateobject.strftime('%H:%M:%S') # timenow
	workbook['Log'][ xlsLog_user     + row_text ] = getpass.getuser()               # username
	workbook['Log'][ xlsLog_computer + row_text ] = os.environ['COMPUTERNAME']      # compname

	# Finally increment the Log row pointer
	next_log_row += 1

	return True
	




#------------------------------------------------------------------------------------------------------

def write_xls_to_disc ( workbook, filename ):

	workbook.save( filename )

