from typing import Optional
from pglib.datetime import TZInfoRep, as_tzinfo
from .parser import register
import datetime


@register("now")
def now(tz: Optional[TZInfoRep] = None):
    tz = None if tz is None else as_tzinfo(tz)
    return datetime.datetime.now(tz)


@register("today")
def today(tz: Optional[TZInfoRep] = None):
    return now(tz).date()


@register("time")
def time(tz: Optional[TZInfoRep] = None):
    return now(tz).time()
