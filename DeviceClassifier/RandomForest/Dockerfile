FROM cyberreboot/poseidonml:base
LABEL maintainer="Charlie Lewis <clewis@iqt.org>"

COPY . /RandomForest
COPY models /models
WORKDIR /RandomForest

ENTRYPOINT ["python3", "eval_RandomForest.py"]
