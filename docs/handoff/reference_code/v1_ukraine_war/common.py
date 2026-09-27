import math
import numpy as np

LON0, LON1, LAT0, LAT1 = 18.0, 46.0, 39.5, 57.5
W_OUT, H_OUT = 854, 480
FPS = 24
LEVELS = [200, 100, 50]          # pixels per degree of longitude


def ym(lat):
    return np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)))


YM_TOP = float(ym(LAT1))
YM_BOT = float(ym(LAT0))


def size_at(ppd):
    return int(math.ceil((LON1 - LON0) * ppd)), int(math.ceil((YM_TOP - YM_BOT) * ppd))


def proj(lon, lat, ppd=1.0):
    """geo -> pixel coords at given ppd (arrays ok)"""
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    return (lon - LON0) * ppd, (YM_TOP - ym(lat)) * ppd


def hexrgb(h, a=None):
    h = h.lstrip('#')
    c = tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return c if a is None else c + (a,)
