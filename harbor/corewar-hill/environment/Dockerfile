FROM python:3.12-slim
# Agent workspace: the scoring simulator, the language reference, the public
# sparring pool and a local battle tool. The hidden hill is not in this image.
RUN apt-get update && apt-get install -y --no-install-recommends gcc make libc6-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir mcp==1.30.0
COPY arena/pmars /opt/pmars-src
RUN make -C /opt/pmars-src pmars && mkdir -p /app/bin && cp /opt/pmars-src/pmars /app/bin/pmars && rm -rf /opt/pmars-src
COPY arena/data/sparring /app/sparring
COPY doc /app/doc
COPY battle.py /app/tools/battle.py
RUN touch /app/submission.red
WORKDIR /app
