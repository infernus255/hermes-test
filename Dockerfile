FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        git \
        python3 \
        python3-venv \
        python3-pip \
        npm \
        xz-utils \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

ENV PATH="/root/.local/bin:/root/.hermes/hermes-agent/venv/bin:$PATH"
WORKDIR /root

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 9119
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["hermes", "gateway", "run"]
