import subprocess

from docutils import nodes

# deprecated
# from sphinx.util.compat import Directive
from docutils.parsers.rst import Directive
from sphinx.directives.code import LiteralInclude

example_dir = '/../../example/manual/'

class IncludeExample(LiteralInclude):
    def run(self):
        self.arguments[0] = '{}/{}'.format(example_dir, self.arguments[0])
        return super(IncludeExample, self).run()

class RunExample(Directive):
    has_content = False
    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        document = self.state.document
        env = document.settings.env
        _ , wd = env.relfn2path(example_dir)
        prog = self.arguments[0]
        out = subprocess.check_output(['python3', '-u', prog], cwd=wd, 
                                      stderr=subprocess.STDOUT,
                                      universal_newlines=True)
        out = '$ python {}\n{}'.format(prog, out)
        ret = [nodes.literal_block(out, out)]
        return ret


def setup(app):
    app.add_directive('include-example', IncludeExample)
    app.add_directive('run-example', RunExample)
