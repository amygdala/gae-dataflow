
# Introduction

This code example shows how you can run
[Cloud Dataflow](https://cloud.google.com/dataflow/) pipelines from
[App Engine](https://cloud.google.com/appengine/) apps, as a replacement
for the older
[GAE Python MapReduce libraries](https://github.com/GoogleCloudPlatform/appengine-mapreduce),
as well as do much more.

The example shows how to periodically launch a Python Dataflow pipeline from GAE, to
analyze data stored in Cloud Datastore; in this case, tweets from Twitter.

This example uses [Dataflow Templates](https://cloud.google.com/dataflow/docs/templates/overview) to launch the pipeline jobs. Since we're just calling the Templates API to launch the jobs, we can use App Engine standard.
For an example that uses the same pipeline, but uses the Dataflow SDK to launch the pipeline jobs, see the [`sdk_launch`](../sdk_launch) directory.  Because of its use of the SDK, that example requires App Engine Flex.

Now that Dataflow Templates are available, they are likely the more straightforward option for this type of task in most cases. See the Templates documentation for more detail, including information on how you can pass in runtime parameters.

###  The Dataflow pipeline

The Python Dataflow pipeline reads recent tweets from the past N days from Cloud Datastore, then
essentially splits into three processing branches. It finds the top N most popular words in terms of
the percentage of tweets they were found in, calculates the top N most popular URLs in terms of
their count, and then derives relevant word co-occurrences (bigrams) using an
approximation to a [tf*idf](https://en.wikipedia.org/wiki/Tf%E2%80%93idf)
ranking metric.  It writes the results to three BigQuery tables.

<a href="https://amy-jo.storage.googleapis.com/images/gae_dataflow/gae_df_graph.png" target="_blank"><img src="https://amy-jo.storage.googleapis.com/images/gae_dataflow/gae_df_graph.png" width=500/></a>

## Prerequisites for running the example

### 1. Basic GCP setup

Follow the "Before you begin" steps on
[this page](https://cloud.google.com/dataflow/docs/quickstarts/quickstart-python#before-you-begin).
Note your project and bucket name; you will need them in a moment.

Then, follow the next section on the same page to
[install pip and the Dataflow SDK](https://cloud.google.com/dataflow/docs/quickstarts/quickstart-
python#Setup).  We'll need this to create our Dataflow Template.


### 2. Create a BigQuery dataset in your project

The app will write its analytic results to BigQuery.  In your project, [create a new
dataset](https://cloud.google.com/bigquery/quickstart-web-ui#create_a_dataset) to use for this
purpose, or note the name of an existing dataset that you will use.

### 3. Create a Twitter App

[Create a Twitter application.](https://apps.twitter.com/).  Note the credentials under the 'Keys
and Access Tokens' tag: 'Consumer Key (API Key)', 'Consumer Secret (API Secret)', 'Access Token',
and 'Access Token Secret'.  You'll need these in moment.

### 4. Library installation

We need to 'vendor' the libraries used by the app's frontend.
Install the dependencies into the app's `lib` subdirectory like this:

```sh
pip install --target=lib -r standard_requirements.txt
```

(Take a look at `appengine_config.py` to see where we specify to GAE to add those libs).


### 5. Template Creation

Now we're set to run the template creation script. It expects `PROJECT`, `BUCKET`, and `DATASET` environment variables to be set. Edit the following and paste at the command line:

```sh
export DATASET=your-dataset
export BUCKET=your-bucket
export PROJECT=your-project
```

Then, run the template creation script:

```sh
python create_template.py
```

Note the resulting template name that is output to the command line. By default it should be:
`<PROJECT> + '-twproc_tmpl'`, but you can change that in the script if you like.


### 6. Edit app.yaml

Finally, edit `app.yaml`.  Add the Twitter app credentials that you generated above.  Then, fill in your PROJECT, DATASET, and BUCKET names.

Next, add your TEMPLATE name.  By default, it will be `<PROJECT>-twproc_templ`, where `<PROJECT>` is replaced with your project name.

### 7. Deploy the app

Now we're ready to deploy the app.  Deploy both the `app.yaml` spec, and the `cron.yaml` spec:

```sh
gcloud app deploy app.yaml
gcloud app deploy cron.yaml
```


## Testing your deployment

To test your deployment, manually trigger the cron jobs.  To do this, go to the
[cloud console](https://console.cloud.google.com) for your project,
and visit the [App Engine pane](https://console.cloud.google.com/appengine).
Then, click on 'Task Queues' in the left navbar, then the 'Cron Jobs' tab in the center pane.

Then, click `Run now` for the `/timeline` cron job.  This is the job that fetches tweets and stores
them in the Datastore. After it runs, you should be able to see `Tweet` entities in the Datastore.
Visit the [Datastore](https://console.cloud.google.com/datastore/entities) pane in the Cloud
Console, and select `Tweet` from the 'Entities' pull-down menu. You can also try a GQL query:

```
select * from Tweet order by created_at desc
```

Once you know that the 'fetch tweets' cron is running successfully, click `Run now` for the
`/launchtemplatejob` cron. This should kick off a Dataflow job and return within a few seconds.  You
should be able to see the job running in the [Dataflow pane](https://console.cloud.google.com/dataflow)
of the Cloud Console. It should finish in a few minutes. Check that it finishes without error.

Once it has finished, you ought to see three new tables in your BigQuery dataset: `urls`,
`word_counts`, and `word_cooccur`.

If you see any problems, make sure that you've configured the `app.yaml` as described above, and check the logs for clues.

Note: the `/launchtemplatejob` request handler is configured to return without launching the pipeline
if the request has not originated as a cron request. You can comment out that logic in `main.py`,
in the `LaunchJob` class, if you'd like to override that behavior.
