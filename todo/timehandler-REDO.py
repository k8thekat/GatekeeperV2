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
#Gatekeeper Bot - timehandler
from datetime import datetime,timedelta
import logging
#delta = timedelta(days=50, seconds=27, microseconds=10, milliseconds=29000, minutes=5, hours=8, weeks=2)

def parse(parameter,delta = False):
    logging.info('Converting the time...')
    print(parameter)

    if parameter == 'None' or parameter == None:
        return None

    curtime = datetime.now()
    time_found = False
    years,months,weeks,days,hours,minutes = 0,0,0,0,0,0
    if type(parameter) == tuple:
        parameter = list(parameter)

    if type(parameter) == list:
        parameter = " ".join(parameter)
        parameter = parameter.lower()

    parameter = parameter.lower()
    parameter = parameter.replace('y:','years:')
    parameter = parameter.replace('mo:','months:')
    parameter = parameter.replace('w:','weeks:')
    parameter = parameter.replace('d:','days:')
    parameter = parameter.replace('h:','hours:')
    parameter = parameter.replace('m:','minutes:')
    #parameter = parameter.replace('s:','seconds:')
    #print(parameter,type(parameter))
    year_find = parameter.find('years:')
    month_find = parameter.find('months:')
    week_find = parameter.find('weeks:')
    day_find = parameter.find('days:')
    hour_find = parameter.find('hours:')
    mins_find = parameter.find('minutes:')
    #sec_find = parameter.find('seconds:')
    reason_id = parameter.find('reason:')

    if reason_id != -1:
        if reason_id < day_find:
            logging.warning('Found reason before datetime objects')
            day_find = -1
            return True
        if reason_id < hour_find:
            logging.warning('Found reason before datetime objects')
            hour_find = -1
            return True

    #If we find a year; strip the value and return it.
    if year_find != -1:
        time_found = True
        yearnum = ''
        for letter in parameter[year_find+6:]:
            if letter.isnumeric():
                yearnum += letter
            else:
                break
        years = int(yearnum)

    #If we find a month; strip the value and return it.
    if month_find != -1:
        time_found = True
        monthnum = ''
        for letter in parameter[month_find+7:]:
            if letter.isnumeric():
                monthnum += letter
            else:
                break
        months = int(monthnum)

    #If we find a week; strip the value and return it.
    if week_find != -1:
        time_found = True
        weeknum = ''
        for letter in parameter[week_find+6:]:
            if letter.isnumeric():
                weeknum += letter
            else:
                break
        weeks = int(weeknum)

    #If we find a day; strip the value and return it.
    if day_find != -1:
        time_found = True
        daynum = ''
        for letter in parameter[day_find+5:]:
            if letter.isnumeric():
                daynum += letter
            else:
                break
        days = int(daynum)
        
    
    #If we find an hour; strip the value and return it.
    if hour_find != -1:
        time_found = True
        hournum = ''
        for letter in parameter[hour_find+6:]:
            if letter.isnumeric():
                hournum += letter
            else:
                break
        hours = int(hournum)

    #If we find minutes;strip the value and return it.
    if mins_find != -1:
        time_found = True
        minsnum = ''
        for letter in parameter[mins_find+8:]:
            if letter.isnumeric():
                minsnum += letter
            else:
                break
        minutes = int(minsnum)
    
    if time_found == False:
        logging.warning('Did not find a time value')
        return False
    # If we need a timedelta object.
    if delta == True:
        return timedelta(days= ((years*365) + (months*30) + (weeks*7) + days), hours=hours, minutes=minutes)
    bantime = curtime + timedelta(days= ((years*365) + (months*30) + (weeks*7) + days), hours=hours, minutes=minutes)
    return bantime


def conversionv2(parameter,flip = None):
    message = ''
    time_var = ['years','months','days','hours','minutes']
    #print(dir(parameter))
    for var in time_var:
        attr_check = hasattr(parameter, var)
        #print(attr_check,var)
        if attr_check:
            attr = getattr(parameter, var)
            if flip:
                message += f'{attr} {var.capitalize()}'
                continue
            else:
                message += f'{var.capitalize()}: {attr}'
                continue
    return message

def conversion(parameter,flip = None):
    message = ''
    var = 'days'
    attr_check = hasattr(parameter, var)
    #print(attr_check,var)
    #print(dir(parameter))
    if attr_check:
        attr = getattr(parameter, var)
        #print(attr)
        if attr == 0:
            min_conv = int(parameter.seconds/60)
            if flip:
                message += f'{min_conv} Minutes'
            else:
                message += f'Minutes: {min_conv}'
            return message
        if flip:
            message += f'{attr} {var.capitalize()}'
        else:
            message += f'{var.capitalize()}: {attr}'
    return message