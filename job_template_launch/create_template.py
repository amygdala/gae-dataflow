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

from apache_beam.options.pipeline_options import PipelineOptions

import dfpipe.pipe as pipe


PROJECT = os.environ['PROJECT']
BUCKET = os.environ['BUCKET']
DATASET = os.environ['DATASET']

pipeline_options = {
    'project': PROJECT,
    'staging_location': 'gs://' + BUCKET + '/staging',
    'runner': 'DataflowRunner',
    'setup_file': './setup.py',
    'job_name': PROJECT + '-twcount',
    'temp_location': 'gs://' + BUCKET + '/temp',
    'template_location': 'gs://' + BUCKET + '/templates/' + PROJECT + '-twproc_tmpl'
}
# define and launch the pipeline (non-blocking), which will create the template.
pipeline_options = PipelineOptions.from_dictionary(pipeline_options)
pipe.process_datastore_tweets(PROJECT, DATASET, pipeline_options)
