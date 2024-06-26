ARG USER_NAME=translatable
ARG USER_UID=1000

FROM nvcr.io/nvidia/cuda:12.3.2-cudnn9-devel-ubuntu22.04 AS build

ARG USER_NAME
ARG USER_UID

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
      bzip2 \
      build-essential \
      git \
      curl \
      libgl1-mesa-dev \
      libglib2.0-0 \
      poppler-utils \
      python3-dev \
      python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
  
RUN useradd -m -s /bin/bash -u $USER_UID $USER_NAME
USER $USER_NAME
WORKDIR /app

RUN python3 -m pip install --user --upgrade pip

COPY --chown=$USER_NAME:$USER_NAME requirements.txt ./

RUN  python3 -m pip install --user -r requirements.txt \
  && python3 -m pip install --no-build-isolation \
    'git+https://github.com/facebookresearch/detectron2.git@v0.6#egg=detectron2'

COPY --chown=$USER_NAME:$USER_NAME . .

# Stage 2
FROM nvcr.io/nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04

ARG USER_NAME
ARG USER_UID

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      libgl1-mesa-dev \
      libglib2.0-0 \
      poppler-utils \
      python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash -u $USER_UID $USER_NAME
USER $USER_NAME
WORKDIR /app

COPY --from=build /home/$USER_NAME/.local /home/$USER_NAME/.local
COPY --from=build /app /app

ENV PATH=$PATH:/home/$USER_NAME/.local/bin
