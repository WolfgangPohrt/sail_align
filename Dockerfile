FROM ubuntu:18.04
COPY ./HTK-3.4.1.tar /home
COPY ./HDecode-3.4.1.tar /home
RUN cd /home \
	&& tar xvf HTK-3.4.1.tar \
	&& tar xvf HDecode-3.4.1.tar
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update \
	&& apt-get install -y git \
	&& apt install -y build-essential gcc-multilib \
	&& apt install -y python3 \
	&& apt-get -y install python3-pip
RUN cd /home/htk \
	&& sed -i 's/^ \+/\t/' HLMTools/Makefile.in \
	&& ./configure --disable-hslab \
	&& make all \
	&& make install \
	&& make hdecode \
	&& make install-hdecode
# this is a only to prevent the git clone from being cached #
ADD https://api.github.com/repos/WolfgangPohrt/sail_align/git/refs/heads/service version.json
RUN cd / \
	&& git clone --branch service https://github.com/WolfgangPohrt/sail_align.git
RUN cd /sail_align \
	&& export PERL_MM_USE_DEFAULT=1 \
	&& cpan Module::Build \
	&& cpan LWP::Simple \
	&& cpan Archive::Extract \
	&& perl Build.PL \
	&& ./Build installdeps \
	&& ./Build \
	&& ./Build install
RUN apt install -y sox
WORKDIR /sail_align
RUN pip3 install -r requirements.txt
CMD [ "python3", "app.py"]



