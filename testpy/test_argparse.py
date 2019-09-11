# test argparse file.
# Test how to accept multiple filename/folder inputs

import argparse
import os, sys

from inspect import currentframe, getframeinfo
from pathlib import Path

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
parser.add_argument('-d','--debug',
    action="store_true", 
    default=False,
    dest='flag_a'
    )
parser.add_argument('dicomfiles', 
	metavar='<Directories or dicom files>', 
	type=str, nargs='*',
	help='put filenames here for deidentification'
	)
args = parser.parse_args()

print(f'Args list: {args}\n')

print(f'Debug flag is: {args.flag_a}\n')

print(f'-x arg: {args.xlsxfilename}\n')
print(f'-x arg type: {type(args.xlsxfilename)}\n')

print(f'files args: {args.dicomfiles}')
print(f'files args type: {type(args.dicomfiles)}')
print(f'files args type: {type(args.dicomfiles[0])}')
print('-------------------------------------------------------------------')

filename = getframeinfo(currentframe()).filename
parent = Path(filename).resolve().parent
print(f'filename: {filename}')
print(f'parent: {parent}')

'''
filename = getframeinfo(currentframe()).filename
parent = Path(filename).resolve().parent

print( f'CWD: {os.getcwd()}')
print( f'.py file path: {parent}  {filename}')

os.chdir( parent )
'''
