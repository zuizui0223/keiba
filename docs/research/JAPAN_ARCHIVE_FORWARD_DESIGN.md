# Japan archive predictive extension — frozen before outcome scoring

Goal: evaluate whether histories of real same-parent horses improve later normalized finishing ranks beyond the focal horse and trainer.

Data: ayuser/horse-racing-in-japan, public archive with Unknown redistribution licence. Raw data remain transient; publish only code and aggregate derived findings. No nationwide-completeness or licence-clearance claim. Original SHA256 c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f; member 2010-2021.csv.

Outcome: normalized classified finishing rank (rank-1)/(N_classified-1), NOT GPS, winning probabilities, heritability, or betting gain. Only untied, contiguous classified ranks in flat turf/dirt events of 600–3600 m. Nonfinishers are not imputed; selection is explicitly conditional on retained finishers. Exact horse/race duplicates fail. Race ID is source date × venue × race number.

Validation: train through Y-2, tune on Y-1, refit history through Y-1, test Y=2019,2020,2021. Whole-year blocks prevent same-day or future outcomes in features. Historical parent/trainer publication timestamps are not independently verified, so this is retrospective, never a prospective forecast.

Models: own-history baseline; +sire, +dam, +sire+dam direct-parent score; +trainer; +Meisho naming group; +trainer+kin. Four predeclared coefficients 0,.25,.5,1; two coefficients for the joint model. Distinct relative-horse contributions, not starts: focal horse removed from each group. Family histories stratified by JRA/NAR venue, turf/dirt, 400m distance bin. Full siblings contribute once per shared parent, half siblings once; this is not a full pedigree A.

Identity: exact supplied horse/sire/dam IDs, never name-derived identity. Past parent contradictions quarantined from family training profiles. No genome-to-name join. The Meisho name flag is not an owner label.

Statistics: all models score identical later rows. Equal-horse RMSE/MAE, unseen-at-year-cutoff and first-retained-record strata, Meisho and JRA/NAR groups. Separate paired bootstrap sensitivity intervals by sire family and race date; not a joint multiway CI or proof of genetic causation.

Implementation: scripts/ecology_japan_archive_forward.py; tests/test_ecology_japan_archive_forward.py. Test-first implementation verified source-label guard failure then all 12 tests passing locally. Compare source hashes, input row counts, ID uniqueness and family contradictions before accepting actual-source results. No changes to PR43 or independent genomic PR44.
