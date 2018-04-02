FROM ubuntu:16.04
MAINTAINER info@landho-app.com
LABEL Description="Land Ho! Crawler" Vendor="Land Ho!" Version="1.0.2"

# INSTALL DEPENDENCIES
RUN apt-get update -y && apt-get install -y python-pip python-setuptools openssl python-dev libssl-dev cron
RUN pip install --upgrade pip

# Copy and install python
COPY . /srv
WORKDIR /srv

RUN pip install -r requirements.txt

# Add crontab file in the cron directory
COPY crontab /etc/cron.d/landho-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/landho-cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the command on container startup
CMD cron && tail -f /var/log/cron.log
