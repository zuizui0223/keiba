"""A synthetic input must never inherit the real Japanese study label."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from ecology_japan_eva_genomic import analyze

class GenotypeProvenanceTests(unittest.TestCase):
    def test_synthetic_fixture_is_not_certified_original_research_data(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);v=root/'fixture.vcf';assembly=root/'map.txt'
            assembly.write_text('# GenBank assembly accession: GCA_000002305.1\n1\tassembled-molecule\t1\tChromosome\tCM1\t=\tNC1\tPrimary Assembly\t1000000\tchr1\n2\tassembled-molecule\t2\tChromosome\tCM2\t=\tNC2\tPrimary Assembly\t1000000\tchr2\n')
            rows=['#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\tB\tC\tD']
            for chrom in ['CM1','CM2']:
                rows.append('\t'.join([chrom,'1','.','A','C','.','PASS','.','GT','0/0','0/1','1/1','0/1']))
                rows.append('\t'.join([chrom,'60001','.','A','C','.','PASS','.','GT','0/1','1/1','0/0','0/0']))
            v.write_text('\n'.join(rows)+'\n')
            with contextlib.redirect_stdout(io.StringIO()):
                result=analyze(v,assembly,root/'output')
            self.assertEqual(result['status'],'UNVERIFIED_INPUT_GENOMIC_RELATIONSHIPS_COMPUTED')
            self.assertFalse(result['original_study_source_identity_verified'])
            self.assertIsNone(result['study'])
            self.assertIsNone(result['analysis_accession'])
            self.assertEqual(result['all_unique_sample_pairs'],6)
            self.assertFalse(result['sample_ids_are_animal_lab_ids_not_registered_horse_names'])

if __name__=='__main__':unittest.main()
