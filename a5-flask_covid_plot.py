#Author: John Santos
import requests
import sqlite3
from flask import Flask, render_template, request
from flask import g # Keeping state: contains database connection
import pandas as pd
from datetime import datetime

# Used for plotting to memory and converting to ascii stream
import base64
from io import BytesIO

from matplotlib.figure import Figure
from matplotlib.ticker import FormatStrFormatter
import seaborn as sns

app = Flask(__name__)

#DATABASE = "data/measurements.db"

# From: https://flask.palletsprojects.com/en/1.1.x/patterns/sqlite3/
# def get_db():
#     """Gets the database.

#     Returns: db (binary format)
#     """
#     db = getattr(g, '_database', None)
#     if db is None:
#         db = g._database = sqlite3.connect(DATABASE)
#     return db
    
def get_df_from_db(start_date=None, end_date=None, province=None): # Read from downloaded csv: def gret_df_from_db(start_date=None, end_date=None):
    """Reads from the database.

    Returns: df
    """
    # # without a date range, we select all data
    # if start_date is None and end_date is None:
    #     query = "select * from alberta"
    # else: # checking if date range is valid, construct sql query with between
    #     try:
    #         start_date = datetime.strptime(start_date, '%Y-%m-%d' )
    #     except:
    #         # default start date is prior to pandemic
    #         start_date = '2020-01-01'
    #     try:
    #         end_date = datetime.strptime(end_date, '%Y-%m-%d' )
    #     except:
    #         # default end date is today
    #         end_date = datetime.today().strftime('%Y-%m-%d' )
    #     query = f"select * from alberta where date between '{start_date}' and '{end_date}'"
        
    # df = pd.read_sql_query(query, con=get_db(), parse_dates=['date'])
    # df['total_cases'] = df['daily_cases'].cumsum()
    # # min_periods=1 avoids NaN at the start
    # df['smooth_daily_cases'] = df['daily_cases'].rolling(7, min_periods=1).mean()

    ####

    print(start_date)
    print(end_date)

    if province is None and start_date is None and end_date is None:
        province = 'AB'
        start_date = '2020-01-25'
        end_date = datetime.today().strftime('%Y-%m-%d' )

    else: 
        pass
        # try:
        #     start_date = datetime.strptime(start_date, '%Y-%m-%d' )
        # except:
        #     # default start date is prior to pandemic
        #     start_date = '2020-01-25'
        # try:
        #     end_date = datetime.strptime(end_date, '%Y-%m-%d' )
        # except:
        #     # default end date is today
        #     end_date = datetime.today().strftime('%Y-%m-%d' )


    response = requests.get('https://api.opencovid.ca/timeseries',
                            params={'stat':'cases', 'loc':province,
                            'after':start_date, 'before':end_date,
                            'ymd':'true'})

    cases_list = response.json()['cases']
    df = pd.DataFrame(cases_list)
    df.rename(columns={'date_report': 'date', 'cases':'daily_cases'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')


    #Make sure dates are sorted
    df = df.sort_values(by=['date'])

    #Compute total and smoothed daily cases
    df['total_cases'] = df.daily_cases.cumsum()
    df['smooth_daily_cases'] = df.daily_cases.rolling(7, min_periods=1).mean()

    #Checking what we have
    # df.info()
    # print(df.head(20))

    # import IPython; IPython.embed(); exit();

    return df

#From: https://matplotlib.org/devdocs/gallery/user_interfaces/web_application_server_sgskip.html
def get_image_from_fig(fig):
    """Converts a plot, fig into an image.

    fig (object): A plot with axis

    Returns: A .png image
    """
    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"<img src='data:image/png;base64,{data}'/>"

# From: https://flask.palletsprojects.com/en/1.1.x/patterns/sqlite3/
@app.teardown_appcontext
def close_connection(exception):
    """Closes the connection between the database and sqlite.

    """
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    """Renders the index.html template with the specified route above.

    Return: template of the index that is displayed on the webserver.
    """
    return render_template('index.html')

@app.route('/Daily')
def daily():
    """Gets the range of dates and reads the database and plots the figure with the daily covid cases versus the date.

    Returns: template of plot.html that is displayed on the webserver.
    """

    # Gets the dates inputted by the user from the webserver which is saved as a query string in the URL.
    date_min = request.args.get('datemin') 
    date_max = request.args.get('datemax')
    province = request.args.get('province')

    #An alternative is to use request.values.get()

    df = get_df_from_db(date_min, date_max, province)

    fig = Figure()
    ax = fig.subplots()

    sns.lineplot(x='date', y='smooth_daily_cases', data=df, ax=ax)
    ax.tick_params(axis="x", which="both", rotation=45)
    ax.grid(b=True)

    fig.tight_layout()

    return render_template('plot.html', 
                            title="Daily", 
                            image_tag=get_image_from_fig(fig), the_date_min=date_min, the_date_max=date_max, the_province=province, df_html=df.to_html())
    
@app.route('/Total')
def total():
    """Gets the range of dates and reads the database and plots the figure with the total covid cases versus the date.

    Returns: template of plot.html that is displayed on the webserver.
    """

    date_min = request.args.get('datemin') 
    date_max = request.args.get('datemax') 
    province = request.args.get('province')

    df = get_df_from_db(date_min, date_max, province)

    fig = Figure()
    ax = fig.subplots()

    sns.lineplot(x='date', y='total_cases', data=df, ax=ax)
    # re-adjusting layout after rotating labels
    ax.tick_params(axis="x", which="both", rotation=45)
    ax.grid(b=True)
   
    fig.tight_layout()

    return render_template('plot.html', 
                            title="Total", 
                            image_tag=get_image_from_fig(fig), the_date_min=date_min, the_date_max=date_max, the_province=province, df_html=df.to_html())

@app.route('/loglog')
def loglog():
    """Gets the range of dates and reads the database and plots the figure with the daily covid cases versus the total covid cases.

    Returns: template of plot.html that is displayed on the webserver.
    """
    # - total_cases (x-axis) and 
    # - smoothed daily_cases (y-axis)
    # as used in: https://www.youtube.com/watch?v=54XLXg4fYsc

    date_min = request.args.get('datemin') 
    date_max = request.args.get('datemax') 
    province = request.args.get('province')

    df = get_df_from_db(date_min, date_max, province)

    fig = Figure()
    ax = fig.subplots()

    x_str='total_cases'
    y_str='smooth_daily_cases'

    # using log-log and two minor ticks per decade
    ax.loglog(df[x_str], df[y_str], subs=[2, 5])

    # Add a 'dot' to indicate last measurement
    ax.plot(df[x_str].iloc[-1], df[y_str].iloc[-1], 'ko')

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

    return render_template('plot.html', 
                            title="Log-Log", 
                            image_tag=get_image_from_fig(fig), the_date_min=date_min, the_date_max=date_max, the_province=province, df_html=df.to_html()) 
    #df.to_html converts df into a table

#This is an optional code to minimize the code above and have this function initialized only. However, it does not tackle the log log function
"""
@app.route('/<plot_type>')
def the_date(plot_type):
        df = get_df_from_db() #Start_date, End_Date Pass

        date_min = request.args.get('datemin') 
        date_max = request.args.get('datemax') 

        data = None

        if plot_type == 'Daily':
            data = 'smooth_daily_cases'

        elif plot_type == 'Total':
            data = 'total_cases'

        else:
            pass

        fig = Figure()
        ax = fig.subplots()

        sns.lineplot(x='date', y=data, data=df, ax=ax)
        # re-adjusting layout after rotating labels
        ax.tick_params(axis="x", which="both", rotation=45)
        ax.grid(b=True)
    
        fig.tight_layout()

        return render_template('test.html', 
                                title=plot_type, 
                                image_tag=get_image_from_fig(fig), the_date_min=date_min, the_date_max=date_max)

"""
        
if __name__ == '__main__':
    app.debug = True
    app.run()