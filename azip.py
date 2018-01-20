#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Custom, Python-based compressor

Requires FILE argument OR input from stream.

Don't use this for real.

Usage:
    azip (--compress | --expand) [FILE] [--out=OUT]
    azip -h | --help
    azip --version

ARGS:
    FILE                A file

Options:
    -c, --compress
    -x, --expand
    -o OUT, --out=OUT   Write output to file instead of stdout.
    -h, --help          Show this screen.
    --version           Show version.
"""
from collections import namedtuple
from enum import Enum
import sys

from docopt import docopt

from binary import BinaryPacker, BinaryUnpacker


class FileMode(Enum):
    READ_BINARY = 1
    READ_UNICODE = 2
    WRITE_BINARY = 3
    WRITE_UNICODE = 4


Node = namedtuple('Node', ('left', 'right', 'count'))
Leaf = namedtuple('Leaf', ('ordinal', 'count'))
TableRow = namedtuple('TableRow', ('ordinal', 'bits'))

VERSION = """azip 1.0.0"""


def build_tree(characters):
    """Build a tree of Nodes from a string

    Args:
        characters (str)
    Returns:
        [Node]
    """
    nodes = []
    ordinals = [ord(char) for char in characters]
    unique_ordinals = set(ordinals)

    nodes = [Leaf(ordinal, ordinals.count(ordinal))
             for ordinal in unique_ordinals]

    while len(nodes) > 1:
        nodes = sorted(nodes, key=lambda x: x.count, reverse=True)
        node1 = nodes.pop()
        node2 = nodes.pop()
        nodes.append(Node(node1, node2, node1.count + node2.count))

    return nodes[0]


def build_table(node, path=None):
    path = [] if path is None else path

    if isinstance(node, Node):
        return build_table(node.left, path + [0]) + \
            build_table(node.right, path + [1])
    return [TableRow(node.ordinal, path)]


def look_up_ordinal(table, ordinal):
    for row in table:
        if row.ordinal == ordinal:
            return row.bits
    raise RuntimeError('Bits lookup failed for {}'.format(ordinal))


def compress(data):
    tree = build_tree(data)
    table = build_table(tree)
    packer = BinaryPacker()

    packer.i_32(len(data))
    pack_table(table, packer)

    for ordinal in [ord(character) for character in data]:
        bits = look_up_ordinal(table, ordinal)
        packer.binary(bits)

    return packer.pack()


def look_up_bits(table, unpacker):
    for row in table:
        if row.bits == unpacker.peek(len(row.bits)):
            unpacker.binary(len(row.bits))
            return row.ordinal

    raise RuntimeError('Couldn\'t match next bits!')


def decompress(data):
    unpacker = BinaryUnpacker(data)

    data_length = unpacker.i_32()

    table = unpack_table(unpacker)

    return ''.join([chr(look_up_bits(table, unpacker)) for _ in range(data_length)])


def pack_table(table, packer):
    packer.i_16(len(table) - 1)
    for row in table:
        packer.i_16(row.ordinal)
        packer.i_16(len(row.bits))
        packer.binary(row.bits)


def unpack_table(unpacker):
    table_length = unpacker.i_16()

    table_rows = []
    for _ in range(table_length + 1):
        ordinal = unpacker.i_16()
        num_bits = unpacker.i_16()
        bits = list(map(int, unpacker.binary(num_bits)))
        table_rows.append(TableRow(ordinal, bits))

    return table_rows


def read(target=None, read_mode=FileMode.READ_UNICODE):
    if target is None:
        buff = sys.stdin.buffer if read_mode is FileMode.READ_BINARY else sys.stdin
        return buff.read()
    else:
        mode = 'rb' if read_mode is FileMode.READ_BINARY else 'r'
        with open(target, mode) as file_handle:
            return file_handle.read()


def write(data, target=None, write_mode=FileMode.WRITE_UNICODE):
    if target is None:
        buff = sys.stdout.buffer if write_mode is FileMode.WRITE_BINARY else sys.stdout
        buff.write(data)
    else:
        mode = 'wb' if write_mode is FileMode.WRITE_BINARY else 'w'
        with open(target, mode) as file_handle:
            file_handle.write(data)


if __name__ == '__main__':
    ARGS = docopt(__doc__, version=VERSION)

    if ARGS['--compress']:
        READ_MODE = FileMode.READ_UNICODE
        WRITE_MODE = FileMode.WRITE_BINARY
        FUNCTION = compress
    elif ARGS['--expand']:
        READ_MODE = FileMode.READ_BINARY
        WRITE_MODE = FileMode.WRITE_UNICODE
        FUNCTION = decompress

    DATA = read(ARGS['FILE'], READ_MODE)
    OUTPUT = FUNCTION(DATA)
    write(OUTPUT, ARGS['--out'], WRITE_MODE)
