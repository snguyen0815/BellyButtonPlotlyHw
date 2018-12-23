########################
# User: Stanley Nguyen
########################
from flask import Flask, jsonify, render_template, request, flash, redirect


import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, desc,select

import pandas as pd
import numpy as np


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///DataSets/belly_button_biodiversity.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)


OTU = Base.classes.otu
Samples = Base.classes.samples
Samples_Metadata= Base.classes.samples_metadata

# Create our session (link) from Python to the DB
session = Session(engine)

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")


@app.route('/names')
def names():
    """Return a list of sample names."""

    # Use Pandas to perform the sql query
    stmt = session.query(Samples).statement
    df = pd.read_sql_query(stmt, session.bind)
    df.set_index('otu_id', inplace=True)

    # Return a list of the column names (sample names)
    return jsonify(list(df.columns))

@app.route('/otu')
def otu():
    """Return a list of OTU descriptions."""
    results = session.query(OTU.lowest_taxonomic_unit_found).all()

    otu_list = list(np.ravel(results))
    return jsonify(otu_list)


@app.route('/metadata/<sample>')
def sample_metadata(sample):
    """Return the MetaData for a given sample."""
    sel = [Samples_Metadata.SAMPLEID, Samples_Metadata.ETHNICITY,
           Samples_Metadata.GENDER, Samples_Metadata.AGE,
           Samples_Metadata.LOCATION, Samples_Metadata.BBTYPE]

    results = session.query(*sel).\
        filter(Samples_Metadata.SAMPLEID == sample[3:]).all()

    # Create a dictionary entry for each row of metadata information
    sample_metadata = {}
    for result in results:
        sample_metadata['SAMPLEID'] = result[0]
        sample_metadata['ETHNICITY'] = result[1]
        sample_metadata['GENDER'] = result[2]
        sample_metadata['AGE'] = result[3]
        sample_metadata['LOCATION'] = result[4]
        sample_metadata['BBTYPE'] = result[5]

    return jsonify(sample_metadata)

@app.route('/wfreq/<sample>')
def sample_wfreq(sample):
    """Return the Weekly Washing Frequency as a number."""

    results = session.query(Samples_Metadata.WFREQ).\
    filter(Samples_Metadata.SAMPLEID == sample[3:]).all()
    wfreq = np.ravel(results)

    return jsonify(int(wfreq[0]))

@app.route('/samples/<sample>')
def samples(sample):
    """Return a list dictionaries containing `otu_ids` and `sample_values`."""
    stmt = session.query(Samples).statement
    df = pd.read_sql_query(stmt, session.bind)

    if sample not in df.columns:
        return jsonify(f"Error! Sample: {sample} Not Found!"), 400

    df = df[df[sample] > 1]

    df = df.sort_values(by=sample, ascending=0)

    # Format the data to send as json
    data = [{
        "otu_ids": df[sample].index.values.tolist(),
        "sample_values": df[sample].values.tolist()
    }]
    return jsonify(data)
if __name__ == "__main__":
    app.run(debug=True)
   
    