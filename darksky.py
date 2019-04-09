# -*- coding: utf-8 -*-
"""
weather.py - sopel Weather Underground Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright 2012, Edward Powell, embolalia.net
Copyleft  2019, Kyle Wilson, kylewilson.info
Licensed under the Eiffel Forum License 2.

http://sopel.dftba.net
"""

from sopel import web
from sopel.module import commands, example, NOLIMIT

import urllib
import json
import sys

reload(sys)
sys.setdefaultencoding('utf8')

darkskyapikey = ''
opencageapikey = ''

def degrees_to_cardinal(d):
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = int((d + 11.25)/22.5)
    return dirs[ix % 16]

def geolookup(query):
    """
    Use open cage data to provide latitude & longitude coordinates for a given query
    """
    url = 'https://api.opencagedata.com/geocode/v1/json?q=' + query + '&key=' + opencageapikey
    wresult = urllib.urlopen(url)
    root = json.loads(wresult.read())
    try:
        lng = root["results"][0]["geometry"]["lng"]
        lat = root["results"][0]["geometry"]["lat"]
    except:
        return None
    return str(lat)+','+str(lng)

@commands('weather', 'wea')
@example('.weather London')
def weather(bot, trigger):
    """.weather location - Show the weather at the given location."""

    location = trigger.group(2)
    if not location:
        first_result = bot.db.get_nick_value(trigger.nick, 'latlng')
        if not first_result:
            return bot.msg(trigger.sender, "I don't know where you live. " +
                           'Give me a location, like .weather London, or tell me where you live by saying .setlocation London, for example.')
    else:
        location = location.strip()
        first_result = bot.db.get_nick_value(location, 'latlng')
        if first_result is None:
            first_result = geolookup(location)
            if first_result is None:
                return bot.reply("I don't know where that is.")
    url = 'https://api.darksky.net/forecast/' + darkskyapikey + '/' + first_result
    wresult = urllib.urlopen(url)
    root = json.loads(wresult.read())
    current = root["currently"]
    cover = current["summary"]
    temp = current["temperature"]
    temp = str(round(temp,1)) + '°F (' + str(round((temp-32)*5/9,1)) + '°C)'
    humidity = str(int(round(current["humidity"] * 100))) + '%'
    pressure = str(int(round(current["pressure"]))) + 'mb'
    bearing = int(current["windBearing"])
    bearing = degrees_to_cardinal(bearing)
    wind = 'Wind ' + str(int(round(current["windSpeed"]))) + 'mph, gusting to ' + str(int(round(current["windGust"]))) + 'mph ' + bearing
    url = 'https://api.opencagedata.com/geocode/v1/json?q=' + first_result + '&key=' + opencageapikey
    wresult = urllib.urlopen(url)
    root = json.loads(wresult.read())
    location = root["results"][0]["components"]
    city = None
    state = None
    try:
        city = location["city"]
    except:
        try:
            city = location["town"]
        except:
            try:
                city = location["village"]
            except:
                try:
                    city = location["hamlet"]
                except:
                    try:
                        city = location["county"]
                    except:
                        pass

    try:
        state = location["state_code"]
    except:
        try:
            state = location["state"]
        except:
            try:
                state = location["country"]
            except:
                pass

    if city is None or state is None:
        location = first_result
    else:
        location = city + ', ' + state
    bot.say(u'%s: %s, %s, %s humidity, %s, %s' % (location, cover, temp, humidity, pressure, wind))


@commands('setlocation', 'setloc')
@example('.setlocation Columbus, OH')
def setlocation(bot, trigger):
    """Set your default weather location."""
    first_result = geolookup(trigger.group(2))
    if first_result is None:
        return bot.reply("I don't know where that is.")

    location = first_result

    bot.db.set_nick_value(trigger.nick, 'latlng', location)

    bot.reply('I now have you at %s.' %(location))

