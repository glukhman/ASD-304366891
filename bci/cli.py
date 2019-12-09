import sys, inspect

class CommandLineInterface:
    commands = {}

    def command(self, f):
        self.commands[f.__name__] = f, inspect.getfullargspec(f).args

    def main(self):
        if len(sys.argv)<2 or \
            sys.argv[1] not in self.commands:
            print(f'USAGE:    python {sys.argv[0]} <command> [<key>=<value>]*')
            print('COMMANDS:', ', '.join(self.commands))
            exit(1)
        command = sys.argv[1]
        function, signature = self.commands[command]
        kwargs = [arg.split('=') for arg in sys.argv[2:]]
        try:
            kwargs = {key:val for key,val in kwargs}
            assert [*kwargs] == signature
        except (ValueError, AssertionError):
            printable_signatue = ' '.join(f'{key}=<value>' for key in signature)
            print(f'USAGE:    python {sys.argv[0]} {command} {printable_signatue}')
            exit(1)
        function(**kwargs)
