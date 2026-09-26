"""Test-support: build a minimal but REAL ELF64 shared object carrying a
``.dynsym`` / ``.dynstr`` with the given exported symbols.

Used by the S1 adversarial suites so that the native verifier's actual-binary
inspection (ELF architecture + dynamic export surface) is exercised against
genuine section tables rather than stubbed symbol readers. Not a build input.
"""

import struct

EM_AARCH64 = 183
EM_X86_64 = 62

_SHT_NULL, _SHT_DYNSYM, _SHT_STRTAB = 0, 11, 3
_SHF_ALLOC = 2


def _shdr(name, sh_type, flags, offset, size, link=0, info=0, align=1, entsize=0):
    return struct.pack("<IIQQQQIIQQ", name, sh_type, flags, 0, offset, size, link, info, align, entsize)


def fake_elf_so(e_machine, exports, payload=b""):
    """Return bytes of an ELF64-LE ET_DYN object whose .dynsym defines every
    name in ``exports`` as a GLOBAL FUNC symbol. ``payload`` is appended
    after the section table so distinct fixtures hash differently."""
    exports = sorted(set(exports))
    dynstr = b"\x00" + b"".join(s.encode() + b"\x00" for s in exports)
    name_off, syms = 1, [struct.pack("<IBBHQQ", 0, 0, 0, 0, 0, 0)]
    for s in exports:
        # st_info = (STB_GLOBAL << 4) | STT_FUNC ; st_shndx = 1 (defined)
        syms.append(struct.pack("<IBBHQQ", name_off, 0x12, 0, 1, 0x1000 + 16 * len(syms), 16))
        name_off += len(s) + 1
    dynsym = b"".join(syms)
    shstrtab = b"\x00.dynsym\x00.dynstr\x00.shstrtab\x00"
    n_dynsym, n_dynstr, n_shstr = 1, 9, 17

    off = 64
    dynsym_off = off
    off += len(dynsym)
    dynstr_off = off
    off += len(dynstr)
    shstr_off = off
    off += len(shstrtab)
    off += (-off) % 8
    shoff = off

    shdrs = b"".join([
        _shdr(0, _SHT_NULL, 0, 0, 0),
        _shdr(n_dynsym, _SHT_DYNSYM, _SHF_ALLOC, dynsym_off, len(dynsym), link=2, info=1, align=8, entsize=24),
        _shdr(n_dynstr, _SHT_STRTAB, _SHF_ALLOC, dynstr_off, len(dynstr)),
        _shdr(n_shstr, _SHT_STRTAB, 0, shstr_off, len(shstrtab)),
    ])
    e_ident = b"\x7fELF" + bytes([2, 1, 1, 0]) + b"\x00" * 8
    header = e_ident + struct.pack("<HHIQQQIHHHHHH",
                                   3, e_machine, 1, 0, 0, shoff, 0, 64, 0, 0, 64, 4, 3)
    body = bytearray(header + dynsym + dynstr + shstrtab)
    body += b"\x00" * (shoff - len(body))
    body += shdrs
    return bytes(body) + payload


def fake_elf_header_only(e_machine):
    """A 64-byte ELF header with no section table — the 'placeholder' shape
    that must NOT be accepted by an actual-binary verifier."""
    b = bytearray(64)
    b[0:4] = b"\x7fELF"
    b[4] = 2
    b[5] = 1
    struct.pack_into("<H", b, 18, e_machine)
    return bytes(b)
