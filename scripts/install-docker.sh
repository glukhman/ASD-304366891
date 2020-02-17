#!/bin/bash

set -e
cd "$(dirname "${BASH_SOURCE[0]}")/.."


function main {
    pip install -U pip
    pip install -U Sphinx
    pip install -r requirements.txt
    pip install grpcio grpcio-tools   # install protobuf compiler

    # compile the cortex protobuf format
    python -m grpc.tools.protoc -I=bci --python_out=bci --grpc_python_out=bci bci/utils/protobuf/cortex.proto
}

main "$@"
