#!/bin/bash

set -e
cd "$(dirname "${BASH_SOURCE[0]}")/.."


function main {
    python -m virtualenv .env --prompt "[Mike's BCI] "
    find .env -name site-packages -exec bash -c 'echo "../../../../" > {}/self.pth' \;
    .env/bin/pip install -U pip
    .env/bin/pip install -U Sphinx
    .env/bin/pip install -r requirements.txt
    .env/bin/pip install grpcio grpcio-tools   # install protobuf compiler

    # compile the cortex protobuf format
    .env/bin/python -m grpc.tools.protoc -I=bci --python_out=bci --grpc_python_out=bci bci/utils/protobuf/cortex.proto

    # run rabbitmq docker container
    sudo docker run -d --network host --hostname myrabbit --name myrabbit -p 5672:5672 -p 15672:15672 rabbitmq:3-management
}

main "$@"
