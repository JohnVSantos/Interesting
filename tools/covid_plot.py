#from sqlalchemy import create_engine
import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.ticker import FormatStrFormatter
import seaborn as sns

# Read measurements from database, sqlalchemy URI
#Database is expected to have:
# - one table 'alberta' with:
#   - one column 'date' (an iso formated date string)
#   - one column 'daily_cases' (an int)

# using an sqlite connection, sql query and pandas to read the data
DATABASE = "../data/measurements.db"

conn = sqlite3.connect(DATABASE)
query = "select * from alberta"
df = pd.read_sql_query(query, con=conn, parse_dates=['date'])
conn.close()



#Make sure dates are sorted
df = df.sort_values(by=['date'])

#Compute total and smoothed daily cases
df['total_cases'] = df.daily_cases.cumsum()
df['smooth_daily_cases'] = df.daily_cases.rolling(7, min_periods=1).mean()

#Checking what we have
df.info()
print(df.head())

#Figure1: Seaborn plots for daily cases
fig, ax = plt.subplots()
sns.lineplot(x='date', y='smooth_daily_cases', data=df, ax=ax)
ax.grid(True)
# re-adjusting layout after rotating labels
ax.tick_params(axis="x", which="both", rotation=45)
fig.tight_layout()

#Figure2: Seaborn plots for total cases
fig, ax = plt.subplots()
sns.lineplot(x='date', y='total_cases', data=df, ax=ax)

ax.grid(b=True)
# re-adjusting layout after rotating labels
ax.tick_params(axis="x", which="both", rotation=45)
fig.tight_layout()

#Figure3: Matplotlib log-log plot of:
# - total_cases (x-axis) and 
# - smoothed daily_cases (y-axis)
# as used in: https://www.youtube.com/watch?v=54XLXg4fYsc
fig, ax = plt.subplots()
x_str='total_cases'
y_str='smooth_daily_cases'
# using log-log and two minor ticks per decade
ax.loglog(df[x_str], df[y_str], subs=[2, 5])
# Add a 'dot' to indicate last measurement
ax.plot(df[x_str].iloc[-1], df[y_str].iloc[-1], 'ko')
print(df[x_str])
ax.set_xlabel(x_str)
ax.set_ylabel(y_str)
# grid on both major and minor ticks
ax.grid(which='both')
# major and minor tick labels as regular numbers
ax.xaxis.set_major_formatter(FormatStrFormatter("%.0f"))
ax.xaxis.set_minor_formatter(FormatStrFormatter("%.0f"))
ax.yaxis.set_major_formatter(FormatStrFormatter("%.0f"))
ax.yaxis.set_minor_formatter(FormatStrFormatter("%.0f"))

# re-adjusting layout after rotating labels
ax.tick_params(axis="x", which="both", rotation=45)
fig.tight_layout()

# show all figures
plt.show()