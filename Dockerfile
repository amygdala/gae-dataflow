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
ENV GOOGLE_APPLICATION_CREDENTIALS /home/vmagent/app/aju-vtests3-f573035097a1.json
# ENV PATH /env/bin:/home/vmagent/app/google-cloud-sdk/bin:$PATH
ENV PATH /home/vmagent/app/google-cloud-sdk/bin:$PATH

EXPOSE 8080
WORKDIR /app

# CMD gunicorn -b :$PORT main:app  # hmmmm
CMD python main_df.py

