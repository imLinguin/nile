# FUEL_PATCH patcher
# https://github.com/derrod/twl.py/blob/master/src/patching.py
import logging
import zstandard as zstd

from enum import Enum

logger = logging.getLogger('PATCHER')


class Instructions(Enum):
    Seek = 0
    Copy = 1
    Insert = 2
    Merge = 3


class PatchCompression(Enum):
    NONE = 0  # nothing
    ZSTD = 1  # zstandard


class Patcher:
    """
    Patcher to apply FUEL_PATCH patches
    Written based on reference in Twitch App, so not perfectly pythonic
    """

    def __init__(self, source_fp, patch_fp, target_fp, block_size=1024*1024):
        self._source = source_fp
        self._patch = patch_fp
        self._patch_raw = None
        self._target = target_fp
        self.block_size = block_size  # work on data in 1 MiB blocks

    def run(self):
        patch_compression = PatchCompression(int.from_bytes(self._patch.read(1), byteorder='big'))
        if patch_compression == PatchCompression.ZSTD:
            logger.debug('Delta patch is zstandard compressed')
            dctx = zstd.ZstdDecompressor()
            self._patch_raw = self._patch
            with dctx.stream_reader(self._patch_raw) as zreader:
                self._patch = zreader
                self.apply_patches()
        else:
            logger.debug('Delta patch is not compressed')
            self.apply_patches()

        # close files
        self._patch.close()
        if self._patch_raw:
            self._patch_raw.close()
        self._source.close()
        self._target.close()

    def apply_patches(self):
        while True:
            try:
                instruction, length = self.read_instruction()
                self.apply_instruction(instruction, length)
            except EOFError:
                break
            except Exception as e:
                print(repr(e))
                break

    def read_instruction(self):
        next_byte = self._patch.read(1)
        if not next_byte:
            raise EOFError

        patch_start_byte = int.from_bytes(next_byte, byteorder='big')
        instruction = Instructions(patch_start_byte >> 6)
        bit_count = 5 if instruction == Instructions.Seek else 6
        length = self.get_length(patch_start_byte, bit_count)
        if instruction == instruction.Seek and patch_start_byte & 32:
            length *= -1
        return instruction, length

    def get_length(self, encoded_length, bit_count):
        bitmask = 2**bit_count - 1
        length = encoded_length & bitmask
        if length < (bitmask - 4):
            return length + 1
        else:
            byte_count = length - (bitmask - 5)
            length = int.from_bytes(self._patch.read(byte_count), byteorder='big')
            return length + 1

    def apply_instruction(self, instruction, length):
        if instruction == Instructions.Seek:
            # logger.debug(f'Seek {length}')
            self._source.seek(length, 1)
        elif instruction == Instructions.Copy:
            # logger.debug(f'Copy {length}')
            self.copy(self._source, self._target, length)
        elif instruction == Instructions.Insert:
            # logger.debug(f'Insert {length}')
            self.copy(self._patch, self._target, length)
        elif instruction == Instructions.Merge:
            # logger.debug(f'Merge {length}')
            self.merge(length)

    def copy(self, source, target, length):
        while length > 0:
            target.write(source.read(min(self.block_size, length)))
            length -= self.block_size

    def merge(self, length):
        while length > 0:
            source_buffer = self._source.read(min(self.block_size, length))
            if not source_buffer:
                raise ValueError('Merge length is longer than source')

            patch_buffer = self._patch.read(min(self.block_size, length))
            if not patch_buffer:
                raise ValueError('Merge length is longer than patch')

            if len(patch_buffer) != len(source_buffer):
                raise ValueError('Patch and Source do not have same length!')

            for s, p in zip(source_buffer, patch_buffer):
                result = (s + p) % 2**8
                self._target.write(result.to_bytes(1, byteorder='big'))

            length -= self.block_size