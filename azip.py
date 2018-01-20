#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""
from collections import namedtuple

from binary import BinaryPacker, BinaryUnpacker


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

    packer.i_32(len(plaintext))
    pack_table(table, packer)

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


def decompress(ciphertext):
    unpacker = BinaryUnpacker(ciphertext)

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


if __name__ == '__main__':
    # data = 'abbcccñÑẚ'
    data = 'abbcccc'

    compressed = compress(data)
    print(compressed)

    with open('out.txt', 'wb') as file_handle:
        file_handle.write(compressed)

    with open('out.txt', 'rb') as file_handle:
        byte_array = file_handle.read()

    decompressed = decompress(byte_array)
    print(decompressed)
