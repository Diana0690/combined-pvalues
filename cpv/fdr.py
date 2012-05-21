"""
perform Benjamini-Hochberg FDR correction on a BED file with p-values.
"""
import argparse
from _common import bediter
from itertools import izip
from _common import get_col_num
import numpy as np

def run(args):
    # get rid of N, just keep the correlation.
    col_num = get_col_num(args.c)
    if args.qvality:
        col_null = get_col_num(args.null)
        for qval, pep, l in _qvality(args.bed_file, col_num, col_null):
            print "%s\t%.4g\t%4g" % (l.rstrip("\r\n"), qval, pep)
    elif args.null:
        col_null = get_col_num(args.null)
        for qval, l in obs_fdr(args.bed_file, col_num, col_null):
            print "%s\t%.4g" % (l.rstrip("\r\n"), qval)
    else:
        for bh, l in fdr(args.bed_file, col_num):
            print "%s\t%.4g" % (l.rstrip("\r\n"), bh)

def _qvality(fbed_file, col_num, col_null):
   from qvality import qvality

   ps = [b['p'] for b in bediter(fbed_file, col_num)]
   nulls = [b['p'] for b in bediter(fbed_file, col_null)]
   fh = open(fbed_file)
   drop_header(fh)
   for (pval, pep, qval), l in izip(qvality(ps, nulls, r=None), fh):
       yield qval, pep, l

def obs_fdr(fbed_file, col_num, col_null):
   ps = [b['p'] for b in bediter(fbed_file, col_num)]
   nulls = [b['p'] for b in bediter(fbed_file, col_null)]
   fh = open(fbed_file)
   drop_header(fh)
   for qval, l in izip(relative_fdr(ps, nulls), fh):
       yield qval, l

# TODO (if null is None: null = 1 / np.arange(len(observed))
def relative_fdr(observed, null):
    observed = np.asarray(observed)
    null = np.asarray(null)

    obs_sort_ind = np.argsort(observed)
    observed = observed[obs_sort_ind]
    obs_unsort_ind = obs_sort_ind.argsort()

    null.sort()

    corrected = observed / null
    corrected = np.minimum.accumulate(corrected[::-1])[::-1]
    corrected[corrected > 1] = 1
    return corrected[obs_unsort_ind]

def drop_header(fh):
    line = fh.readline()
    if not (line[0] == "#" or line.split()[0] == "chrom"):
        fh.seek(0)

def fdr(fbed_file, col_num):
    from scikits.statsmodels.stats import multicomp as multitest
    pvals = np.array([b["p"] for b in bediter(fbed_file, col_num)],
                        dtype=np.float64)
    bh_pvals = multitest.multipletests(pvals, method='fdr_bh')[1]
    fh = open(fbed_file)
    drop_header(fh)
    for bh, l in izip(bh_pvals, fh):
        yield bh, l

def main():
    p = argparse.ArgumentParser(description=__doc__,
                   formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-c", dest="c", help="column number of the pvalues",
                   type=int, default=-1)
    p.add_argument("--qvality", action="store_true", default=False,
        help="""if specified --null must also be specified and qvality"
        " must be on the path""")
    p.add_argument("--null", type=int,
        help="""(optional) column number of the pvalues under the null, e.g.
             for shuffled data is used to do the correction. Otherwise,
             Benjamini-Hochberg is used""")

    p.add_argument('bed_file', help='bed file to correct')
    args = p.parse_args()
    if args.qvality and not args.null:
        sys.exit(not p.print_help())
    return run(args)

if __name__ == "__main__":
    import doctest
    if doctest.testmod(optionflags=doctest.ELLIPSIS |\
                                   doctest.NORMALIZE_WHITESPACE).failed == 0:
        main()
