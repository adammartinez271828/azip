#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""
from collections import namedtuple

from bin import BinaryPacker, BinaryUnpacker


Node = namedtuple('Node', ('left', 'right', 'count'))
Leaf = namedtuple('Leaf', ('ordinal', 'count'))
TableRow = namedtuple('TableRow', ('ordinal', 'bits'))


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


def compress(plaintext):
    tree = build_tree(data)
    table = build_table(tree)
    packer = BinaryPacker()

    packer.i_32(len(plaintext) - 1)

    for ordinal in [ord(character) for character in plaintext]:
        bits = look_up_ordinal(table, ordinal)
        packer.binary(bits)

    return packer.pack()


def look_up_bits(table, unpacker):
    for row in table:
        if row.bits == unpacker.peek(len(row.bits)):
            unpacker.binary(len(row.bits))
            return row.ordinal

    raise RuntimeError('Couldn\'t match next bits!')


def decompress(table, ciphertext):
    unpacker = BinaryUnpacker(ciphertext)

    data_length = unpacker.i_32()

    return ''.join([chr(look_up_bits(table, unpacker)) for _ in range(data_length + 1)])


if __name__ == '__main__':
    # data = 'abbcccñÑẚ'
    data = 'abbcccc'

    compressed = compress(data)
    print(compressed)
    decompressed = decompress(build_table(build_tree(data)), compressed)
    print(decompressed)
