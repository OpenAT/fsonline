# odoo operating system image
FROM python:3.8-slim-buster AS odoo-os

EXPOSE 8069 8072


ARG GEOIP_UPDATER_VERSION=4.3.0
ARG WKHTMLTOPDF_VERSION=0.12.5
ARG WKHTMLTOPDF_CHECKSUM='1140b0ab02aa6e17346af2f14ed0de807376de475ba90e1db3975f112fbd20bb'

# Requirements and recommendations
# See https://github.com/$ODOO_SOURCE/blob/$ODOO_VERSION/debian/control
RUN apt-get -qq update \
    && apt-get install -yqq --no-install-recommends \
        curl \
    && curl -SLo wkhtmltox.deb https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/${WKHTMLTOPDF_VERSION}/wkhtmltox_${WKHTMLTOPDF_VERSION}-1.stretch_amd64.deb \
    && echo "${WKHTMLTOPDF_CHECKSUM}  wkhtmltox.deb" | sha256sum -c - \
    && apt-get install -yqq --no-install-recommends \
        ./wkhtmltox.deb \
        chromium \
        ffmpeg \
        fonts-liberation2 \
        gettext \
        git \
        gnupg2 \
        locales-all \
        nano \
        npm \
        openssh-client \
        telnet \
        vim \
        zlibc \
    && echo 'deb http://apt.postgresql.org/pub/repos/apt/ stretch-pgdg main' >> /etc/apt/sources.list.d/postgresql.list \
    && curl -SL https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
    && apt-get update \
    && curl --silent -L --output geoipupdate_${GEOIP_UPDATER_VERSION}_linux_amd64.deb https://github.com/maxmind/geoipupdate/releases/download/v${GEOIP_UPDATER_VERSION}/geoipupdate_${GEOIP_UPDATER_VERSION}_linux_amd64.deb \
    && dpkg -i geoipupdate_${GEOIP_UPDATER_VERSION}_linux_amd64.deb \
    && rm geoipupdate_${GEOIP_UPDATER_VERSION}_linux_amd64.deb \
    && apt-get autopurge -yqq \
    && rm -Rf wkhtmltox.deb /var/lib/apt/lists/* /tmp/* \
    && sync

VOLUME ["/opt/odoo"]
WORKDIR /opt/odoo
# Do more stuff
ENTRYPOINT ["python3", "/opt/odoo/odoo-bin"]


#COPY bin/* /usr/local/bin/
#COPY lib/doodbalib /usr/local/lib/python3.8/site-packages/doodbalib
#COPY build.d common/build.d
#COPY conf.d common/conf.d
#COPY entrypoint.d common/entrypoint.d
#RUN mkdir -p auto/addons auto/geoip custom/src/private \
#    && ln /usr/local/bin/direxec common/entrypoint \
#    && ln /usr/local/bin/direxec common/build \
#    && chmod -R a+rx common/entrypoint* common/build* /usr/local/bin \
#    && chmod -R a+rX /usr/local/lib/python3.8/site-packages/doodbalib \
#    && mv /etc/GeoIP.conf /opt/odoo/auto/geoip/GeoIP.conf \
#    && ln -s /opt/odoo/auto/geoip/GeoIP.conf /etc/GeoIP.conf \
#    && sed -i 's/.*DatabaseDirectory .*$/DatabaseDirectory \/opt\/odoo\/auto\/geoip\//g' /opt/odoo/auto/geoip/GeoIP.conf \
#    && sync
