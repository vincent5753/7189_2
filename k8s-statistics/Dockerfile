FROM python:3.6
MAINTAINER VP

WORKDIR /statistics
ENV PYTHONUNBUFFERED=0
COPY statistics.py statistics.py
COPY excludeapp.list excludeapp.list
#RUN apt-get update
#RUN pt-get install -y git
#RUN git clone --recursive https://github.com/kubernetes-client/python.git
#RUN python python/setup.py install

RUN pip install kubernetes

CMD [ "python", "statistics.py" ]
