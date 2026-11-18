import unittest
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import ecology_japan_eva_genomic as g

class GenomicTests(unittest.TestCase):
    def test_unphased_and_phased_diploid_dosage(self):
        for text,want in [('0/0',0),('0|1',1),('1/0',1),('1|1',2)]:
            self.assertEqual(g.genotype(text),want)
    def test_missing_haploid_and_nonbiallelic_not_dosages(self):
        for text in ('.','./.','.|.','0/.','./1','0','0/2','10/0','0/1/1'):
            self.assertIsNotNone(g.genotype(text))
            self.assertTrue(np.isnan(g.genotype(text)))
    def test_autosomes_only_exact_labels(self):
        for text,want in [('1',1),('chr31',31),('CHR2',2),('X',None),('32',None),('MT',None),('1_random',None)]:
            self.assertEqual(g.chromosome_number(text),want)
    def test_manual_vanraden(self):
        x=np.array([[0.,1.,2.,1.]])
        got=g.grm(x)
        self.assertIsNotNone(got)
        want=np.outer([-1.,0.,1.,0.],[-1.,0.,1.,0.])/.5
        np.testing.assert_allclose(got,want)
    def test_missing_mean_imputation_centering(self):
        x=np.array([[0.,1.,np.nan,2.],[2.,1.,0.,1.]])
        got=g.grm(x)
        self.assertIsNotNone(got)
        p=np.nanmean(x,axis=1)/2
        z=np.where(np.isnan(x),2*p[:,None],x)-2*p[:,None]
        np.testing.assert_allclose(got,z.T@z/np.sum(2*p*(1-p)))
        np.testing.assert_allclose(got.sum(axis=1),0,atol=1e-12)
    def test_allele_flip_invariance(self):
        x=np.array([[0.,1.,2.,1.],[1.,2.,0.,0.]])
        got=g.grm(x); self.assertIsNotNone(got)
        np.testing.assert_allclose(got,g.grm(2-x))
    def test_psd_and_symmetry(self):
        rng=np.random.default_rng(17); x=rng.integers(0,3,(70,8)).astype(float)
        got=g.grm(x); self.assertIsNotNone(got)
        np.testing.assert_allclose(got,got.T,atol=1e-12)
        self.assertGreaterEqual(np.linalg.eigvalsh(got).min(),-1e-10)
    def test_monomorphic_only_rejected(self):
        with self.assertRaises(ValueError): g.grm(np.zeros((2,4)))

import tempfile
import gzip
class FileAndQcTests(unittest.TestCase):
    def test_vcf_autosome_filter_and_missing_call(self):
        text='##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\tB\tC\n'
        text+='CM1\t10\t.\tA\tC\t.\tPASS\t.\tGT\t0/0\t0/1\t1/1\n'
        text+='CMX\t20\t.\tA\tG\t.\tPASS\t.\tGT\t0\t1\t0\n'
        text+='CM1\t30\t.\tA\tC,G\t.\tPASS\t.\tGT\t0/0\t0/1\t0/0\n'
        text+='CM1\t40\t.\tA\tT\t.\tPASS\t.\tGT:DP\t0/0:8\t./.:0\t1/1:9\n'
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'in.vcf.gz'
            with gzip.open(p,'wt') as f:f.write(text)
            got=g.read_vcf(p,{'CM1':1,'CMX':None})
        self.assertIsNotNone(got)
        x,c,pos,s,audit=got
        self.assertEqual(s,['A','B','C']);self.assertEqual(x.shape,(2,3))
        self.assertEqual(x[1,1],-1);self.assertEqual(audit['raw_variant_rows'],4)
        self.assertEqual(audit['nonautosomal_rows'],1);self.assertEqual(audit['not_biallelic_snp'],1)
    def test_duplicate_samples_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'in.vcf';p.write_text('#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\tA\n')
            with self.assertRaisesRegex(ValueError,'SAMPLE'):g.read_vcf(p,{})
    def test_unknown_contig_not_guessed(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'in.vcf';p.write_text('#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\tB\nweird\t1\t.\tA\tC\t.\tPASS\t.\tGT\t0/0\t1/1\n')
            with self.assertRaisesRegex(ValueError,'UNMAPPED'):g.read_vcf(p,{})
    def test_marker_qc_does_not_impute_before_call_rate_filter(self):
        x=np.array([[0,1,2],[0,1,2],[0,-1,2],[0,0,0]],dtype=np.int8)
        got=g.marker_qc(x,sample_call_rate=.7,site_call_rate=.99,maf=.01)
        self.assertIsNotNone(got)
        sample_keep,site_keep,stats=got
        self.assertEqual(sample_keep.tolist(),[True,True,True])
        self.assertEqual(site_keep.tolist(),[True,True,False,False])
    def test_block_and_direct_grm_match(self):
        rng=np.random.default_rng(101);x=rng.integers(0,3,(41,7)).astype(np.int8);x[3,1]=-1
        got=g.block_grm(x,block_size=5);self.assertIsNotNone(got)
        dense=x.astype(float);dense[dense<0]=np.nan
        np.testing.assert_allclose(got,g.grm(dense),atol=1e-12)
    def test_assembly_accessions_not_inferred_arithmetically(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'map.txt';p.write_text('# GenBank assembly accession: GCA_000002305.1\n1\tassembled-molecule\t1\tChromosome\tCM1\t=\tNC1\tPrimary Assembly\t100\tchr1\nX\tassembled-molecule\tX\tChromosome\tCMX\t=\tNCX\tPrimary Assembly\t100\tchrX\n')
            got=g.read_assembly(p)
        self.assertIsNotNone(got);self.assertEqual(got['CM1'],1);self.assertIsNone(got['CMX'])

class OutputValidationTests(unittest.TestCase):
    def test_spaced_selection_is_chromosome_specific(self):
        c=np.array([2,1,1,2,1]);p=np.array([1,1,20,20,60])
        np.testing.assert_array_equal(g.spaced_mask(c,p,distance=50),[True,True,False,False,True])
    def test_identical_matrix_comparison_has_unit_correlations(self):
        x=np.array([[0,1,2,1],[2,0,1,2]],dtype=np.int8)
        a=g.block_grm(x);r=g.matrix_comparison(a,a)
        self.assertAlmostEqual(r['pairwise_pearson'],1)
        self.assertEqual(r['same_nearest_neighbor_count'],4)
        self.assertEqual(r['mean_top10_neighbor_overlap'],1)
    def test_all_duplicate_position_rows_are_excluded(self):
        head='#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\tB\n'
        body='1\t10\t.\tA\tC\t.\tPASS\t.\tGT\t0/0\t1/1\n'*2
        body+='1\t20\t.\tA\tC\t.\tPASS\t.\tGT\t0/0\t1/1\n'
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'in.vcf';p.write_text(head+body)
            x,c,pos,ids,audit=g.read_vcf(p,{'1':1})
        self.assertEqual(x.shape,(1,2));self.assertEqual(audit['rows_at_duplicate_positions_removed'],2)
        self.assertEqual(pos.tolist(),[20])
    def test_complete_small_analysis_writes_every_pair(self):
        import csv,json
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);v=p/'input.vcf';a=p/'map.txt';out=p/'out'
            a.write_text('# GenBank assembly accession: GCA_000002305.1\n1\tassembled-molecule\t1\tChromosome\tCM1\t=\tNC1\tPrimary Assembly\t1000000\tchr1\n2\tassembled-molecule\t2\tChromosome\tCM2\t=\tNC2\tPrimary Assembly\t1000000\tchr2\n')
            lines=['#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\tB\tC\tD']
            for chrom in ['CM1','CM2']:
                for i in range(5):
                    gt=['0/0','0/1','1/1','0/1'] if i%2==0 else ['0/1','1/1','0/0','0/0']
                    lines.append('\t'.join([chrom,str(i*60000+1),'.','A','C','.','PASS','.','GT']+gt))
            v.write_text('\n'.join(lines)+'\n')
            summary=g.analyze(v,a,out)
            self.assertEqual(summary['all_unique_sample_pairs'],6)
            self.assertEqual(summary['variants_retained_by_panel']['all_maf01'],10)
            self.assertEqual(summary['sample_count_retained'],4)
            with (out/'genomic_relationship_all_pairs.csv').open() as f:
                self.assertEqual(len(list(csv.DictReader(f))),6)
            self.assertTrue((out/'genomic_relationship_matrix.csv').exists())

if __name__=='__main__':
    unittest.main()
