############################################################
# Dockerfile to build Nginx Amplify Agent container
# Based on Centos6
############################################################

# Set the base image to Centos
FROM centos:6

# File Author / Maintainer
MAINTAINER Mike Belov

# Install basic applications
RUN yum -y install tar curl wget net-tools redhat-lsb initscripts
RUN yum -y groupinstall 'Development Tools'

# Install Python and Basic Python Tools
RUN yum -y install python python-devel python-distribute
RUN wget --no-check-certificate https://bootstrap.pypa.io/ez_setup.py -O - | python
RUN easy_install pip

# Install nginx
ADD nginx.repo /etc/yum.repos.d/nginx.repo
RUN yum -y install nginx
RUN mkdir /run

# Copy the application folder inside the container
ADD . /amplify

# Get pip to download and install requirements:
RUN pip install rstr==2.2.3 greenlet==0.4.9 gevent==1.0.2 lockfile==0.11.0 netaddr==0.7.18 netifaces==0.10.4 psutil==4.0.0 requests==2.10.0 ujson==1.33 python-daemon==2.0.6 pyparsing==2.0.1 setproctitle==1.1.10

ENV AMPLIFY_ENVIRONMENT development
ENV PYTHONPATH /amplify/

# Set the default directory where CMD will execute
WORKDIR /amplify

# add stub status
ADD nginx.conf /etc/nginx/nginx.conf

# add ssl
ADD amplify-agent-test.crt /etc/nginx/certs.d/amplify-agent-test.crt
ADD amplify-agent-test.key /etc/nginx/certs.d/amplify-agent-test.key

CMD /usr/sbin/nginx && python /amplify/nginx-amplify-agent.py start --config=/amplify/etc/agent.conf.development && tail -f /amplify/log/agent.log