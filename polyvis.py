
import pandas as pd
import numpy as np
import os
import json
from . import app
from flask import request, session, jsonify, abort, redirect
import datetime

import requests

from HydraLib import config

import code.dataset_utilities as datasetutils

from werkzeug.exceptions import InternalServerError

global POLYVIS_URL
POLYVIS_URL = config.get('polyvis', 'POLYVIS_URL', 'http://polyvis.org/')

@app.route('/export_to_polyvis', methods=['GET'])
def do_export_to_polyvis():
    """
        Pass a multi-soluviton value (produced by MGA for example) into polyvis, first
        re-formatting it into a csv structure.
        Return a URL generated by polyvis and redirect to that URL
    """
    dataset_id = int(request.args['dataset_id'])
    user_id = session['user_id']

    app.logger.info('Exporting %s to polyvis', dataset_id)
    dataset = datasetutils.get_dataset(dataset_id, user_id)
    
    value = dataset.value

    json_val = json.loads(value)
    

    data = {}
    for k, v in json_val.items():
        soln_df = pd.read_json(json.dumps(v))
        avg_df = soln_df.mean(axis=1)
        #Try to int-ify the solution identifier as it'll provide a more nicely sorted csv file.
        try:
            k = int(k)
        except:
            pass
        data[int(k)] = avg_df.to_dict()
    
    avg_df = pd.read_json(json.dumps(data)).transpose()

    csv_text = avg_df.to_csv()

    f = open('/tmp/df.txt', 'w+')
    f.writelines(csv_text)
    f.flush()

    f = open('/tmp/df.txt', 'r')

    client = requests.session()

    # Retrieve the CSRF token first
    client.get(POLYVIS_URL)  # sets cookie
    csrftoken = client.cookies['csrftoken']

    resp = client.post(POLYVIS_URL+'upload_parallel_data',
                       files={'csv':f},
                       data={'csrfmiddlewaretoken':csrftoken},
                       headers=dict(Referer=POLYVIS_URL))
    

    return redirect(resp.url)