# dcmtools.py
'''Just some tools that I use sporadically
Mainly for troubleshooting anonymised datasets

Needs PEP 8 compliance work
'''

import pydicom
from study_modules import *


def dcm_qload(filename, path=""):
    ds = pydicom.filereader.dcmread(path + filename, force=True)
    return ds


def save(dcm_object, filename, path=""):
    dcm_object.save_as(path + filename, write_like_original=True)
    print(f'Saved as {path+filename}')
    return


def alter(filename, PatientID="", AccessionNumber="", StudyDate=""):
    ds = pydicom.filereader.dcmread(filename, force=True)
    if PatientID != "":
        ds.PatientID = PatientID
        print(f'Changed PatientID to {PatientID}')
    if AccessionNumber != "":
        ds.AccessionNumber = AccessionNumber
        print(f'Changed AccessionNumber to {AccessionNumber}')
    if StudyDate != "":
        ds.StudyDate = StudyDate
        print(f'Changed StudyDate to {StudyDate}')
    ds.save_as(filename, write_like_original=True)


def setptID(filename, newID):
    fname = 'sample_2\\' + filename
    ds = pydicom.filereader.dcmread(fname, force=True)
    ds.PatientID = newID
    ds.save_as(fname, write_like_original=True)
    # print(f'changed patient ID in {fname} to {newID}.')


def settag(filename, tag, new_value):
    fname = 'sample_2\\' + filename
    ds = pydicom.filereader.dcmread(fname, force=True)
    ds.data_element(tag).value = new_value
    ds.save_as(fname, write_like_original=True)
    # print(f'changed patient ID in {fname} to {newID}.')


def set_AccessionNumber(filename, new_value):
    fname = 'sample_2\\' + filename
    ds = pydicom.filereader.dcmread(fname, force=True)
    ds.AccessionNumber = new_value
    ds.save_as(fname, write_like_original=True)
    # print(f'changed patient ID in {fname} to {newID}.')


def set_StudyDate(filename, new_value):
    fname = 'sample_2\\' + filename
    ds = pydicom.filereader.dcmread(fname, force=True)
    ds.StudyDate = new_value
    ds.save_as(fname, write_like_original=True)
    # print(f'changed patient ID in {fname} to {newID}.')
