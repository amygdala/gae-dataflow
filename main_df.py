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

import logging
import re
import time
import uuid

from google.datastore.v1 import entity_pb2
from google.datastore.v1 import query_pb2
from googledatastore import helper as datastore_helper, PropertyFilter

import apache_beam as beam
from apache_beam import combiners
from apache_beam.pvalue import AsDict
from apache_beam.pvalue import AsSingleton
from apache_beam.io.datastore.v1.datastoreio import ReadFromDatastore
from apache_beam.io.datastore.v1.datastoreio import WriteToDatastore
from apache_beam.utils.options import PipelineOptions

from flask import Flask

app = Flask(__name__)


class WordExtractingDoFn(beam.DoFn):
  """Parse each line of input text into words."""

  def process(self, context):
    """...
    """

    content_value = context.element.properties.get('text', None)
    text_line = ''
    if content_value:
      text_line = content_value.string_value

    words = re.findall(r'[A-Za-z\']+', text_line)
    stopwords = [
        't', 'https', 'co', 'the', 'a', 'to', 'rt', 'and', 'in', 'of', 'is',
        'it', 's', 'at', 'on', 'for', 'that', 'by', 'are', 'amp', 'an', 'so',
        'you', 'this', 'if', 'be', 'was', 'but', 'as'
    ]
    stopwords += list(map(chr, range(97, 123)))
    rwords = []
    for w in words:
      # weed out some 'stopwords'
      if not w.lower() in stopwords:
        rwords.append(w.lower())
    return rwords


class CoOccurExtractingDoFn(beam.DoFn):
  """..."""

  def process(self, context):
    """...
    """

    content_value = context.element.properties.get('text', None)
    text_line = ''
    if content_value:
      text_line = content_value.string_value

    words = re.findall(r'[A-Za-z\']+', text_line)
    stopwords = [
        't', 'https', 'co', 'the', 'a', 'to', 'rt', 'and', 'in', 'of', 'is',
        'it', 's', 'at', 'on', 'for', 'that', 'by', 'are', 'amp', 'an', 'so',
        'you', 'this', 'if', 'be', 'was', 'but', 'as'
    ]
    stopwords += list(map(chr, range(97, 123)))
    co = set()
    # TODO - make nicer
    for w1 in words:
      w1 = w1.lower()
      if w1 in stopwords:
        continue
      for w2 in words:
        w2 = w2.lower()
        if w2 in stopwords:
          continue
        if not w1 == w2:
          tlist = [w1, w2]
          tlist.sort()
          co.add(tuple(tlist))
    return list(co)


class URLExtractingDoFn(beam.DoFn):
  """..."""

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
      'project': 'aju-vtests3',
      'staging_location': 'gs://aju-vtests3-dataflow/staging',
      'runner':
      # 'BlockingDataflowPipelineRunner',
      'DataflowPipelineRunner',
      'job_name': 'aju-vtests3-twcount',
      'num_workers': 10,
      # 'save_main_session': True,
      'temp_location': 'gs://aju-vtests3-dataflow/temp'
  }
  read_from_datastore(project,
                      PipelineOptions.from_dictionary(pipeline_options))
  print "returned from read_from_datastore"

  return 'Done.'


def make_query(kind):
  """Creates a Cloud Datastore query."""

  days_ago = int(time.time()) - 604800  # 60 * 60 * 24 * 7 seconds

  query = query_pb2.Query()
  query.kind.add().name = kind

  datastore_helper.set_property_filter(query.filter, 'created_at',
                                       PropertyFilter.GREATER_THAN,
                                       (days_ago * 1000))  # nanoseconds

  return query


def read_from_datastore(project, pipeline_options):
  """Creates a pipeline that reads entities from Cloud Datastore...
  """
  p = beam.Pipeline(options=pipeline_options)
  # Create a query to read entities from datastore.
  query = make_query('Tweet')
  poutput = 'gs://aju-vtests3-dataflow/output/%s/twoutput' % int(time.time())
  num_shards = 1
  days_ago = int(time.time()) - 604800  # 60 * 60 * 24 * 7

  # Read entities from Cloud Datastore into a PCollection.
  lines = (p
      | 'read from datastore' >> ReadFromDatastore(
          project, query, None)
      # | 'after date' >> beam.Filter(lambda elt: {
      #     elt.properties.get('created_at', None).timestamp_value.seconds > days_ago
      #   })
      )

  global_count = AsSingleton(
    lines
    | 'global count' >> beam.combiners.Count.Globally())

  # Count the occurrences of each word.
  percents = (lines
            | 'split' >> (beam.ParDo(WordExtractingDoFn())
                          .with_output_types(unicode))
            | 'pair_with_one' >> beam.Map(lambda x: (x, 1))
            | 'group' >> beam.GroupByKey()
            | 'count' >> beam.Map(lambda (word, ones): (word, sum(ones)))
            | 'in tweets percent' >> beam.Map(
                lambda (word, wsum), gc: (word, float(wsum)/gc), global_count))
  counts = (percents
            | 'top 500' >> combiners.Top.Of(500, lambda x, y: x[1] < y[1])
            )
  # Count the occurrences of each expanded url in the tweets
  url_counts = (lines
            | 'geturls' >> (beam.ParDo(URLExtractingDoFn())
                          .with_output_types(unicode))
            | 'urls_pair_with_one' >> beam.Map(lambda x: (x, 1))
            | 'urls_group' >> beam.GroupByKey()
            | 'urls_count' >> beam.Map(lambda (word, ones): (word, sum(ones)))
            | 'urls top 300' >> combiners.Top.Of(300, lambda x, y: x[1] < y[1])
            )

  def join_cinfo(cooccur, percents):
    """..."""
    import math

    word1 = cooccur[0][0]
    word2 = cooccur[0][1]
    word1_percent = 0
    word2_percent = 0
    weight1 = 0
    weight2 = 0
    if word1 in percents:
      word1_percent = percents[word1]
    if word2 in percents:
      word2_percent = percents[word2]
    if word1_percent:
      weight1 = 1 / word1_percent
    if word2_percent:
      weight2 = 1 / word2_percent
    return (cooccur[0], cooccur[1], cooccur[1] *
            math.log(min(weight1, weight2)))

  # Count the word co-occurences
  cooccur_rankings = (lines
            | 'getcooccur' >> (beam.ParDo(CoOccurExtractingDoFn())
                               # .with_output_types(typehints.Tuple[str, str])
                          )
            | 'co_pair_with_one' >> beam.Map(lambda x: (x, 1))
            | 'co_group' >> beam.GroupByKey()
            | 'co_count' >> beam.Map(lambda (wordts, ones): (wordts, sum(ones)))
            | 'weights'  >> beam.Map(join_cinfo, AsDict(percents))
            | 'co top 300' >> combiners.Top.Of(300, lambda x, y: x[2] < y[2])
            )

  # Format the counts into a PCollection of strings.
  output = counts | 'format' >> beam.FlatMap(
      lambda x: ['%s: %s' % (xx[0], xx[1]) for xx in x])
  url_output = url_counts | 'urls_format' >> beam.FlatMap(
      lambda x: ['%s: %s' % (xx[0], xx[1]) for xx in x])
  co_output = cooccur_rankings | 'co_format' >> beam.FlatMap(
      lambda x: ['%s: %s , %s' % (xx[0], xx[1], xx[2]) for xx in x])

  # Write the output using a "Write" transform that has side effects.
  # pylint: disable=expression-not-assigned
  output | 'write' >> beam.io.WriteToText(file_path_prefix=poutput,
                                          num_shards=num_shards)
  url_output | 'urls_write' >> beam.io.WriteToText(
      file_path_prefix=poutput + 'url', num_shards=num_shards)
  co_output | 'co_write' >> beam.io.WriteToText(
      file_path_prefix=poutput + 'co', num_shards=num_shards)

  # Actually run the pipeline (all operations above are deferred).
  return p.run()


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=True)
