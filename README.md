# Michael Glukhman's BCI

Michael Glukhman's project for Advanced System Design

## Installation and deployment
run the following commands to install dependencies and enter the virtual environment:

1. Clone the repository and enter it:

    ```sh
    git clone git@github.com:advanced-system-design/project-304366891.git
    cd project-304366891/
    ```

2. Run the installation script and activate the virtual environment:

    ```sh
    ./scripts/install.sh    
    source .env/bin/activate  
    ...
    [Mike`s BCI] $    # you're good to go!
    ```

    To use the standard message queue and database, run:

    ```
    docker run -d --name rabbit -p 5672:5672 rabbitmq
    docker run -d --name mongo -p 27017:27017 mongo
    ```

3. To check that everything is working as expected, run the tests:

    ```sh
    pytest tests/
    ```

## Project overview

#### TODO: flowchart + short description

## The client

The client exposes the following Python API:

```pycon
from bci.client import upload_sample
upload_sample(host='127.0.0.1', port=8000, path='sample.mind.gz')
```
where `host` is the IP address or hostname of the server, `port` is the port on which the server communicates
and `path` is the relative or absolute path to a snapshots file;

And the following CLI:

```sh
python -m bci.client upload-sample -h/--host '127.0.0.1' -p/--port 8000 'snapshot.mind.gz'
```
with the same arguments.

The supported snapshots file format is a gzipped binary packed with Google&apos;s
<a href="https://developers.google.com/protocol-buffers/docs/proto3">Protobuf 3</a> format.
The structure of a correct snapshots file is:
...

#### TODO: how to add readers for snapshot


## The server

The server exposes the following Python API:

```pycon
from bci.server import run_server
run_server(host='127.0.0.1', port=8000, publish=<i>publisher_name</i>)
```
where `host` is the IP address or hostname of the server, `port` is the port on which the server communicates
and `publish` is the name of the publishing module the server uses (currently, only <i>rabbitmq</i> is supported);


And the following CLI:

```sh
python -m bci.server run-server -h/--host '127.0.0.1' -p/--port 8000 'rabbitmq://127.0.0.1:5672/'
```
where `host` and `port` are the same as above, while the last argument is the address (IP:port) of
the message queue, preceded by the protocol used (currently, only <i>rabbitmq</i> is supported).

In order to add custom publisher modules, put a file named <i>publisher_name</i>.py in the
`bci/publishers` directory, containing the following method:
```pycon
def publish(message, msg_type, user_id, **kwargs):
    # your publishing code here
```
A module named <i>publisher_name</i> will become available for use as the `publish=` argument in
the <i>run_server</i> python API above.

## The message queue

...TODO...

## The parsers

Each parser exposes the following Python API:

```pycon
from bci.parsers import run_parser
result = run_parser(<i>parser_name</i>, <i>raw_data_path</i>)
```
which accepts a parser name and the path to a raw data file (as consumed from
the message queue), and returns the result (as published to the message queue);

And the following CLI:

```sh
python -m bci.parsers parse '<i>parser_name</i>' '<i>raw_data_path</i>' > '<i>parsed_data_path</i>'
```
which accepts a parser name and the path to a raw data file (as consumed from
the message queue), and prints the result (as published to the message queue) or
redirects it to a result file as in the example above.

A parsing service continuously consuming from the message queue is available by:

```sh
python -m bci.parsers run-parser '<i>parser_name</i>' 'rabbitmq://127.0.0.1:5672/'
```
where the last argument is the address (IP:port) of the message queue,
preceded by the protocol used (currently, only <i>rabbitmq</i> is supported).

Parsers currently available are:
- feelings
- pose
- color_image
- depth_image
#### TODO: say something about what each one does

In order to add custom parser modules, put a file named <i>parser_name</i>.py in the
`bci/parsing` directory, containing the following:
```pycon
from ..parsers import BasicParser

class MyParser(BasicParser):
    def parse(self, raw_snapshot_path):
        # your parsing code here, generating some savable result
        return result

parser_cls = MyParser
```
A parser named <i>parser_name</i> will become available for use in the Python API and CLI above.

## The saver



## The database

## The API server

## The CLI (command line interface)

## The GUI (graphical user interface)
