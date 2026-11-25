# Independent wild-ungulate extension: source feasibility

26 November 2026 · literature and repository-file-list audit only. No raw data acquired, no ecological effect estimated. Main manuscript remains a managed allocation study.

## Why this is a meaningful next test

Gervais et al. (2022), Journal of Animal Ecology 91:1239–1250, [doi:10.1111/1365-2656.13677](https://doi.org/10.1111/1365-2656.13677), study habitat composition and genomic/environmental similarity in roe deer. Their [Dryad dataset](https://doi.org/10.5061/dryad.6wwpzgn1j), public listing dated February 2022, includes 293 deer in the reduced genomic/environmental analysis. Original research addresses quantitative genetic partitioning, not the additional predictive value of a frozen genomic-history correction during accumulation of focal records. The cited study makes habitat–genome association and spatial confounding particularly relevant to our hypothesis. It is not our result.

The listed files include data_spaceuse_ID.Rdata, dailyaveragespeed_ID.Rdata, grm_full_ID.Rdata, grm_reduced_n293_ID.Rdata, sim_envi_MONTH_FULL_ID.Rdata, sim_envi_for456month_ID.Rdata, bodymass_ID.Rdata, hindfoot_ID.Rdata and README.txt. File names alone do not establish exact columns, dated repetition or compatible ID ordering. License and exact file revision must be verified from provider metadata before data reuse.

## Gates for a new independent analysis

1. Verify the data release and license, download from the provider only, hash bytes, read README, inspect object types and exact identifier/time variables locally, without publishing identifiers or coordinates.
2. Confirm row/column labels and symmetry of reduced GRM and spatial similarity matrix, exact IDs across habitat outcomes and GRM; do not join by row order. Determine if there is genuinely time-ordered repeated habitat composition or only a single settlement summary per individual. Month-of-year without observation year/date does not suffice for chronological validation.
3. If eligible repeated dated habitat outcomes exist, predefine a scalar environmental-use outcome, an earlier training period and later untouched periods before examining prediction gains. Compare an individual-only shrunk baseline with an earlier fitted GRM-informed auxiliary correction, and with a spatial/environmental similarity control. Use a stable common cohort for fixed-correction own-update and outcome-shift decomposition; separately report full-cohort membership. All evaluated predictions chronological; no outcome-based donor selection. Keep negative results and low support. Genomic similarity can be negative and does not equal known sibship: use an explicitly validated regularized kernel predictor, not direct reuse of horse sire counts.
4. If only cross-sectional habitat composition, do not manufacture longitudinal histories. Evaluate only a separately defined cross-sectional question, or keep the temporal extension HOLD. Movement and phenotype endpoints are not substitutes for habitat allocation without explicit reframing.
5. Control shared space and opportunity; same site and season can create genomic/environmental overlap. Distinguish realized use from preference. No new causal genetic or heritability claim from loss differences.

Secondary candidate: Winter et al. (2024), [Dryad 10.5061/dryad.4f4qrfjmz](https://doi.org/10.5061/dryad.4f4qrfjmz) / [Zenodo 12181326](https://zenodo.org/records/12181326), [Ecography doi:10.1111/ecog.07225](https://doi.org/10.1111/ecog.07225). Pronghorn individual habitat selection and prediction transport. File list includes RSF_data.rds and MEM_data.rds. No genomic or pedigree information verified; a possible individual-versus-group predictor test, not a family-channel replication.

Source availability and schema unresolved; web access to Dryad API/related Zenodo records was unsuccessful in this turn. No automatic download of unverified data and no claim of an external validation. The first priority is an actual source/metadata audit, not adding another retrospective horse gate.
