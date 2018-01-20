#!/usr/bin/env python
# -*- coding: utf-8 -*-
from itertools import chain, islice


def partition(iterable, n):
    iterator = iter(iterable)

    subpartition = list(islice(iterator, n))
    while subpartition:
        yield subpartition
        subpartition = list(islice(iterator, n))


class BinaryPacker:
    def __init__(self):
        self.bits = []

    def i_32(self, integer):
        self.i_n(integer, 32)

    def i_16(self, integer):
        self.i_n(integer, 16)

    def i_8(self, integer):
        self.i_n(integer, 8)

    def i_n(self, integer, num_bits):
        self.binary(list(map(int, self.to_bin(integer, num_bits)))[::-1])

    def binary(self, bits):
        self.bits.append(bits)

    @staticmethod
    def to_bin(integer, num_bits):
        fmt_str = '0{}b'.format(num_bits)
        return format(integer, fmt_str)

    def pack(self):
        byte_array = bytearray()

        bitstring = chain.from_iterable(self.bits)
        for group in partition(bitstring, 8):
            bitstring = ''.join(map(str, group))[::-1]
            byte_array.append(int(bitstring, 2))

        return byte_array

    def __str__(self):
        byte_info = []

        bitstring = chain.from_iterable(self.bits)
        for group in partition(bitstring, 8):
            byte = ''.join(list(map(str, group))).ljust(8, '0')[::-1]
            value = int(byte, 2)
            ordinal = format(value, '#04x')

            byte_info.append(
                '{0} | {1:3} | "{2}"'.format(byte, value, ordinal))

        return '\n  '.join(['BinaryPacker:'] + byte_info)


class BinaryUnpacker:
    def __init__(self, packed_str):
        raw_bits = ''.join(format(ord, '08b') for ord in packed_str)
        self.bits = ''.join(''.join(group[::-1])
                            for group in partition(raw_bits, 8))

    def popnleft(self, n):
        _bits, self.bits = self.bits[:n], self.bits[n:]
        return _bits

    def i_32(self):
        bitstring = self.popnleft(32)[::-1]
        return int(bitstring, 2)

    def i_16(self):
        bitstring = self.popnleft(16)[::-1]
        return int(bitstring, 2)

    def i_8(self):
        bitstring = self.popnleft(8)[::-1]
        return int(bitstring, 2)

    def binary(self, n):
        return list(self.popnleft(n))

    def peek(self, n):
        return list(map(int, self.bits[:n]))
