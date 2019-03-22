'''
Modules part of the Batch Anonymiser

Oliver Nickalls, Jan 2019

using pyDICOM (originally version 1.2.1)

'''



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


#	These are fairly specific- taken from sample DICOM studies.

def deidentifyDICOM( DCOobj, newPtName = 'Anon', newPtID = 'research' ):

	print(f'deidentifyDICOM received newPtName={newPtName} \tnewPtID={newPtID} ')

	DCOobj.remove_private_tags()
	DCOobj.walk(tag_data_type_callback)
	DCOobj.walk(curves_callback)

    # (0008, ) tags

	DCOobj.AccessionNumber = ''  
	DCOobj.StudyID = ''           # Often contains the same data as AccessionNumber
	# DCOobj.StudyDescription = ''
	DCOobj.InstitutionalDepartmentName = 'St Elsewhere Radiology'
	DCOobj.InstitutionAddress = ''   # (0008, 0081) 

    # (0010, ) tags
	DCOobj.PatientID = newPtID   # (0008, 0020)
	DCOobj.PatientName = newPtName   # (0008, 0010)
	DCOobj.PatientBirthDate = ''   # (0008, 0030)
	DCOobj.InstitutionName = 'St Elsewhere'   # (0008, 0080)
	DCOobj.StationName = 'anon MRI Station'   # (0008, 1010)
	DCOobj.PerformedStationName	= 'anon MRI Station'   # (0008, 0242)
	DCOobj.PerformedLocation = 'anon MRI Station'	    # (0008, 0243)
	DCOobj.PerformedProcedureStepStartDate = ''	 
	DCOobj.PerformedProcedureStepStartTime = ''	 
	DCOobj.PerformedProcedureStepEndDate = 	''
	DCOobj.PerformedProcedureStepEndTime = ''
	DCOobj.PerformedProcedureStepID = ''
	DCOobj.PerformedProcedureStepDescription = ''
	DCOobj.ScheduledProcedureStepDescription = ''
	DCOobj.ScheduledProcedureStepID = ''
	DCOobj.RequestedProcedureID = ''
	DCOobj.DeviceSerialNumber = ''
	DCOobj.PlateID = ''
	DCOobj.DetectorDescription = ''
	DCOobj.DetectorID = ''

	if 'RequestAttributeSequence' in DCOobj:
		del DCOobj.RequestAttributesSequence


	#try:
	#	del DCOobj.RequestAttributesSequence
	#except Exception as e:
	#	pass



