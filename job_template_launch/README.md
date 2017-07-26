

## Prerequisites for running the example

### 1. Basic GCP setup

Follow the "Before you begin" steps on
[this page](https://cloud.google.com/dataflow/docs/quickstarts/quickstart-python#before-you-begin).
Note your project and bucket name; you will need them in a moment.

For local testing (not required, but may be useful), follow the next section on the same page to
[install pip and the Dataflow SDK](https://cloud.google.com/dataflow/docs/quickstarts/quickstart-
python#Setup).


### 2. Create a BigQuery dataset in your project

The app will write its analytic results to BigQuery.  In your project, [create a new
dataset](https://cloud.google.com/bigquery/quickstart-web-ui#create_a_dataset) to use for this
purpose, or note the name of an existing dataset that you will use.

### 3. Create a Twitter App

[Create a Twitter application.](https://apps.twitter.com/).  Note the credentials under the 'Keys
and Access Tokens' tag: 'Consumer Key (API Key)', 'Consumer Secret (API Secret)', 'Access Token',
and 'Access Token Secret'.  You'll need these in moment.

### 4. Library installation and config

1. We need to 'vendor' the libraries used by the app's frontend.
Install the dependencies into the app's `lib` subdirectory like this:

```sh
pip install --target=lib -r standard_requirements.txt
```

(Take a look at `appengine_config.py` to see where we specify to GAE to add those libs).

2. Then, edit `app.yaml` to add the Twitter app credentials that you generated above.

export DATASET=gae_dataflow
export BUCKET=aju-vtests3-dataflow
export PROJECT=aju-vtests3


pip install google-cloud-dataflow

pip install --target=lib -r standard_requirements.txt

For the template creation:

ln -s ../sdk_launch/dfpipe .
python create_template.py

gcloud app deploy cron.yaml
