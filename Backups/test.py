import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import quandl
import math

mydata = quandl.get("FRED/DCOILWTICO")

print(mydata.tail())


