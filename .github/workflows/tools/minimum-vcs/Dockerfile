FROM python:3.7-buster
RUN set -ex; \
    cd tmp; \
    wget http://snapshot.debian.org/archive/debian/20121102T092448Z/pool/main/g/git/git-man_1.8.0-1_all.deb; \
    dpkg -i git-man_1.8.0-1_all.deb; \
    wget http://snapshot.debian.org/archive/debian/20121102T151957Z/pool/main/g/git/git_1.8.0-1_"$(dpkg --print-architecture)".deb; \
    dpkg -i git_1.8.0-1_*.deb
RUN set -ex; \
    pip install --upgrade pip wheel; \
    pip install --upgrade --upgrade-strategy=eager tox; \
    pip install mercurial==5.2
