"""Independent public-genotype relationship analysis (not a national pedigree)."""
from __future__ import annotations
import re
import numpy as np
_GT = {'0/0':0.,'0|0':0.,'0/1':1.,'1/0':1.,'0|1':1.,'1|0':1.,'1/1':2.,'1|1':2.}

def genotype(token: str) -> float:
    """Invalid, missing, partial or non-diploid calls remain missing."""
    return _GT.get(token, float('nan'))

def chromosome_number(label: str) -> int | None:
    text=re.sub(r'^chr','',label,flags=re.IGNORECASE)
    return int(text) if text.isdigit() and 1<=int(text)<=31 else None

def grm(dosages: np.ndarray) -> np.ndarray:
    """VanRaden method 1; SNP rows, sample columns, observed-cohort frequencies."""
    x=np.asarray(dosages,dtype=np.float64)
    if x.ndim!=2 or x.shape[1]<2 or not len(x): raise ValueError('EMPTY_OR_BAD_GENOTYPES')
    valid=np.isfinite(x)
    if np.any(np.isinf(x)) or np.any(valid & ((x<0)|(x>2))): raise ValueError('INVALID_DOSAGE')
    n=valid.sum(axis=1)
    if np.any(n==0): raise ValueError('ALL_MISSING_SNP')
    p=np.nansum(x,axis=1)/(2*n)
    denominator=float(np.sum(2*p*(1-p)))
    if denominator<=0: raise ValueError('NO_POLYMORPHISM')
    z=np.where(valid,x-2*p[:,None],0.)
    return z.T@z/denominator

import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path
import time


def read_assembly(path: Path) -> dict[str, int | None]:
    text=Path(path).read_text(encoding='utf-8')
    if 'GCA_000002305.1' not in text: raise ValueError('WRONG_REFERENCE_ASSEMBLY')
    result={}
    for line in text.splitlines():
        if not line or line.startswith('#'): continue
        f=line.split('\t')
        if len(f)<10: raise ValueError('BAD_ASSEMBLY_REPORT')
        number=chromosome_number(f[2]) if f[1]=='assembled-molecule' else None
        for alias in (f[0],f[4],f[6],f[9]):
            if alias=='na': continue
            if alias in result and result[alias]!=number: raise ValueError('CONFLICTING_CHROMOSOME_MAP')
            result[alias]=number
    if not result: raise ValueError('EMPTY_ASSEMBLY_REPORT')
    return result


def read_vcf(path: Path, assembly_map: dict) -> tuple:
    """Read biallelic autosomal SNPs; unknown contigs and duplicate sample IDs fail.

    All rows at multiply represented autosomal positions are removed, rather
    than guessing whether assays at the same site are duplicates or multiallelic.
    Missing/invalid calls are int8 -1 until QC; never allele zero.
    """
    opener=gzip.open if str(path).endswith('.gz') else open
    samples=None; blocks=[]; buffer=[]; chrs=[]; positions=[]; audit=Counter()
    chrom_counts=Counter(); format_counts=Counter(); gtmap={k:int(v) for k,v in _GT.items()}
    with opener(path,'rt',encoding='utf-8') as handle:
        for line in handle:
            if line.startswith('##'): continue
            f=line.rstrip('\r\n').split('\t')
            if line.startswith('#CHROM'):
                if samples is not None: raise ValueError('REPEATED_SAMPLE_HEADER')
                samples=f[9:]
                if len(samples)<2 or len(set(samples))!=len(samples) or not all(samples):
                    raise ValueError('INVALID_OR_DUPLICATE_SAMPLE_ID')
                continue
            if line.startswith('#') or not line.strip(): continue
            if samples is None: raise ValueError('MISSING_SAMPLE_HEADER')
            if len(f)!=9+len(samples): raise ValueError('RAGGED_VCF_ROW')
            audit['raw_variant_rows']+=1;chrom_counts[f[0]]+=1
            if f[0] not in assembly_map: raise ValueError('UNMAPPED_CHROMOSOME:'+f[0])
            chrom=assembly_map[f[0]]
            if chrom is None: audit['nonautosomal_rows']+=1;continue
            if f[3] not in ('A','C','G','T') or f[4] not in ('A','C','G','T') or f[3]==f[4]:
                audit['not_biallelic_snp']+=1;continue
            if f[6] not in ('.','PASS'): audit['failed_vcf_filter']+=1;continue
            fmt=f[8].split(':');format_counts[f[8]]+=1
            if 'GT' not in fmt: audit['no_genotype_format']+=1;continue
            index=fmt.index('GT')
            if f[8]=='GT': tokens=f[9:]
            else:
                fields=[v.split(':') for v in f[9:]]
                tokens=[v[index] if len(v)>index else '.' for v in fields]
            dosage=np.fromiter((gtmap.get(v,-1) for v in tokens),dtype=np.int8,count=len(samples))
            audit['missing_or_invalid_autosomal_genotypes']+=int(np.count_nonzero(dosage<0))
            pos=int(f[1])
            if pos<=0 or pos>=2**32: raise ValueError('INVALID_POSITION')
            buffer.append(dosage);chrs.append(chrom);positions.append(pos)
            if len(buffer)==8192:blocks.append(np.stack(buffer));buffer=[]
    if samples is None: raise ValueError('MISSING_SAMPLE_HEADER')
    if buffer:blocks.append(np.stack(buffer))
    if not blocks: raise ValueError('NO_AUTOSOMAL_BIALLELIC_SNPS')
    x=np.concatenate(blocks);c=np.array(chrs,dtype=np.int16);p=np.array(positions,dtype=np.int64)
    key=(c.astype(np.int64)<<32)+p
    _,inverse,n=np.unique(key,return_inverse=True,return_counts=True)
    unique=n[inverse]==1
    audit['duplicate_positions']=int(np.count_nonzero(n>1))
    audit['rows_at_duplicate_positions_removed']=int(np.count_nonzero(~unique))
    audit['autosomal_biallelic_rows_before_duplicate_filter']=len(x)
    audit['autosomal_biallelic_unique_positions']=int(unique.sum())
    audit['samples_in_header']=len(samples)
    output=dict(audit);output['original_contig_rows']=dict(chrom_counts);output['formats']=dict(format_counts)
    return x[unique],c[unique],p[unique],samples,output


def marker_qc(x: np.ndarray, sample_call_rate=.98, site_call_rate=.99, maf=.01):
    if not 0<sample_call_rate<=1 or not 0<site_call_rate<=1 or not 0<maf<.5:
        raise ValueError('INVALID_QC_PARAMETERS')
    if x.ndim!=2 or not len(x): raise ValueError('EMPTY_DOSAGES')
    sample_rate=np.mean(x>=0,axis=0)
    keep=sample_rate>=sample_call_rate
    if keep.sum()<2: raise ValueError('TOO_FEW_SAMPLES_AFTER_QC')
    retained=x[:,keep];valid=retained>=0;n=valid.sum(axis=1)
    rate=n/keep.sum()
    p=np.divide(np.where(valid,retained,0).sum(axis=1),2*n,out=np.zeros(len(x),dtype=float),where=n>0)
    frequency=np.minimum(p,1-p)
    sites=(rate>=site_call_rate)&(frequency>=maf)
    if sites.sum()==0: raise ValueError('NO_POLYMORPHIC_MARKERS_AFTER_QC')
    return keep,sites,{'sample_call_rates':sample_rate,'site_call_rates':rate,'allele_frequency':p,'minor_allele_frequency':frequency}


def block_grm(x: np.ndarray, block_size=2048) -> np.ndarray:
    if block_size<1 or x.ndim!=2 or len(x)==0: raise ValueError('INVALID_BLOCK_INPUT')
    matrix=np.zeros((x.shape[1],x.shape[1]),dtype=np.float64);denominator=0.
    for start in range(0,len(x),block_size):
        block=x[start:start+block_size].astype(np.float64)
        valid=block>=0;n=valid.sum(axis=1)
        if np.any(n==0): raise ValueError('ALL_MISSING_SNP')
        p=np.where(valid,block,0).sum(axis=1)/(2*n)
        z=np.where(valid,block-2*p[:,None],0.)
        matrix+=z.T@z;denominator+=float(np.sum(2*p*(1-p)))
    if denominator<=0: raise ValueError('NO_POLYMORPHISM')
    return matrix/denominator


def spaced_mask(chrom: np.ndarray, pos: np.ndarray, distance=50000) -> np.ndarray:
    if distance<1:raise ValueError('BAD_DISTANCE')
    result=np.zeros(len(pos),bool);last={}
    for i in np.lexsort((pos,chrom)):
        c=int(chrom[i]);p=int(pos[i])
        if c not in last or p-last[c]>=distance:result[i]=True;last[c]=p
    return result


def quantiles(values: np.ndarray) -> dict:
    return {str(q):float(np.quantile(values,q)) for q in (0,.01,.05,.5,.95,.99,1)}


def matrix_comparison(a: np.ndarray, b: np.ndarray) -> dict:
    tri=np.triu_indices(len(a),1);x=a[tri];y=b[tri]
    if np.std(x)==0 or np.std(y)==0: raise ValueError('DEGENERATE_PAIR_VALUES')
    aa=a.copy();bb=b.copy();np.fill_diagonal(aa,-np.inf);np.fill_diagonal(bb,-np.inf)
    n=len(a);k=min(10,n-1)
    topa=np.argsort(-aa,axis=1)[:,:k];topb=np.argsort(-bb,axis=1)[:,:k]
    return {'pairwise_pearson':float(np.corrcoef(x,y)[0,1]),
            'same_nearest_neighbor_count':int(np.count_nonzero(topa[:,0]==topb[:,0])),
            'sample_count':n,'mean_top10_neighbor_overlap':float(np.mean([len(set(v)&set(w))/k for v,w in zip(topa,topb)])),
            'same_subjects_different_markers_not_independent_animals':True,
            'no_pairwise_independence_p_value':True}


def file_hash(path: Path, method='sha256') -> str:
    h=hashlib.new(method)
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def analyze(vcf: Path, assembly: Path, output: Path, *, expected_md5: str | None=None) -> dict:
    started=time.monotonic();output.mkdir(parents=True,exist_ok=True)
    digest=file_hash(vcf);md5=file_hash(vcf,'md5')
    if expected_md5 and md5!=expected_md5:raise ValueError('SOURCE_MD5_MISMATCH')
    x,chrom,pos,samples,audit=read_vcf(vcf,read_assembly(assembly))
    keep,sites,qc=marker_qc(x)
    ids=[s for s,k in zip(samples,keep) if k]
    selected=x[sites][:,keep];chr_selected=chrom[sites];pos_selected=pos[sites]
    higher=qc['minor_allele_frequency'][sites]>=.05
    spaced=spaced_mask(chr_selected,pos_selected)
    masks={'all_maf01':np.ones(len(selected),bool),'maf05':higher,
           'odd_autosomes':chr_selected%2==1,'even_autosomes':chr_selected%2==0,
           'spaced_50kb':spaced}
    matrices={};variant_counts={}
    for name,mask in masks.items():
        if not mask.any():raise ValueError('NO_MARKERS_'+name)
        matrix=block_grm(selected[mask]);matrices[name]=matrix;variant_counts[name]=int(mask.sum())
        np.save(output/f'G_{name}.npy',matrix)
    g=matrices['all_maf01'];eigen=np.linalg.eigvalsh(g);rowsum=float(np.max(np.abs(g.sum(axis=1))))
    symmetry=float(np.max(np.abs(g-g.T)))
    if eigen.min() < -1e-8 or symmetry>1e-10 or rowsum>1e-8:raise ValueError('MATRIX_ALGEBRA_FAILED')
    tri=np.triu_indices(len(ids),1);values=g[tri]
    with (output/'samples_quality.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['source_sample_id','pre_site_QC_call_rate','retained','G_diagonal_if_retained'])
        j=0
        for i,s in enumerate(samples):
            w.writerow([s,float(qc['sample_call_rates'][i]),int(keep[i]),float(g[j,j]) if keep[i] else ''])
            j+=int(keep[i])
    with (output/'genomic_relationship_matrix.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['source_sample_id']+ids)
        for s,row in zip(ids,g):w.writerow([s]+[f'{v:.10g}' for v in row])
    with (output/'genomic_relationship_all_pairs.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['sample_1','sample_2']+list(matrices))
        for i,j in zip(*tri):w.writerow([ids[i],ids[j]]+[f'{m[i,j]:.10g}' for m in matrices.values()])
    with (output/'markers_by_autosome.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['autosome','autosomal_biallelic_unique_before_QC','selected_maf01','selected_maf05','selected_spaced50kb'])
        for c in range(1,32):w.writerow([c,int(np.sum(chrom==c)),int(np.sum(chr_selected==c)),int(np.sum((chr_selected==c)&higher)),int(np.sum((chr_selected==c)&spaced))])
    verified=(digest=='f8ca6056b897fe2d3fc0e9cabdf866794933034a57ede2948428451f4826fd9e'
              and file_hash(assembly)=='376246dc4dac2bd8873594f5d40a1109781da550cdbfa794779d5bfd0a9eaa53'
              and len(samples)==370)
    summary={'status':('REAL_PUBLIC_JAPANESE_THOROUGHBRED_GENOMIC_RELATIONSHIPS_COMPUTED'
                       if verified else 'UNVERIFIED_INPUT_GENOMIC_RELATIONSHIPS_COMPUTED'),
        'original_study_source_identity_verified':verified,
        'study':'PRJEB32686' if verified else None,
        'analysis_accession':'ERZ936110' if verified else None,
        'publication_doi':'10.1371/journal.pone.0218407' if verified else None,
        'source_file':vcf.name,'source_sha256':digest,'source_md5':md5,'matches_official_md5':md5==expected_md5 if expected_md5 else None,
        'assembly':'GCA_000002305.1 EquCab2.0','assembly_report_sha256':file_hash(assembly),
        'raw_file_audit':audit,'sample_QC_threshold':.98,'site_call_rate_threshold':.99,'primary_MAF':.01,
        'sample_count_before_QC':len(samples),'sample_count_retained':len(ids),'sample_ids_are_animal_lab_ids_not_registered_horse_names':verified,
        'sample_call_rate_quantiles':quantiles(qc['sample_call_rates']),
        'variants_retained_by_panel':variant_counts,'selected_genotype_cells':int(selected.size),
        'selected_observed_genotype_cells':int(np.count_nonzero(selected>=0)),
        'all_unique_sample_pairs':len(values),'offdiagonal_G_quantiles':quantiles(values),'diagonal_G_quantiles':quantiles(np.diag(g)),
        'descriptive_G_threshold_counts_NOT_pedigree_relationship_classes':{str(t):int(np.sum(values>=t)) for t in (.125,.25,.5)},
        'matrix_checks':{'symmetric_max_abs_difference':symmetry,'max_abs_row_sum':rowsum,'min_eigenvalue':float(eigen.min()),'max_eigenvalue':float(eigen.max())},
        'sensitivity':{name:matrix_comparison(g,matrices[name]) for name in ('maf05','spaced_50kb')},
        'odd_even_autosome_stability':matrix_comparison(matrices['odd_autosomes'],matrices['even_autosomes']),
        'normalization':'G=ZZ^T/sum(2p(1-p)); p from retained cohort, missing dosages mean-imputed after QC',
        'limitations':[('Selected 370-horse research sample, not all JRA/NAR horses.' if verified
                        else 'Input source identity is unverified; synthetic tests and other datasets are not original Japanese study observations.'),
            'Sample-relative genomic G is not absolute pedigree A or a coefficient of identity by descent.',
            'Negative G means below the sampled allele-frequency baseline; not absence of common ancestry.',
            'G diagonal minus 1 is not reported as pedigree/ROH inbreeding.',
            'SNP-array ascertainment and linkage disequilibrium influence G; 50kb spacing is a sensitivity check, NOT LD pruning.',
            'No linkage to Meisho horse names or registry pedigree has been established.',
            'No race-performance phenotype or future prediction validation is included.'],
        'runtime_seconds':round(time.monotonic()-started,3)}
    (output/'analysis_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2));return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--vcf',type=Path,required=True);p.add_argument('--assembly-report',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--expected-md5')
    a=p.parse_args();analyze(a.vcf,a.assembly_report,a.output,expected_md5=a.expected_md5)

if __name__=='__main__':main()
