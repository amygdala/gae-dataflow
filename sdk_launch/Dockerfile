# Copyright 2017 Google Inc.
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

FROM gcr.io/google_appengine/python

RUN apt-get update
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN apt-get install -y curl

# You may later want to change this download as the Cloud SDK version is updated.
RUN curl https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-176.0.0-linux-x86_64.tar.gz | tar xvz
RUN ./google-cloud-sdk/install.sh -q
RUN ./google-cloud-sdk/bin/gcloud components install beta

ADD . /app/
RUN pip install -r requirements.txt
ENV PATH /home/vmagent/app/google-cloud-sdk/bin:$PATH
# CHANGE THIS: Edit the following 3 lines to use your settings.
ENV PROJECT your-project
ENV BUCKET your-bucket-name
ENV DATASET your-dataset-name

EXPOSE 8080
WORKDIR /app

CMD gunicorn -b :$PORT main_df:app

