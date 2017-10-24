
# Running Dataflow jobs from Google App Engine

This directory contains two different examples that show how you can run
[Cloud Dataflow](https://cloud.google.com/dataflow/) pipelines from
[App Engine](https://cloud.google.com/appengine/) apps, as a replacement
for the older
[GAE Python MapReduce libraries](https://github.com/GoogleCloudPlatform/appengine-mapreduce),
as well as do much more.

The examples show how to periodically launch a Python Dataflow pipeline from GAE, to
analyze data stored in Cloud Datastore; in this case, tweets from Twitter.

The example in [`sdk_launch`](./sdk_launch) shows how to launch Dataflow jobs via the Dataflow SDK.  This requires the use of an App Engine Flex [service](https://cloud.google.com/appengine/docs/standard/python/an-overview-of-app-engine) to launch the pipeline.

The example in [`job_template_launch`](./job_template_launch) shows how to launch Dataflow jobs via job [Templates](https://cloud.google.com/dataflow/docs/templates/overview). This can be done using only App Engine Standard.
Prior to deploying the app, you create a pipeline template (via your local command line, in this example) for the app to use.

## Contributions

Contributions are not currently accepted.  This is not an official Google product.
