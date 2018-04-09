FROM ubuntu:16.04

RUN apt-get update && apt-get -y dist-upgrade
RUN apt-get -y install python3-pip sudo git

RUN useradd -m user

RUN echo 'user ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/80-user

RUN pip3 install flask PyJWT requests netifaces

USER user
WORKDIR /home/user

COPY . SecurityApplianceWrapper

RUN cd SecurityApplianceWrapper/ && chmod +x setup.sh && ./setup.sh -y --nosystemd

EXPOSE 5001

CMD /usr/bin/python3 /home/wrapper/bin/SecAppWrapper/start_wrapper.py
