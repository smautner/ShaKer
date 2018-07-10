from rna_tools import shexec
import re


import rna_tools
def rnasubopt(sequence, return_energy=False):
        """call rnasubopt, return (dotbracket, energy)"""
        #print "echo " + "%s" % sequence + " | RNAsubopt -p 60 --maxBPspan=150"

        d={}
        if len(sequence) > 300:
            d = rna_tools.loadfile(".rnasubopt_cache")
            if sequence in d:
                return d[sequence] if return_energy else d[sequence][0]
        retcode, err, out = shexec("echo " + "%s" % sequence + " | RNAsubopt -p 60 --maxBPspan=150")
        energy = re.findall(r"[-+]?[0-9]*\.?[0-9]+", out)
        shape = [a.strip() for a in re.findall(r'\n[.()]+', out)]

        if len(sequence) > 300:
            d[sequence]= (shape, energy)
            rnasubopt.dumpfile(d,".rnasubopt_cache")

        if return_energy:
            return shape, energy
        else:
            return shape