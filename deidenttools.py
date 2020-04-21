# deident_helper.py
# Helper functions etc. for batch deident_helper

import pydicom
# import openpyxl
import os

# ####################################################################
# #                         Ops class                                #
# ####################################################################


class Ops_Class():
    QUIET = False
    VERBOSE = False
    DEBUG = False

    def msg(self, message, level='NORMAL', endstr='\n'):
        # level should correlate with Quiet/Normal/Verbose string
        # if level arg is omitted, it will default to 'NORMAL'
        if self.QUIET:  # Quiet prints nothing
            return
        if self.VERBOSE or self.DEBUG:  # verbose prints everything
            print(message, end=endstr)
            return
        # Only not QUIET or VERBOSE reaches this point.
        if level == 'NORMAL':
            print(message)


# ####################################################################
# #                        PROCESS_FILE                              #
# ####################################################################

def process_file(study, filename: str) -> int:
    # ----------- Try to open with pydicom
    try:
        study.DCM = pydicom.filereader.dcmread(filename, force=True)

        load_warning = ''

        for tag in study.DCM_TAG_CHECKLIST:
            # this fn. returns '-blank' (as supplied failure string) if the
            # queried tag is not present.
            if study.try_dcm_attrib(tag, '-blank-') == '-blank-':
                load_warning += (tag + ' ')

    except:  # noqa If file loading fails for whatever reason
        study.msg('\t-File load failed')
        return False

    if load_warning != '':
        study.msg(f'{filename} : {load_warning}\n\t\t')

    study.msg('De-identify', endstr='')

    # Get the DCM StudyInstanceUID.
    # If there is no StudyInstanceUID tag (bad file) returns False
    study.check_si_UID = study.get_DCM_StudyInstanceUID()

    # If StudyTime tag is absent, make one
    if 'StudyTime' not in study.DCM:
        study.DCM.StudyTime = "000000"

    # update the values in study.CurrStudy class
    study._update_fromDCM()

    # Check if StudyInstanceUID has match in cache
    if study.check_si_UID in study.xls_UID_lookup:
        # retrieve the previous studyID linked to the UID
        study.CurrStudy.AnonID = study.get_old_study_attrib_from_UID(
            study.XLSDATA_DEIDUID,
            study.check_si_UID
            )
        print(f' - Known UID, using {study.CurrStudy.AnonID}')
    else:
        # If UNIQUE study UID ie. not in cache
        study.CurrStudy.AnonID = study.assign_new_si_UID()
        print(f' - Unique UID - Assigning {study.CurrStudy.AnonID}')

    # Perform deidentification on loaded DICOM data
    study.deidentifyDICOM(study.CurrStudy.AnonName, study.CurrStudy.AnonID)

    # replace the preamble.
    study.DCM.preamble = study.NEW_PREAMBLE

    # todo: Change tag to show DCM is deidentified/anonymised
    # as per relevent standard [needs reference]

    # Write de-identified DICOM to disc
    study.DCM.save_as(study.CurrStudy.savefilename, write_like_original=True)

    return True

# ---------------------------------------------------------------------------


def create_dir(dir_name, verbose=True):
    try:
        os.makedirs(dir_name)
    except OSError:
        if not os.path.isdir(dir_name):
            print(f'Fatal Error: Failed to create dir: {dir_name}')
            raise
    else:
        if verbose:
            print(f'\n\t{dir_name} created OK')
        return True


def check_fourCC(filename):
    with open(filename, "r", encoding="Latin-1") as file:
        file.seek(128, 0)
        line = file.read(4)
    if line == "DICM":
        return True
    else:
        return False


def try_dcm_attrib(study, attrib_str, failure_value):
    '''
    PYDICOM crashes if the queried data element is not present.
    Often happens in some anonymised/internet DICOMs.
    This is a quick & dirty but 'safe' method to query and return something.
    Usage: var = <>.try_dcm_attrib( <attribute string>, <failure string> )
    Returns: on success returns the value held in the DICOM object attribute.
        On failure, returns the failure string.
    '''
    try:
        # todo: Does this always fail?
        value = study.DCM.data_element(attrib_str).value
    except:  # noqa - what error is returned if the above fails?
        value = failure_value
    return value
