ARG OUTPUT=run

FROM python:3.9 as builder

COPY requirements.txt /src/requirements.txt
WORKDIR /src
RUN pip install -r requirements.txt

COPY runci /src/runci/
COPY main.py /src/main.py
COPY setup.py /src/setup.py

COPY tests /src/tests/
RUN python -m unittest

RUN pip install .

COPY runci.spec /src/runci.spec
RUN pyinstaller runci.spec


FROM builder as artifact
CMD ["pyinstaller", "-F", "--distpath", "/out", "-n", "runci", "runci.spec"]


FROM python:3.9 as run
ARG EXTENSION=
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
COPY --from=builder /src/dist/runci${EXTENSION} /
COPY docker-entrypoint.sh /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

FROM ${OUTPUT}