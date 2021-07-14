################ PLACES #####################
FROM debian:testing

WORKDIR /places-finder

RUN apt-get -qq update \
  && DEBIAN_FRONTEND=noninteractive \
  apt-get -y install --no-install-recommends \
    ca-certificates \
  && apt-get clean

# RUN echo "deb [trusted=yes] https://apt.fury.io/caddy/ /" \
#     | tee -a /etc/apt/sources.list.d/caddy-fury.list
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y update \
    && apt-get -y install \
      --no-install-recommends \
      bash \
    #   caddy \
      cron \
      curl \
      dnsutils \
      fcgiwrap \
      file \
      gettext \
      git \
      grep \
      htop \
      jq \
      less \
      net-tools \
      network-manager \
      nmap \
      osmium-tool \
      procps \
      unzip \
      util-linux \
      uuid-runtime \
      vim \
      wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y update \
    && apt-get -y install \
      --no-install-recommends \
      gdal-bin \
      osmctools \
      postgresql-client \
      python3-wheel \
      python3-geopandas \
      python3-geojson \
      python3-pycurl \
      python3-pip \
      python3-rtree \
      python3-pyosmium \
      python3-requests \
      python3-flask \
      python3-sqlalchemy \
      python3-psycopg2 \ 
      python3-geoalchemy2 \
      python3-socketio \
      python3-wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


RUN mkdir -p /places-finder
COPY ./requirements.txt /places-finder/
RUN pip3 install -r /places-finder/requirements.txt


COPY loadTours.py /places-finder/loadTours.py
COPY ./places-finder.py /places-finder/places-finder.py
COPY ./regions.json /places-finder/regions.json
COPY ./tours.osm.pbf /places-finder/tours.osm.pbf
RUN chmod +x /places-finder/loadTours.py

CMD bash -c "/places-finder/main.py"  



