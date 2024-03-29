# Copyright (c) 2015, Open Source Robotics Foundation, Inc.
# Copyright (c) 2013, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Open Source Robotics Foundation, Inc.
#       nor the names of its contributors may be used to endorse or promote
#       products derived from this software without specific prior
#       written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Authors: Stuart Glaser, William Woodall, Robert Haschke
# Maintainer: Morgan Quigley <morgan@osrfoundation.org>

import textwrap
from optparse import OptionParser, IndentedHelpFormatter
from xacro.color import colorize, warning, message


class ColoredOptionParser(OptionParser):
    def error(self, message):
        msg = colorize(message, 'red')
        OptionParser.error(self, msg)


_original_wrap = textwrap.wrap


def wrap_with_newlines(text, width, **kwargs):
    result = []
    for paragraph in text.split('\n'):
        result.extend(_original_wrap(paragraph, width, **kwargs))
    return result


class IndentedHelpFormatterWithNL(IndentedHelpFormatter):
    def __init__(self, *args, **kwargs):
        IndentedHelpFormatter.__init__(self, *args, **kwargs)

    def format_option(self, text):
        textwrap.wrap, old = wrap_with_newlines, textwrap.wrap
        result = IndentedHelpFormatter.format_option(self, text)
        textwrap.wrap = old
        return result


# copied from rosgraph.names
REMAP = ":="


def load_mappings(argv):
    """
    Load name mappings encoded in command-line arguments. This will filter
    out any parameter assignment mappings.

    @param argv: command-line arguments
    @type  argv: [str]
    @return: name->name remappings.
    @rtype: dict {str: str}
    """
    mappings = {}
    for arg in argv:
        if REMAP in arg:
            try:
                src, dst = [x.strip() for x in arg.split(REMAP)]
                if src and dst:
                    if len(src) > 1 and src[0] == '_' and src[1] != '_':
                        # ignore parameter assignment mappings
                        pass
                    else:
                        mappings[src] = dst
            except Exception:
                raise RuntimeError("Invalid remapping argument '%s'\n" % arg)
    return mappings


def process_args(argv, require_input=True):
    parser = ColoredOptionParser(usage="usage: %prog [options] <input>",
                                 formatter=IndentedHelpFormatterWithNL())
    parser.add_option("-o", dest="output", metavar="FILE",
                      help="write output to FILE instead of stdout")
    parser.add_option("--distro", "-d", dest="distro", help="ROS distro")
    parser.add_option("--repo", "-r", dest="repo", help="Github repo link where the URDF (xacro) file is located")
    parser.add_option("--branch", "-b", dest="branch", help="Github repo branch where the URDF (xacro) file is located")
    parser.add_option("--package", "-p", dest="package", help="ROS package to which the URDF (xacro) file belongs")
    parser.add_option("--version", "-n", dest="version", help="Git version of URDF (xacro) file")
    parser.add_option("--category", "-c", dest="category", help="Category of the component")
    parser.add_option("--push_to_db", "-u", dest="db", help="Push parsed component to DB")

    # verbosity options
    parser.add_option("-q", action="store_const", dest="verbosity", const=0,
                      help="quiet operation, suppressing warnings")
    parser.add_option("-v", action="count", dest="verbosity",
                      help="increase verbosity")
    parser.add_option("--verbosity", metavar='level', dest="verbosity", type='int',
                      help=textwrap.dedent("""\
                      set verbosity level
                      0: quiet, suppressing warnings
                      1: default, showing warnings and error locations
                      2: show stack trace
                      3: log property definitions and usage on top level
                      4: log property definitions and usage on all levels"""))

    # process substitution args
    try:
        mappings = load_mappings(argv)
        # filter-out REMAP args
        filtered_args = [a for a in argv if REMAP not in a]
    except ImportError as e:
        warning(e)
        mappings = {}
        filtered_args = argv

    parser.set_defaults(just_deps=False, verbosity=1)
    (options, pos_args) = parser.parse_args(filtered_args)

    if not options.output:
        parser.error('Output file must be provided')

    if not options.distro:
        parser.error('ROS distro has to be provided')

    if not options.repo:
        parser.error('Github repo of the xacro file has to be provided')

    if not options.branch:
        parser.error('Github repo branch of the xacro file has to be provided')

    if not options.package:
        parser.error('ROS package of the xacro file must be provided')

    if not options.version:
        parser.error('Git version of the xacro file must be provided')

    if len(pos_args) != 1:
        if require_input:
            parser.error("expected exactly one input file as argument")
        else:
            pos_args = [None]

    options.mappings = mappings
    return options, pos_args[0]
