'''
   Copyright (C) 2021-2022 Katelynn Cadwallader.

   This file is part of Gatekeeper, the AMP Minecraft Discord Bot.

   Gatekeeper is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 3, or (at your option)
   any later version.

   Gatekeeper is distributed in the hope that it will be useful, but WITHOUT
   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
   or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
   License for more details.

   You should have received a copy of the GNU General Public License
   along with Gatekeeper; see the file COPYING.  If not, write to the Free
   Software Foundation, 51 Franklin Street - Fifth Floor, Boston, MA
   02110-1301, USA. 
'''
def ParseIGNServer(msg:str):
	print(msg)
	message_commafilter = msg.find(',')
	message_semicolonfilter = msg.find(';')
	if message_commafilter != -1:
		msg = msg.replace(',',' ')
	
	if message_semicolonfilter != -1:
		msg = msg.replace(';',':')

	ret = ['', ''] #0,1

	#split on tab, newline, and space
	msg = msg.split()

	#try to find matches
	fieldflag = -1
	pos = 0
	while pos < len(msg):
		curentry = msg[pos].lower()
		print('curentry',curentry)
		if curentry.startswith("server") and (fieldflag == 1):
			ret[fieldflag] += f' {msg[pos]}'
		elif curentry.startswith("ign") or curentry.startswith("server") or curentry.startswith("in-game-name") or curentry.startswith('in-gamename') or curentry.startswith('ingamename'):
    			#flag what we are looking at, ign or server
			if curentry.startswith("ign") or curentry.startswith("in-game-name") or curentry.startswith('in-gamename') or curentry.startswith('ingamename'):
				fieldflag = 0
			else:
				fieldflag = 1

			#if a : exists in this entry then see if the name/server is after it
			if ":" in curentry:
				#split on colon and see if we have anything after it, use msg[pos] so we don't have
				#the lower version of a name or server
				colonsplit = msg[pos].split(":")

				#if something is after the colon then get it as they did name:val
				if len(colonsplit) != 2:
					#we got more than 2 entries, too many colons, fail
					return None

				#see if anything exists after the colon
				if len(colonsplit[1]):
					ret[fieldflag] = colonsplit[1]
				else:
					#nothing after the colon, see if we have another entry after us
					#in the list as it should be the value we want
					#but if no more entries exist then fail the parse
					if pos+1 >= len(msg):
						return None

					#get the next entry and skip past it in the for loop
					ret[fieldflag] = msg[pos+1]
					pos = pos + 1
			else:
				#colon should be next entry, make sure we have an entry to parse
				if pos+1 >= len(msg):
					return None

				#if the message is a colon then we should have another field after it			
				if msg[pos+1] == ":":
					#see if another field exists allowing for name : value
					#fail if no more entries exist, example inputting name :
					if pos+2 >= len(msg):
						return None

					#found colon by itself, entry after should be the value we want
					#adjust pos so we skip past it in our search
					ret[fieldflag] = msg[pos + 2]
					pos = pos + 2
				elif msg[pos+1][0] == ":":
					#starts with a :, rest should be the entry we want, double check no extra : exists in it
					if ":" in msg[pos+1][1:]:
						return None

					#no extra :, get everything after the colon
					ret[fieldflag] = msg[pos+1][1:]
				else:
					#could not find the :
					return None
		else:
			if fieldflag == -1:
				return None
			ret[fieldflag] += f' {msg[pos]}'	
			
		#next entry
		pos = pos + 1

	#make sure both fields are filled in
	if len(ret[0]) == 0 or len(ret[1]) == 0:
		return None

	return (ret[0], ret[1])