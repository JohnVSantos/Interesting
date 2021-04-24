import pandas as pd
from sqlalchemy import create_engine

# Data is from https://covid19stats.alberta.ca
csv_file = '../data/covid19dataexport.csv'

# Using SQLAlchemy and pandas to write the sqlite database
sqlite_file = 'sqlite:///../data/measurements.db'

# CSV contains one line for every covid case
df = pd.read_csv(csv_file)
# Need date to be of type datetime
df['Date reported'] = pd.to_datetime(df['Date reported'])
# Data has one entry per case, we want daily counts
s = df['Date reported'].value_counts()
# s is a Series, dates are now the index, values are daily counts
s = s.sort_index()

# drop last day, usually not accurate
s = s.iloc[:-1]

# create the desired dataframe from the series.
df = pd.DataFrame({'date': s.index, 'daily_cases': s.values})

# Write to Sqlite with Pandas and SQLAlchemy
engine = create_engine(sqlite_file, echo=False)
df.to_sql('alberta', con=engine, if_exists='replace') 
engine.dispose()
