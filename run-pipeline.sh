docker build -t cortex .
docker network create -d bridge cortex
docker run --net cortex -d --name rabbit -p 5672:5672 rabbitmq:3-management
docker run --net cortex -d --name mongo -p 27017:27017 mongo
docker run --net cortex -d --name server -v shared_data:/data -p 5000:5000 cortex python -m bci.server run-server -h '0.0.0.0' -p 5000 'rabbitmq://rabbit:5672/'
docker run --net cortex -d --name parse_pose -v shared_data:/data cortex python -m bci.parsers run-parser 'pose' 'rabbitmq://rabbit:5672'
docker run --net cortex -d --name parse_feelings -v shared_data:/data cortex python -m bci.parsers run-parser 'feelings' 'rabbitmq://rabbit:5672'
docker run --net cortex -d --name parse_color -v shared_data:/data cortex python -m bci.parsers run-parser 'color_image' 'rabbitmq://rabbit:5672'
docker run --net cortex -d --name parse_depth -v shared_data:/data cortex python -m bci.parsers run-parser 'depth_image' 'rabbitmq://rabbit:5672'
docker run --net cortex -d --name saver -v shared_data:/data cortex python -m bci.saver run-saver 'mongodb://mongo:27017' 'rabbitmq://rabbit:5672'
docker run --net cortex -d --name api -v shared_data:/data -p 8000:8000 cortex python -m bci.api run-server -h '0.0.0.0' -d 'mongodb://mongo:27017'
docker run --net cortex -d --name gui -v shared_data:/data -p 8080:8080 cortex python -m bci.gui run-server -h '0.0.0.0' -H 'api'
