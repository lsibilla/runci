ARG OUTPUT=run

FROM python:3.9 as builder

RUN pip install flake8 coverage

COPY requirements.txt /src/requirements.txt
WORKDIR /src
RUN pip install -r requirements.txt

COPY main.py /src/main.py
COPY setup.py /src/setup.py
COPY runci /src/runci/
COPY tests /src/tests/

RUN flake8 . --count  --max-complexity=10 --max-line-length=127 --show-source --statistics
RUN python -m unittest
RUN coverage run --source ./runci --timid -m unittest && coverage report -m

RUN pip install .

COPY runci.spec /src/runci.spec
RUN pyinstaller runci.spec


FROM builder as artifact
CMD ["pyinstaller", "-F", "--distpath", "/out", "-n", "runci", "runci.spec"]


FROM python:3.9-alpine as run
ARG EXTENSION=
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
COPY --from=builder /src/dist/runci${EXTENSION} /
COPY docker-entrypoint.sh /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

FROM ${OUTPUT}
