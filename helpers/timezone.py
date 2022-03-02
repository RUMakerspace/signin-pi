# https://stackoverflow.com/questions/4770297/convert-utc-datetime-string-to-local-datetime

from datetime import datetime, timedelta
from dateutil import tz

est = tz.gettz("America/New_York")


def convertTZ(utc):
    from_zone = tz.gettz("UTC")
    to_zone = est

    # Tell the datetime object that it's in UTC time zone since
    # datetime objects are 'naive' by default
    utc = utc.replace(tzinfo=from_zone)
    return utc.astimezone(to_zone)


def todayInEST():
    midnight = (
        datetime.now(tz.tzutc())
        .astimezone(est)
        .replace(hour=0, minute=0, second=0, microsecond=0)
    )
    return midnight
