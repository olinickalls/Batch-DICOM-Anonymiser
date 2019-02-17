'''
StudyTools.py

Functions for use with Study anonymiser/Study ID generator

'''

import random


alphalistboth = ['a','b','c','d','e','f','g','h','i','j','k','l','m','o','n','p','q','r',
                 's','t','u','v','w','x','y','z','A','B','C','D','E','F','G','H','I','J',
                 'K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
alphalistupper = ['A','B','C','D','E','F','G','H','I','J',
                  'K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
alphalistlower = ['a','b','c','d','e','f','g','h','i','j','k','l','m','o','n','p','q','r',
                  's','t','u','v','w','x','y','z' ]

digitlist = [ '0','1','2','3','4','5','6','7','8','9' ]


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

