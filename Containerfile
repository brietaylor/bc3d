FROM fedora:31

RUN dnf upgrade -y
RUN dnf install -y blender python3-boto3 xz awscli

ADD dem23d_blender.py /opt/dem23d_blender.py
ADD aws/bc3d_s3_credentials /root/.aws/credentials

WORKDIR /opt/
