# Michael Glukhman's BCI

Michael Glukhman's project for Advanced System Design

## Installation

1. Clone the repository and enter it:

    ```sh
    $ git clone git@github.com:advanced-system-design/project-304366891.git
    ...
    $ cd project-304366891/
    ```

2. Run the installation script and activate the virtual environment:

    ```sh
    $ ./scripts/install.sh
    ...
    $ source .env/bin/activate
    [Mike`s BCI] $    # you're good to go!
    ```

3. To check that everything is working as expected, run the tests:


    ```sh
    $ pytest tests/
    ...
    ```

## Usage

The `bci` package provides the class: `Thought`, `utils.Connection` and `utils.Listener`
Additionally, the `bci` package provides the following functions:

- `run_server`:
    This fuction runs a server which receives thoughts and stores them in a given directory, ordered by user ID.
    Arguments: ADDRESS [a tuple (host:port)], DATA [path to the data directory].

    ```pycon
    >>> from bci import run_server
    >>> run_server(('127.0.0.1', 5050), 'data/')
    ```

- `upload_thought`:
    This fuction runs a client which sends thoughts to the server.
    Arguments: ADDRESS [a tuple (host:port)], USER_ID [integer], THOUGHT [string].
    The address should match that of the server.

    ```pycon
    >>> from bci import upload_thought
    >>> upload_thought(('127.0.0.1', 5050), 12, 'thoughty little thought')
    ```

- `run_webserver`:
    This fuction runs a webserver which displays the content of the thoughts directory on the server, as a website.
    Arguments: ADDRESS [a tuple (host:port)], DATA [path to the data directory].

    ```pycon
    >>> from bci import run_webserver
    >>> run_webserver(('127.0.0.1', 8080), 'data/')
    ```

The `bci` package also provides a command-line interface:

```sh
$ python -m bci
Usage: bci [OPTIONS] COMMAND [ARGS]...
```

The CLI provides the `run-server`, `upload-thought` and `run-web` commands, with the same arguments as above:

```sh
$ python -m bci run-server 127.0.0.1:5050 data/
...
$ python -m bci upload-thought 127.0.0.1:5050 12 'thoughty little thought'
done
$ python -m bci run-web localhost:8080 data/
* Serving Flask app "bci.website.web" (lazy loading)
...
```
