FROM nvcr.io/nvidia/cuda:12.3.2-cudnn9-devel-ubuntu22.04

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG USER_GECOS=VSCode

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
      wget \
      bzip2 \
      build-essential \
      git \
      git-lfs \
      curl \
      python3-pip \
      python3-venv \
      vim \
      less \
      tree \
      apt-utils \
      netcat \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN \
  # Create a non-root user
  groupadd --gid $USER_GID $USERNAME \
  && useradd \
    -s /bin/bash \
    --uid $USER_UID \
    --gid $USER_GID \
    -c "$USER_GECOS" \
    -m $USERNAME \
  && export DEBIAN_FRONTEND=noninteractive \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
    sudo \
    locales \
    tzdata \
  # Add sudo support for non-root user
  && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
  && chmod 0440 /etc/sudoers.d/$USERNAME \
  # JP locale
  && sed -i -E 's/# (en_US.UTF-8)/\1/' /etc/locale.gen \
  && sed -i -E 's/# (ja_JP.UTF-8)/\1/' /etc/locale.gen \
  && locale-gen \
  # timezone
  && ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime \
  && dpkg-reconfigure tzdata \
  # Clean up
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/*

RUN export DEBIAN_FRONTEND=noninteractive\
    && apt-get update \
    && apt-get install -y --no-install-recommends \
      python3-dev \
      libgl1-mesa-dev \
      libglib2.0-0 \
      poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
