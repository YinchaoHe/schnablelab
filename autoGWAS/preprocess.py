# -*- coding: UTF-8 -*-

"""
Convert GWAS dataset to particular formats for GEMMA, GAPIT, FarmCPU, and MVP.
"""

import os.path as op
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser
from JamesLab.apps.slurmhead import SlrumHeader

def main():
    actions = (
        ('hmp2BIMBAM', 'transform hapmap format to BIMBAM format'),
        ('hmp2numeric', 'transform hapmap format to numeric format'),
        ('hmp2MVP', 'transform hapmap format to MVP format')
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def judge(ref, alt, genosList):
    newlist = []
    for k in j[11:]:
        #if len(set(k))==1 and k[0] == ref:
        if k=='AA':
            nums.append('0')
        #elif len(set(k))==1 and k[0] == alt:
        elif k=='BB':
            nums.append('2')
        #elif len(set(k))==2 :
        elif k=='AB' :
            nums.append('1')
        else:
            print 'genotype error !'
    return newlist

def hmp2BIMBAM(args):
    """
    %prog hmp bimbam_prefix
    
    Convert hmp genotypic data to bimnbam datasets (*.mean and *.annotation).
    """
    p = OptionParser(hmp2BIMBAM.__doc__)
    opts, args = p.parse_args(args)
    
    if len(args) == 0:
        sys.exit(not p.print_help())
    
    hmp, bim_pre = args
    f1 = open(hmp)
    f1.readline()
    f2 = open(bim_pre+'.mean', 'w')
    f3 = open(bim_pre+'.annotation', 'w')
    for i in f1:
        j = i.split()
        rs = j[0]
        ref, alt = j[1].split('/')[0], j[1].split('/')[1]
        newNUMs = judge(ref, alt, j[11:])
        newline = '%s,%s,%s,%s\n'%(rs, ref, alt, ','.join(newNUMs))
        f2.write(newline)
        pos = j[3]
        chro = j[2]
        f3.write('%s,%s,%s\n'%(rs, pos, chro))
    f1.close()
    f2.close()
    f3.close()

def hmp2numeric(args):
    """
    %prog hmp numeric_prefix
    
    Convert hmp genotypic data to numeric datasets (*.GD and *.GM).
    """
    p = OptionParser(hmp2BIMBAM.__doc__)
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())

    hmp, num_pre = args
    f1 = open(hmp)
    f2 = open(num_pre+'.GD', 'w')
    f3 = open(num_pre+'.GM', 'w')

    hmpheader = f1.readline()
    preConverted = []
    header = 'taxa\t%s'%('\t'.join(hmpheader.split()[11:]))
    preConverted.append(header.split())

    f3.write('SNP\tChromosome\tPosition\n')
    for i in f1:
        j = i.split()
        taxa,ref,alt,chro,pos = j[0],j[1][0],j[1][2],j[2],j[3]
        f3.write('%s\t%s\t%s\n'%(taxa, chro, pos))
        newNUMs = judge(ref, alt, j[11:])
        newline = '%s\t%s'%(taxa, '\t'.join(newNUMs))
        preConverted.append(newline.split())
    rightOrder = map(list, zip(*preConverted))
    for i in rightOrder:
        newl = '\t'.join(i)+'\n'
        f2.write(newl)
    f1.close()
    f2.close()

if __name__ == '__main__':
    main()
