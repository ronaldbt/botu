import numpy as np
import time

def calc_slope(series):
    x = np.arange(len(series))
    y = series.values
    slope = np.polyfit(x, y, 1)[0]
    return slope

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
