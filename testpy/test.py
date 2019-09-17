# test argparse file.
# Test how to accept multiple filename/folder inputs

import argparse
import os, sys

from inspect import currentframe, getframeinfo
from pathlib import Path

from test_helper import *


parser = argparse.ArgumentParser(
		description='Deidentify DICOM files using a .xlsx Template file.'
		)
parser.add_argument('-x', 
	metavar='<Study Template filename>', 
	type=str, 
	dest='xlsxfilename',
	default='default.xlsx',
	help='Study Template .xlsx filename'
	)

#parser.add_argument('dicomfiles', 
#	metavar='<Directories or dicom files>', 
#	type=str, nargs='*',
#	help='put filenames here for deidentification'
#	)

parser.add_argument('-d','--debug',
	action="store_true", 
	default=False,
	dest='debug'
	)
#parser.add_argument('-v','--verbose',
#    action="store_true", 
#    default=False,
#	metavar='<increase verbosity>', 
#	dest='verbose',
#	help='Prints more info about activity'
#	)
parser.add_argument('dicomfiles',  # positional arg -no '-' required
	metavar='<Directories or dicom files>', 
	type=str, nargs='*',  # No limit to number of args expected
	help='<filenames> and <dirnames> for deidentification'
	)
args = parser.parse_args()



print(f'Args list: {args}\n')

print(f'Debug flag is: {args.debug}\n')

print(f'-x arg: {args.xlsxfilename}\n')
print(f'-x arg type: {type(args.xlsxfilename)}\n')

print(f'files args: {args.dicomfiles}')
print(f'files args type: {type(args.dicomfiles)}')
print('-------------------------------------------------------------------')

filename = getframeinfo(currentframe()).filename
parent = Path(filename).resolve().parent
print(f'filename: {filename}')
print(f'parent: {parent}\n\n\n')

basevar = 'something'
print(f'Executing functioncall. Returns:{functioncall("some text")}')
'''

#############################################################
def functioncall( variable ):
	print(f'in functioncall - variable: {variable}')
	print(f'basevar ={basevar}')
	return True

#############################################################

'''