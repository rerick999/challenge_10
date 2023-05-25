# Import the dependencies.
import numpy as np
import pandas as pd
import datetime as dt
#
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
#
from flask import Flask, jsonify
#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///resources/hawaii.sqlite",connect_args={'check_same_thread': False})
# reflect an existing database into a new model
Base=automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)
# # Save references to each table
Measurement=Base.classes.measurement
Station=Base.classes.station
# # Create our session (link) from Python to the DB
session=Session(engine)
#################################################
# Flask Setup
#################################################
app = Flask(__name__)
#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    """List all available api routes."""
    now=dt.datetime.now()
    apidesc='api/v1.0/'
    return (
        f"Time: {now}<br/>"
        f"Available Routes:<br/>"
        f"{apidesc}precipitation<br/>"
        f"{apidesc}stations<br/>"
        f"{apidesc}tobs<br/>"
        f"{apidesc}<start>  (use yyyymmmdd)<br/>"
        f"{apidesc}<start>/<end>  (use yyyymmmdd)<br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    first_date=session.query(Measurement).order_by(sqlalchemy.desc(Measurement.date)).first().date
    most_recent=session.query(Measurement).order_by(sqlalchemy.desc(Measurement.date)).first().date
    most_recent=dt.datetime.strptime(most_recent,'%Y-%m-%d').date()
    # Calculate the date one year from the last date in data set.
    one_year_ago=most_recent-dt.timedelta(days=1*365)
    # Perform a query to retrieve the data and precipitation scores
    data=session.query(Measurement).filter(Measurement.date>=one_year_ago)\
    .with_entities(Measurement.date,Measurement.prcp).all()
    datadf=pd.DataFrame(data,columns=['date','precipitation'])
    datadf=datadf.sort_values(by=['date'])
    datadf=datadf.dropna(how='any')
    vals=datadf.values.tolist()
    return jsonify(vals)

@app.route("/api/v1.0/stations")
def stations():
    alist=[]
    for class_instance in session.query(Measurement).all():
        adict=vars(class_instance)
        adict={k:v for k,v in adict.items() if not k.startswith('_')}
        alist+=[adict]
    alist=list(np.ravel(alist))
    return jsonify(alist)

@app.route("/api/v1.0/tobs")
def tobs():
    stations=session.query(Measurement.station,func.count(Measurement.station))\
    .group_by(Measurement.station)\
    .order_by(func.count(Measurement.station).desc())
    most_active_id=stations[0][0]
    ma_most_recent=session.query(Measurement)\
    .filter(Measurement.station==most_active_id)\
    .order_by(sqlalchemy.desc(Measurement.date)).first().date
    ma_most_recent=dt.datetime.strptime(ma_most_recent,'%Y-%m-%d').date()
    ma_one_year_ago=ma_most_recent-dt.timedelta(days=1*365)
    ma_dates_temps=session.query(Measurement)\
    .filter(Measurement.station==most_active_id)\
    .filter(Measurement.date>=ma_one_year_ago)\
    .with_entities(Measurement.date,Measurement.tobs)
    ma_dt_df=pd.DataFrame(ma_dates_temps)
    vals=ma_dt_df.values.tolist()
    return jsonify(vals)

@app.route("/api/v1.0/<start>")
def start(start):
    startdate=dt.datetime.strptime(start,'%Y%m%d').date()
    ma_dates_temps=session.query(Measurement)\
    .filter(Measurement.date>=startdate)\
    .with_entities(Measurement.tobs).all()
    ma_dt_df=pd.DataFrame(ma_dates_temps)
    if len(ma_dt_df)==0: return "No data!  Try an earlier date!"
    adict={'min':round(ma_dt_df.min()[0],2),
           'max':round(ma_dt_df.max()[0],2),
           'average':round(ma_dt_df.mean()[0],2)}
    alist=['%s: %s'%(x,y) for x,y in adict.items()]
    return jsonify(' '.join(alist))

@app.route("/api/v1.0/<start>/<end>")
def start_end(start,end):
    startdate=dt.datetime.strptime(start,'%Y%m%d').date()
    enddate=dt.datetime.strptime(end,'%Y%m%d').date()
    ma_dates_temps=session.query(Measurement)\
    .filter(Measurement.date>=startdate)\
    .filter(Measurement.date<=enddate)\
    .with_entities(Measurement.tobs)
    ma_dt_df=pd.DataFrame(ma_dates_temps)
    if len(ma_dt_df)==0: return "No data!  Try an earlier date!"
    adict={'min':round(ma_dt_df.min()[0],2),
           'max':round(ma_dt_df.max()[0],2),
           'average':round(ma_dt_df.mean()[0],2)}
    alist=['%s: %s'%(x,y) for x,y in adict.items()]
    return jsonify(' '.join(alist))

if __name__ == '__main__':
    app.run(debug=True)
