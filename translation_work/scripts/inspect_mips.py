"""Small read-only MIPS decoder for targeted PS2 analysis (standard library).

Unknown instructions remain .word; no claim of full R5900 decoding.
Addresses are ELF virtual addresses, translated through PT_LOAD headers.
"""
import argparse
import struct
from pathlib import Path

REG = 'zero at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra'.split()

def decode(w, pc):
    op, rs, rt, rd, sa, fn = w >> 26, (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31, (w >> 6) & 31, w & 63
    imm = w & 65535
    signed = imm if imm < 32768 else imm - 65536
    s, t, d = REG[rs], REG[rt], REG[rd]
    if w == 0: return 'nop'
    if op == 0:
        if fn in (0, 2, 3, 56, 58, 59, 60, 62, 63):
            name = {0:'sll',2:'srl',3:'sra',56:'dsll',58:'dsrl',59:'dsra',60:'dsll32',62:'dsrl32',63:'dsra32'}[fn]
            return f'{name} {d},{t},{sa}'
        if fn in (4, 6, 7): return f'{ {4:"sllv",6:"srlv",7:"srav"}[fn]} {d},{t},{s}'
        if fn == 8: return f'jr {s}'
        if fn == 9: return f'jalr {d},{s}'
        if fn in (10,11): return f'{"movz" if fn == 10 else "movn"} {d},{s},{t}'
        if fn in (16, 18): return f'{"mfhi" if fn == 16 else "mflo"} {d}'
        if fn in (24,25): return f'{"mult" if fn==24 else "multu"} {d},{s},{t} ; R5900 result also in rd'
        if fn in (26,27): return f'{"div" if fn==26 else "divu"} {s},{t}'
        if fn in (32,33,34,35,36,37,38,39,42,43,44,45,46,47):
            return f'{ {32:"add",33:"addu",34:"sub",35:"subu",36:"and",37:"or",38:"xor",39:"nor",42:"slt",43:"sltu",44:"dadd",45:"daddu",46:"dsub",47:"dsubu"}[fn]} {d},{s},{t}'
    if op in (2,3): return f'{"j" if op == 2 else "jal"} 0x{((pc+4)&0xf0000000)|((w&0x3ffffff)<<2):08X}'
    if op in (4,5,6,7,20,21,22,23):
        name={4:'beq',5:'bne',6:'blez',7:'bgtz',20:'beql',21:'bnel',22:'blezl',23:'bgtzl'}[op]
        return f'{name} {s},{t},0x{pc+4+signed*4:08X}'
    if op == 1:
        name={0:'bltz',1:'bgez',2:'bltzl',3:'bgezl',16:'bltzal',17:'bgezal'}.get(rt,'regimm')
        return f'{name} {s},0x{pc+4+signed*4:08X}'
    if op == 15: return f'lui {t},0x{imm:04X}'
    if op in (8,9,10,11,12,13,14,24,25):
        name={8:'addi',9:'addiu',10:'slti',11:'sltiu',12:'andi',13:'ori',14:'xori',24:'daddi',25:'daddiu'}[op]
        value=f'0x{imm:X}' if op in (12,13,14) else str(signed)
        return f'{name} {t},{s},{value}'
    if op in (30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,49,55,57,63):
        name={30:'lq',31:'sq',32:'lb',33:'lh',34:'lwl',35:'lw',36:'lbu',37:'lhu',38:'lwr',39:'lwu',40:'sb',41:'sh',42:'swl',43:'sw',44:'sdl',45:'sdr',46:'swr',49:'lwc1',55:'ld',57:'swc1',63:'sd'}[op]
        return f'{name} {t},{signed}({s})'
    return f'.word 0x{w:08X}'

class Elf:
    def __init__(self, path):
        self.data = Path(path).read_bytes()
        b=self.data
        if b[:6] != b'\x7fELF\x01\x01': raise ValueError('expected ELF32 little-endian')
        ph=struct.unpack_from('<I',b,28)[0]
        stride,count=struct.unpack_from('<HH',b,42)
        self.segments=[]
        for i in range(count):
            typ,off,va,_,size,mem,flags,align=struct.unpack_from('<8I',b,ph+i*stride)
            if typ==1: self.segments.append((off,va,size))
    def offset(self, va):
        for off,start,size in self.segments:
            if start <= va < start+size: return off+va-start
        raise ValueError(f'unmapped VA {va:X}')
    def word(self, va): return struct.unpack_from('<I',self.data,self.offset(va))[0]
    def disasm(self, start, size):
        return '\n'.join(f'{pc:08X} file={self.offset(pc):08X} {self.word(pc):08X}  {decode(self.word(pc),pc)}' for pc in range(start,start+size,4))+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--elf',default='decompile/SLPM_621.12')
    p.add_argument('--start',type=lambda s:int(s,0),required=True)
    p.add_argument('--size',type=lambda s:int(s,0),default=0x200)
    p.add_argument('--output',type=Path)
    a=p.parse_args(); result=Elf(a.elf).disasm(a.start,a.size)
    if a.output:
        root=Path('translation_work').resolve()
        if not a.output.resolve().is_relative_to(root): raise ValueError('output must be under translation_work')
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(result,encoding='utf-8')
    else: print(result,end='')
