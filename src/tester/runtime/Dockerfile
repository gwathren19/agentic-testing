FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    sudo \
    python3 \
    python3-pip \
    curl wget ping nmap sqlmap \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash tester

RUN echo "tester ALL=(ALL) NOPASSWD: /usr/bin/apt-get" >> /etc/sudoers

USER tester
WORKDIR /home/tester

CMD ["bash"]