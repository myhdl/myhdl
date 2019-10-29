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

USER masocist
RUN install -d /home/masocist/scripts/recipes
RUN wget https://raw.githubusercontent.com/hackfin/myhdl/upgrade/scripts/recipes/myhdl.mk -O /home/masocist/scripts/recipes/myhdl.mk
WORKDIR /home/masocist

