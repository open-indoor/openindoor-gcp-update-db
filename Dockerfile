################ PLACES #####################
FROM debian:latest

RUN apt update && apt upgrade\
    && apt install \
      bash \
      cronie \
      curl \
      file \
      gettext \
      git \
      grep \
      htop \
      jq \
      less \
      net-tools \
      nmap \
      osmium-tool \
      procps-ng \
      unzip \
      util-linux \
      uuid \
      vim \
      wget \
    && dnf -y clean all

RUN apt install \
      gdal \
      osmctools \
      postgresql \
      python3-wheel \
      python3-geopandas \
      python3-geojson \
      python3-pycurl \
      python3-pip \
      python3-rtree \
      python3-requests \
      python3-flask \
      python3-sqlalchemy \
      python3-psycopg2 \ 
      python3-socketio \
    && dnf -q clean all

RUN pip install wget
RUN pip install geoalchemy2
RUN mkdir -p /places-finder
COPY ./requirements.txt /places-finder/
RUN pip3 install -r /places-finder/requirements.txt

# COPY ./Caddyfile /etc/caddy/Caddyfile

WORKDIR /places-finder

COPY ./places-finder/main.py /places-finder/main.py
COPY ./places-finder/regions.json /places-finder/regions.json
COPY ./places-finder/interior_data.py /places-finder/interior_data.py
COPY ./places-finder/keep.json /places-finder/keep.json
RUN chmod +x /places-finder/main.py
RUN chmod +x /places-finder/interior_data.py


#RUN mkdir -p /data/tmp

CMD bash -c "/places-finder/main.py"
