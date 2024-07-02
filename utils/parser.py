import argparse
import re

version = ''
with open('./gatekeeper/__init__.py') as file:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', file.read(), re.MULTILINE).group(1)  # type:ignore


class Parser(argparse.ArgumentParser):
    # TODO: Finish docstring.
    """
    The ArgumentParser for Gatekeeper.
    *The %(prog)s format specifier is available to fill in the program name in your usage messages.
    """

    # TODO: Add epilog and finish description.
    def __init__(self, prog: str = f"Gatekeeper v{version}",
                 description: str = """A Discord Bot bringing AMP by Cubecoders to Discord with the
                 ability to interact and control Instances.(https://github.com/k8thekat/Gatekeeper)
                         """,
                 prefix_chars: str = "-",
                 epilog: str = "placeholder epilog for arg parse.") -> None:

        super().__init__(prog=prog,
                         description=description,
                         prefix_chars=prefix_chars,
                         epilog=epilog)
        self.add_argument("-t", help="This shows the programs name %(prog)s.")
        self.add_argument("-")


A = Parser()
A.print_help()
A.print_usage()
