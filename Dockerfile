FROM centos:7

ARG vcs_ref=
LABEL org.label-schema.vcs-ref=$vcs_ref

RUN yum -y update && \
    yum -y install epel-release && \
    yum -y install \
	python2-pip \
	python-BeautifulSoup \
	python-dateutil \
	python-feedparser \
	python-jinja2 \
	python-lxml \
	python-simplejson \
	python-gunicorn && \
    yum clean all

RUN pip install pytidylib

ADD . /srv/planeteria

WORKDIR /srv/planeteria

RUN echo http://localhost:8001 > data/base_href

EXPOSE 8001
CMD gunicorn --bind=0.0.0.0:8001 --access-logfile=- wsgi:application
