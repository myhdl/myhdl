FROM ghdl/ghdl:buster-gcc-7.2.0

RUN apt-get update --allow-releaseinfo-change ; \
	apt-get install -y make git wget bzip2 \
	python python-pytest python-pip \
	screen gnupg sudo pkg-config autoconf libtool iverilog

# Install some python modules:
RUN pip install intelhex numpy

RUN useradd -u 1000 -g 100 -m -s /bin/bash masocist 
RUN echo "export LD_LIBRARY_PATH=\$HOME/src/vhdl/ghdlex/src:$LD_LIBRARY_PATH" >> /home/masocist/.bashrc

RUN adduser masocist sudo
RUN echo "masocist ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/masocist-nopw

COPY Makefile /home/masocist
COPY scripts  /home/masocist/scripts
RUN chown -R masocist scripts

USER masocist
WORKDIR /home/masocist

