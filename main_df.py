# Copyright 2017 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The app for the 'backend' service, which handles cron job requests to
launch a Dataflow pipeline to analyze recent tweets stored in the Datastore.
"""

from __future__ import absolute_import

import logging
import os

from apache_beam.utils.pipeline_options import PipelineOptions

from flask import Flask
from flask import request

import dfpipe.pipe as pipe


logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

PROJECT = os.environ['PROJECT']
BUCKET = os.environ['BUCKET']
DATASET = os.environ['DATASET']


# Route the incoming app requests.

@app.route('/')
def hello():
  """A no-op."""
  return 'nothing to see.'


@app.route('/launchpipeline')
def launch():
  """Launch the Dataflow pipeline."""
  is_cron = request.headers.get('X-Appengine-Cron', False)
  logging.info("is_cron is %s", is_cron)
  # Comment out the following test to allow non cron-initiated requests.
  if not is_cron:
    return 'Blocked.'
  pipeline_options = {
      'project': PROJECT,
      'staging_location': 'gs://' + BUCKET + '/staging',
      'runner': 'DataflowRunner',
      'setup_file': './setup.py',
      'job_name': PROJECT + '-twcount',
      'max_num_workers': 10,
      'temp_location': 'gs://' + BUCKET + '/temp'
  }
  # define and launch the pipeline (non-blocking).
  pipe.process_datastore_tweets(PROJECT, DATASET,
                      PipelineOptions.from_dictionary(pipeline_options))

  return 'Done.'


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=True)
