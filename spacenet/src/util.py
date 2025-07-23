# Licensed to the Apache Software Foundation (ASF) under one or more contributor license agreements; and to You under the Apache License, Version 2.0.

import math
import time
from datetime import datetime, timezone

km2au = 1.0/149597870.700
km2gm = 1e-6
km2m = 1e3
hrs2sec = 3600
day2sec = 24*hrs2sec
min2sec = 60

J2000="2000-01-01 12:00:00"


EARTH_RADIUS=6378.1
MOON_RADIUS=1737.4
SUN_RADIUS=696340


def getTimestamp(time_str):
    return time.mktime( datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timetuple())

J2000_ts=getTimestamp(J2000)

def getTimestampSinceJ2000Epoch(time_str):
    global J2000_ts
    return getTimestamp(time_str)-J2000_ts

def getTimestampUNIX(ts):
    global J2000_ts
    return J2000_ts+ts


def geoToCart(lon, lat, radius):
    radLon = math.radians(lon)
    radLat = math.radians(lat)
    return (
        radius * math.cos(radLat) * math.cos(radLon),
        radius * math.cos(radLat) * math.sin(radLon),
        radius * math.sin(radLat)
    )

