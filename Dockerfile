# syntax=docker/dockerfile:1
FROM ubuntu:20.04
COPY requirements.txt requirements.txt
RUN apt-get update &&  \
    apt-get install -yqq software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    add-apt-repository ppa:ubuntu-toolchain-r/test && \
    apt-get update && \
    apt-get install -yqq gcc g++ python3.8 python3-distutils python3-apt curl \
                         python3-dev unzip && \
    apt-get upgrade libstdc++6 -yqq && \
    curl -L https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3 get-pip.py && \
    apt-get install -y git && \
    pip3 install --no-cache-dir -r requirements.txt && \
    pip3 install git+https://github.com/Warra07/mlflow-hf-transformers-flavor.git && \
    pip3 install --no-cache-dir torch==1.11.0+cpu -f https://download.pytorch.org/whl/torch_stable.html
COPY . .
EXPOSE 1234