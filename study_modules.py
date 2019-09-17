'''
Class definitions for 'Study' Class
encompasses:
    openpyxl and pydicom objects
    simple variables (like cell and column definitions)
    methods:
'''

# PEP 8 compliance is a work in progress... sigh 


import pydicom
from dicom_dictionary import DicomDictionary
import openpyxl
import random
import getpass
import os
from datetime import date, time, datetime


# ----------------------> Constants <-------------------------------

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

class FileStats_Class( ):
    # Basic counters etc. for use in file stats.
    # Keep it neat and easily dealt with by helper functions.
    
    # Stats for each iterated 'root' directory
    # Needs to be reset after each root is completed.
    dir_count = 0
    file_count = 0
    valid_DCM_file = 0
    copyOK = 0
    copyfailed = 0
    anonok = 0
    anonfailed = 0

    # Overall stats for the whole operation
    all_dir_count = 0
    all_file_count = 0
    all_valid_DCM_file = 0
    all_copyOK = 0
    all_copyfailed = 0
    all_anonok = 0
    all_anonfailed = 0
    skipped_dcm_filenames = []
    not_DCM_filenames = []
    tag_warning = []

    def reset_sub( self ):
        # All values back to zero (initialised values)
        self.dir_count = 0
        self.file_count = 0
        self.valid_DCM_file = 0
        self.copyOK = 0
        self.copyfailed = 0
        self.anonok = 0
        self.anonfailed = 0
    
    def start_subdir( self, subdirlist, filelist ):
        self.dir_count  += len( subdirlist )
        self.file_count += len( filelist )

    def subdir_complete( self ):
        # Nothing to do right now... ?Delete?
        return
    
    def update_rootdir_complete( self ):
        self.all_dir_count += self.dir_count
        self.all_file_count += self.file_count
        self.all_valid_DCM_file += self.valid_DCM_file
        self.all_copyOK += self.copyOK
        self.all_copyfailed += self.copyfailed
        self.all_anonok += self.anonok
        self.all_anonfailed += self.anonfailed




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


    #self.cfgsheet = xls['Config']

    Config_Start_Row = 3

    VR_Action_Col = 'A'
    VR_Val_Col = 'B'
    VR_RVal_Col = 'C'

    FLAG_COL = 'E'
    FLAG_VAL_COL = 'F'

    Tag_Name_Col = 'H'
    Tag_Group_Col = 'I'
    Tag_Element_Col = 'J'
    Tag_Action_Col = 'K'
    Tag_RVal_Col = 'L'

    vr_actions = {}
    vr_action_list = []
    list_of_vr_actions = ['set_all_AE', 'set_all_AS',
        'set_all_AT', 'set_all_CS',
        'set_all_DA', 'set_all_DS',
        'set_all_DT', 'set_all_FL',
        'set_all_FD', 'set_all_IS',
        'set_all_LO', 'set_all_LT',
        'set_all_OB', 'set_all_OD',
        'set_all_OF', 'set_all_OW',
        'set_all_PN', 'set_all_SH',
        'set_all_SL', 'set_all_SQ',
        'set_all_SS', 'set_all_ST',
        'set_all_TM', 'set_all_UI',
        'set_all_UL', 'set_all_UN',
        'set_all_US', 'set_all_UT'
        ]
    tag_actions = {}
    tag_action_list = []

    FLAGS_COL = 'F'

    #Please do not mess with the _CELL definitions below-
    # They need to tie in with the code to generate the
    # new blank XLS templates in create_new_study()
    # not sure how else to do it
    flags_dict = {}
    flags_list = [
        'DEL_PRIVATE_FLAGS',
        'DEL_CURVES_FLAG',
        'CROP_US_TOPBAR_FLAG'
        ]
    DEL_PRIVATE_FLAG_CELL = FLAGS_COL + '3'
    DEL_CURVES_FLAG_CELL = FLAGS_COL + '4'
    CROP_US_TOPBAR_FLAG_CELL = FLAGS_COL + '5'

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

    class CurrStudy():
        AnonName = ""
        AnonID = ""
        StudyInstanceUID = ""

        testfilename = ""
        savefilename = ""


    # *********************************************************************
    # *                                                                   *
    # *                     Start of Methods                              *
    # *                                                                   *
    # *                                                                   *
    # *********************************************************************

    # ####################################>  Helper function for .load_xls()
    def import_xls_settings( self ):
        # setup standard human-readable shortcuts (more readable for me...)
        self.frontsheet = self.XLS['Front']
        self.datasheet = self.XLS['Data']
        self.logsheet = self.XLS['Log']
        self.cfgsheet = self.XLS['Config']

        # Identify the first available log row
        self.find_first_available_log_row()

        # Load the existing UIDs into the dict cache
        self.cache_existing_xls_UIDs( )

        # Identify row of the first available new studyID
        self.next_studyID_row = self.first_available_studyID_row( )

        # Load config from the Config sheet <--------------------------
        # Flags:  to tidy- do I need both the FLAG and flags dict?
        self.DEL_PRIVATE_FLAG = self.cfgsheet[ self.DEL_PRIVATE_FLAG_CELL ].value
        self.flags_dict['DEL_PRIVATE_FLAG'] = self.cfgsheet[ self.DEL_PRIVATE_FLAG_CELL ].value
        
        self.DEL_CURVES_FLAG = self.cfgsheet[ self.DEL_CURVES_FLAG_CELL ].value
        self.flags_dict['DEL_CURVES_FLAG'] = self.cfgsheet[ self.DEL_CURVES_FLAG_CELL ].value

        self.CROP_US_TOPBAR_FLAG = self.cfgsheet[ self.CROP_US_TOPBAR_FLAG_CELL ].value
        self.flags_dict['CROP_US_TOPBAR_FLAG'] = self.cfgsheet[ self.CROP_US_TOPBAR_FLAG_CELL ].value

        print(f'Delete private flags: {self.DEL_PRIVATE_FLAG}')
        if self.CROP_US_TOPBAR_FLAG:
            print('Warning: US image cropping not yet implemented.')

        # VR based actions
        row = self.Config_Start_Row
        action = str(self.cfgsheet[ self.VR_Action_Col + str(row) ].value).lower()
        enabled = self.cfgsheet[ self.VR_Val_Col + str(row) ].value

        while action != None:
            if enabled:
                value_rep = action[-2:].upper()
                vr_action_list = [
                    action,
                    enabled,
                    self.cfgsheet[ self.VR_RVal_Col + str(row) ].value
                    ]
                self.vr_actions[value_rep] = vr_action_list
                print(f'row: {row}: {vr_action_list[-1]}')
            row += 1
            action = self.cfgsheet[ self.VR_Action_Col + str(row) ].value
            enabled = self.cfgsheet[ self.VR_Val_Col + str(row) ].value

        # Tag based actions
        row = self.Config_Start_Row
        rowstr = str(row)
        action = self.cfgsheet[ self.Tag_Action_Col + str(row) ].value

        while action != None:
            group = hex( int( self.cfgsheet[ self.Tag_Group_Col + rowstr].value, 16) )
            element = hex( int(self.cfgsheet[ self.Tag_Element_Col + rowstr].value, 16) )
            repvalue = str(self.cfgsheet[ self.Tag_RVal_Col + rowstr ].value)
            action = str(action)
            # Update tag name column in config sheet
            tagname = DicomDictionary.get( combotag( group, element ), [0,0,'** Unknown **'] )[2]  # [2] selects the tag name
            self.cfgsheet[ self.Tag_Name_Col + rowstr ].value = tagname
            self.tag_action_list.append([
                group,
                element,
                action,
                repvalue
                ])
            #print(f'row: {row}: ({group},{element}) action: {action}, rep value: {repvalue}')
            row += 1
            rowstr = str(row)
            action = self.cfgsheet[ self.Tag_Action_Col + rowstr ].value




    ####################################################> load_xls()
    def load_xls( self, xls_filename ):
        """
        Loads study XLS file, and does basic checking to make sure that it
        is actually a valid XLS sheet with check_xls_is_valid().
        Usage: study_workbook = load_study_xls( <filename> )
        Returns: openpyxl XLS workbook object
        """
        # mini-__init__
        self.xls_UID_lookup = {}  # new lookup dict for study UIDs 
        valid = True  # until proven false
        validity_msg = ""  # info about errors as we find them

        # Test for openpyxl failing to open XLS file
        try:
            self.XLS = openpyxl.load_workbook( xls_filename )
        except:
            print(f'load_xls: {xls_filename} failed to load. FATAL ERROR')
            raise

        # Test actually saving the XLS file before proceeding.
        try:
            self.XLS.save( xls_filename )
        except:
            print(f'{xls_filename} save permission denied.')
            print('Is the file open in excel?.\nPlease unlock and try again.')
            raise

        #-------------------   Validity Checks go here -----------

        if 'Front' not in self.XLS.sheetnames:
            valid = False
            validity_msg += "No \'Front\' sheet;"

        if 'Log' not in self.XLS.sheetnames:
            valid = False
            validity_msg += "No \'Log\' sheet;"

        if 'Data' not in self.XLS.sheetnames:
            valid = False
            validity_msg += "No \'Data\' sheet;"

        if 'Config' not in self.XLS.sheetnames:
            valid = False
            validity_msg += "No \'Config\' sheet;"

        #---------------------------------------------------------

        if valid:
            self.import_xls_settings(  )
            self.log( f'load_xls: Complete OK. loaded {xls_filename} OK',
                     self.LOGLEVEL_DEBUG
                    )
            return True
        else:
            print(f'load_xls: {xls_filename} failed checks. FATAL ERROR')
            return False


    #----------------------------------------------------------------------
    # Create new 'blank' XLS. Does not load a blank XLS to do this.

    def new_XLS( self ):
        self.XLS = openpyxl.Workbook()
        self.xls_populate_attribs()


    def xls_populate_attribs( self ):
        '''Used in Init_Study.py after creating a new [blank] XLS file object
        Populate things like shortcuts to the workbook sheets etc.
        This is essentially moved from the load_xls method.
        '''
        #Create readable shortcuts
        self.frontsheet = self.XLS['Front']
        self.datasheet = self.XLS['Data']
        self.logsheet = self.XLS['Log']
        self.cfgsheet = self.XLS['Config']
        
        #perform baseline evaluation of all new workbooks
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
        max_row = self.frontsheet[ self.XLSFRONT_NUMBER_OF_STUDYIDS_CELL ].value + 1
        # +1 as the data-containing rows start at row 2, not 1
        max_row = int( max_row )

        check_ptID = self.datasheet[self.XLSDATA_PATIENTID + str(row)].value
        check_studyID = self.datasheet[self.XLSDATA_STUDYIDS + str(row)].value
        check_study_UID = self.datasheet[self.XLSDATA_STUDYUID + str(row)].value

        while (check_studyID != None ) and (check_ptID != None ) and (row <= max_row ):
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
        'attribute' should be txt indicating the relevent data page column. 
        Use the static xls_Data_... column values from studytools.py
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
    




    def deidentifyDICOM( self, newPtName = 'Anon', newPtID = 'research' ):

        # ----------------> NEW configurable METHOD <-----------------------
        #Callback fn for removing private tags

        # enact FLAG based actions - need to sync this with excel file
        if self.DEL_PRIVATE_FLAG:
            self.DCM.remove_private_tags()
        
        if self.DEL_CURVES_FLAG:
             self.DCM.walk( del_curves_callback )
        
        # enact Value Representation (VR) based actions
        def Perform_VR_Actions(dataset, data_element):
            vr_str = data_element.VR
            if vr_str in self.vr_actions:
                new_val = self.vr_actions[vr_str][2]
                if new_val == None:
                    new_val = ""
                data_element.value = new_val

        self.DCM.walk(Perform_VR_Actions)

        # enact TAG-based actions
        for [group, element, action, repvalue] in self.tag_action_list:
            print(f'{pretty_tag(group,element)} action: {action}, rep value: {repvalue}')
            if [group,element] in self.DCM:
                old = self.DCM[group,element].value
            else:
                old = None
            
            if action.lower() == 'replace':
                if [group,element] in self.DCM:
                    self.DCM[group, element].value = repvalue
            elif action.lower() == 'delete':
                if [group,element] in self.DCM:
                    del self.DCM[group,element]

            if [group,element] in self.DCM:
                new = self.DCM[group,element].value
            else:
                new = None


        # ----------------> OLD METHOD <-----------------------
        if 'RequestAttributeSequence' in self.DCM:
            del self.DCM.RequestAttributesSequence
            print('Removing RequestAttributesSequence tag')

    # ---------------------> Moved from Init_Study
    # should return the openpyxl workbook object 
    def create_new_study( 	self, 
                            new_xlsfilename,
                            new_study_title,
                            new_primary_investigator,
                            new_number_of_study_IDs ):


        #new_study = Study_Class()
        self.XLS = openpyxl.Workbook()    # create new blank XLS object
        
        try:
            self.XLS.save( new_xlsfilename ) # Sanity check to make sure we can save
        except:
            print(f'Fatal Error: Failed to save \"{ new_xlsfilename }\"')
            raise
        else:
            print(f'Created blank template file \"{ new_xlsfilename }\" OK')


        self.frontsheet = self.XLS.active
        self.frontsheet.title = 'Front'

        self.datasheet = self.XLS.create_sheet('Data') 
        self.logsheet = self.XLS.create_sheet('Log' ) 
        self.cfgsheet = self.XLS.create_sheet('Config')  

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

        self.cfgsheet[ self.VR_Action_Col + '1' ] = 'ACTION'
        self.cfgsheet[ self.VR_Action_Col + '2' ] = '-'
        self.cfgsheet[ self.VR_Val_Col + '1' ] = 'Value'
        self.cfgsheet[ self.VR_Val_Col + '2' ] = '-'
        self.cfgsheet[ self.VR_RVal_Col + '1' ] = 'Replacement Value'
        self.cfgsheet[ self.VR_RVal_Col + '2' ] = '-'
        
        row = self.Config_Start_Row
        offset = 0

        #VR based action rules
        for action in self.list_of_vr_actions:
            self.cfgsheet[ self.VR_Action_Col + str(row + offset) ] = action
            offset += 1
        #flags - need to include current list of flags and default values
        self.cfgsheet[ self.FLAG_COL + '1' ] = 'FLAG'
        self.cfgsheet[ self.FLAG_VAL_COL + '1' ] = 'VALUE'

        # Note that there are _CELL definitions for each flag
        # but I am not sure how to make those without hardcoding.
        # For compatibility purposes, I am keeping few flags, and
        # keeping them in the same position
        row = self.Config_Start_Row
        offset = 0
        for flag in self.flags_list:
            self.cfgsheet[ self.FLAG_COL + str(row + offset)] = flag
            self.cfgsheet[ self.FLAG_VAL_COL + str(row + offset)] = 'FALSE'
            offset += 1

        #tags        
        self.cfgsheet[ self.Tag_Name_Col + '1' ] = 'Tag Name (autofilled)'
        self.cfgsheet[ self.Tag_Group_Col + '1' ] = 'Dicom Tag'
        self.cfgsheet[ self.Tag_Group_Col + '2' ] = 'group'
        self.cfgsheet[ self.Tag_Element_Col + '2' ] = 'element'
        self.cfgsheet[ self.Tag_Action_Col + '1' ] = 'Action'
        self.cfgsheet[ self.Tag_Action_Col + '1' ] = 'delete/replace'
        self.cfgsheet[ self.Tag_RVal_Col + '1' ] = 'Replacement Value'



        


        
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



def del_curves_callback(dataset, data_element):
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


# Consider embedding this into creat_rnd_studyID
# to make sure the ode to create is not duplicated
# or could turn into a function instead.
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




def create_rnd_studyID( format = 'lldddd', prefix='', suffix=''):

    # c = alphabetical char, d = digit
    # u = upper, l = lower

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

    newID += suffix

    return newID


def pretty_tag(group, element):
    '''Create a 'pretty' string for DICOM tag display
    input group and element hex strings
    This should match the style received from the XLS config sheet
    e.g. print( pretty_tag( "0x50", "0x8") )
    output: "(0050,0008)"
    '''
    group = str(group)[2:]
    group = group.rjust(4,"0")

    element = str(element)[2:]
    element = element.rjust(4,"0")
    
    return f'({group},{element})'


def combotag( group, element, outtype = 'int'):
    group = int(group, 16)
    element = int(element, 16)
    combotag = (group * 65536) + element
    if outtype.lower() == 'int':
        return combotag
    elif outtype.lower() == 'str':
        return hex(combotag)


pass

