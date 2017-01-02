# Copyright 2016 Google Inc. All rights reserved.
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
...
"""

from __future__ import absolute_import

import cgi
import cStringIO
import logging
import urllib

# from google.appengine.api import memcache
# from google.appengine.api import users
# from google.appengine.ext import ndb

import base64
import datetime
import logging
import os
import time

import argparse
import re
import uuid

from google.datastore.v1 import entity_pb2
from google.datastore.v1 import query_pb2
from googledatastore import helper as datastore_helper, PropertyFilter
from googledatastore import Timestamp

import apache_beam as beam
from apache_beam import combiners
from apache_beam.io.datastore.v1.datastoreio import ReadFromDatastore
from apache_beam.io.datastore.v1.datastoreio import WriteToDatastore
from apache_beam.utils.options import GoogleCloudOptions
from apache_beam.utils.options import PipelineOptions
from apache_beam.utils.options import SetupOptions

from flask import Flask

app = Flask(__name__)


class WordExtractingDoFn(beam.DoFn):
  """Parse each line of input text into words."""

  def process(self, context):
    """...
    """
    import time

    days_ago = int(time.time()) - 604800  # 60 * 60 * 24 * 7

    content_value = context.element.properties.get('text', None)
    ts_value = context.element.properties.get('created_at', None)
    text_line = ''
    if content_value:
      text_line = content_value.string_value
      if ts_value:
        ts = ts_value.timestamp_value.seconds
        # logging.info("timestamp value: %s", ts)
        if ts < days_ago:
          # logging.info("filtered out ts %s: lt %s", ts, days_ago)
          return []

    words = re.findall(r'[A-Za-z\']+', text_line)
    stopwords = ['t', 'https', 'co', 'the', 'a', 'to', 'rt', 'and', 'in',
      'of', 'is', 'it', 's', 'at', 'on', 'for', 'that', 'by', 'are', 'amp',
      'an', 'so']
    stopwords += list(map(chr, range(97, 123)))
    rwords = []
    for w in words:
      # weed out some 'stopwords'
      if not w.lower() in stopwords:
        rwords.append(w.lower())
    return rwords

class URLExtractingDoFn(beam.DoFn):
  """Parse each line of input text into words."""

  def process(self, context):
    """...
    """
    url_content = context.element.properties.get('urls', None)
    if url_content:
      urls = url_content.array_value.values
      links = []
      for u in urls:
        links.append(u.string_value.lower())
      return links


class EntityWrapper(object):
  """Create a Cloud Datastore entity from the given string."""
  def __init__(self, namespace, kind, ancestor):
    self._namespace = namespace
    self._kind = kind
    self._ancestor = ancestor

  def make_entity(self, content):
    entity = entity_pb2.Entity()
    if self._namespace is not None:
      entity.key.partition_id.namespace_id = self._namespace

    # All entities created will have the same ancestor
    datastore_helper.add_key_path(entity.key, self._kind, self._ancestor,
                                  self._kind, str(uuid.uuid4()))

    datastore_helper.add_properties(entity, {"content": unicode(content)})
    return entity



@app.route('/')
def hello():
    """..."""
    return 'nothing to see.'

@app.route('/launchpipeline')
def launch():
    # TODO: unhardwire
    project = 'aju-vtests3'
    pipeline_options = {
        'project':
            'aju-vtests3',
        'staging_location':
            'gs://aju-vtests3-dataflow/staging',
        'runner':
            # 'BlockingDataflowPipelineRunner',
            'DataflowPipelineRunner',
        'job_name': 'aju-vtests3-twcount',
        'temp_location': 'gs://aju-vtests3-dataflow/temp'
    }
    read_from_datastore(project, PipelineOptions.from_dictionary(pipeline_options))
    print "returned from read_from_datastore"

    return 'Done.'

def make_query(kind):
    """Creates a Cloud Datastore query.
    """

    # query = query_pb2.GqlQuery(
      # query_string="select * from Tweet where created_at > %s" % days_ago)

    query = query_pb2.Query()
    query.kind.add().name = kind

    # timestamp = Timestamp(seconds=days_ago, nanos=0)

    # test_filter = query.filter.composite_filter.filters.add()
    # test_filter.property_filter.op = PropertyFilter.GREATER_THAN
    # test_filter.property_filter.property.name = 'created_at'
    # # test_filter.property_filter.value.timestamp_value = timestamp
    # test_filter.property_filter.value.timestamp_value.CopyFrom(timestamp)
    # # upper_bound.property_filter.value.key_value.CopyFrom(next_key)

    # datastore_helper.set_property_filter(
      # query.filter, 'created_at', PropertyFilter.GREATER_THAN,
      # days_ago)

    return query

def read_from_datastore(project, pipeline_options):
  """Creates a pipeline that reads entities from Cloud Datastore."""
  p = beam.Pipeline(options=pipeline_options)
  # Create a query to read entities from datastore.
  query = make_query('Tweet')
  poutput = 'gs://aju-vtests3-dataflow/output/%s/twoutput' % int(time.time())
  num_shards = 1

  # Read entities from Cloud Datastore into a PCollection.
  lines = p | 'read from datastore' >> ReadFromDatastore(
      project, query, None)

  # Count the occurrences of each word.
  counts = (lines
            | 'split' >> (beam.ParDo(WordExtractingDoFn())
                          .with_output_types(unicode))
            | 'pair_with_one' >> beam.Map(lambda x: (x, 1))
            | 'group' >> beam.GroupByKey()
            | 'count' >> beam.Map(lambda (word, ones): (word, sum(ones)))
            | 'top 300' >> combiners.Top.Of(300, lambda x, y: x[1] < y[1])
            )
  # Count the occurrences of each expanded url in the tweets
  url_counts = (lines
            | 'geturls' >> (beam.ParDo(URLExtractingDoFn())
                          .with_output_types(unicode))
            | 'urls_pair_with_one' >> beam.Map(lambda x: (x, 1))
            | 'urls_group' >> beam.GroupByKey()
            | 'urls_count' >> beam.Map(lambda (word, ones): (word, sum(ones)))
            | 'urls_top 300' >> combiners.Top.Of(300, lambda x, y: x[1] < y[1])
            )

  # Format the counts into a PCollection of strings.
  output = counts | 'format' >> beam.FlatMap(
      lambda x: ['%s: %s' % (xx[0], xx[1]) for xx in x])
  url_output = url_counts | 'urls_format' >> beam.FlatMap(
      lambda x: ['%s: %s' % (xx[0], xx[1]) for xx in x])

  # Write the output using a "Write" transform that has side effects.
  # pylint: disable=expression-not-assigned
  output | 'write' >> beam.io.WriteToText(file_path_prefix=poutput,
                                          num_shards=num_shards)
  url_output | 'urls_write' >> beam.io.WriteToText(
      file_path_prefix=poutput + 'url', num_shards=num_shards)

  # Actually run the pipeline (all operations above are deferred).
  return p.run()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)


