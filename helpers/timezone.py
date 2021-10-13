# https://stackoverflow.com/questions/4770297/convert-utc-datetime-string-to-local-datetime

from datetime import datetime
from dateutil import tz


def convertTZ(utc):
    from_zone = tz.gettz("UTC")
    to_zone = tz.gettz("America/New_York")

    # Tell the datetime object that it's in UTC time zone since
    # datetime objects are 'naive' by default
    utc = utc.replace(tzinfo=from_zone)
    return utc.astimezone(to_zone)
