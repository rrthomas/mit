ARG BASE_IMAGE=ubuntu
FROM ${BASE_IMAGE}

# Test with non-root user.
ENV TEST_USER tester
ENV WORK_DIR "/work"

RUN uname -a
RUN apt-get update -qq && \
  apt-get install -yq --no-install-suggests --no-install-recommends \
  locales \
  build-essential \
  file \
  gcc \
  clang \
  make \
  git \
  sudo \
  m4 \
  automake \
  autoconf \
  libtool \
  libtool-bin \
  help2man \
  ipython3 \
  oprofile \
  python3-yaml \
  python3.8 \
  sloccount \
  texlive-latex-extra \
  texlive-science \
  texlive-fonts-recommended \
  texlive-fonts-extra \
  tex-gyre \
  latexmk \
  hevea

# Create test user and the environment
RUN adduser "${TEST_USER}"
WORKDIR "${WORK_DIR}"
COPY . .
RUN chown -R "${TEST_USER}:${TEST_USER}" "${WORK_DIR}"

# Set up and select a Unicode locale
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Enable sudo without password for convenience.
RUN echo "${TEST_USER} ALL = NOPASSWD: ALL" >> /etc/sudoers

USER "${TEST_USER}"
