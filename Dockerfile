# Copyright 2016 Google Inc.
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

# Install the fortunes binary from the debian repositories.
RUN apt-get update
RUN pip install --upgrade pip
RUN apt-get install -y curl

RUN curl https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-138.0.0-linux-x86_64.tar.gz | tar xvz
RUN ./google-cloud-sdk/install.sh -q
RUN ./google-cloud-sdk/bin/gcloud components install beta

# RUN apt-get install -y emacs

# Change the -p argument to use Python 2.7 if desired.
# RUN virtualenv /env -p python2.7

# Set virtualenv environment variables. This is equivalent to running
# source /env/bin/activate.
# ENV VIRTUAL_ENV /env

ADD requirements.txt /app/
RUN pip install -r requirements.txt
ADD . /app/
# CHANGE THIS to point to your credentials file
ENV GOOGLE_APPLICATION_CREDENTIALS /path/to/credentials/file
# ENV PATH /env/bin:/home/vmagent/app/google-cloud-sdk/bin:$PATH
ENV PATH /home/vmagent/app/google-cloud-sdk/bin:$PATH

EXPOSE 8080
WORKDIR /app

# CMD gunicorn -b :$PORT main:app  # hmmmm
CMD python main_df.py

