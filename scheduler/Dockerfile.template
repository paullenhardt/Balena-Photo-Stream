ARG BALENA_ARCH=%%BALENA_ARCH%%

FROM balenalib/$BALENA_ARCH-alpine
ARG BALENA_ARCH=%%BALENA_ARCH%%

COPY scripts /usr/src/
RUN chmod +x /usr/src/*.sh

CMD /usr/src/start.sh
