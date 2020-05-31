docker build -t cortex .
docker network create -d bridge cortex
docker run --net cortex -d --name qd_rabbit -p 5672:5672 rabbitmq:3-management
docker run --net cortex -d --name qd_mongo -p 27017:27017 mongo
docker run --net cortex -d --name qd_server -v shared_data:/data -p 5000:5000 cortex python -m bci.server run-server -h '0.0.0.0' -p 5000 'rabbitmq://qd_rabbit:5672/'
docker run --net cortex -d --name qd_parse_pose -v shared_data:/data cortex python -m bci.parsers run-parser 'pose' 'rabbitmq://qd_rabbit:5672'
docker run --net cortex -d --name qd_parse_feelings -v shared_data:/data cortex python -m bci.parsers run-parser 'feelings' 'rabbitmq://qd_rabbit:5672'
docker run --net cortex -d --name qd_parse_color -v shared_data:/data cortex python -m bci.parsers run-parser 'color_image' 'rabbitmq://qd_rabbit:5672'
docker run --net cortex -d --name qd_parse_depth -v shared_data:/data cortex python -m bci.parsers run-parser 'depth_image' 'rabbitmq://qd_rabbit:5672'
docker run --net cortex -d --name qd_saver -v shared_data:/data cortex python -m bci.saver run-saver 'mongodb://qd_mongo:27017' 'rabbitmq://qd_rabbit:5672'
docker run --net cortex -d --name qd_api -v shared_data:/data -p 8000:8000 cortex python -m bci.api run-server -h '0.0.0.0' -d 'mongodb://qd_mongo:27017'
docker run --net cortex -d --name qd_gui -v shared_data:/data -p 8080:8080 cortex python -m bci.gui run-server -h '0.0.0.0' -H 'qd_api'
