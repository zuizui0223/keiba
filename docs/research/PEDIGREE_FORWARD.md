# Pedigree prediction: ecological extension (2026-11-14)

**Status: implementation and synthetic-software tests only. Real equine kin effect is UNTESTED.**

The project has original HORSES-ID-linked repeated GPS timing, but the checked Racing Queensland SOAP horse-roster endpoint lacks structured sire/dam IDs. Horse-ID repeatability is not automatically heritability. Do not add guessed parent IDs, infer pedigrees from names, or commit original horse-level rows.

## Research hypotheses

H_K1: Historical *relatives'* early GPS timing improves future predictions for horses with **no usable own histories (cold starts)** beyond matched race-context means.

H_K2: Relatives add predictive information even after conditioning on the focal horse's own earlier early-GPS behavior. The expected marginal gain should be smaller when the horse has abundant own observations, but this is a hypothesis.

H_K3: Kinship signal differs across distance, ground and first-sectional marker. The current exact-context matching screen does NOT identify an inherited environment reaction norm; a formal random-slope animal model is a separate future study.

H_K4: Genetically nonrandom **opponent composition**, direct versus indirect genetic effects and interactions with market odds are future extensions, NOT implemented or supported from the currently incomplete starter/finisher records. Never substitute postrace observed peer means for prerace opponent exposures.

The primary outcome is **absolute focal seconds to the first GPS marker**, not race finish time, odds, a calibrated winning probability, or physiological fitness.

## Prior evidence and likely novelty

Pedigree effects in Thoroughbred performance are not novel by themselves:

- Oda & Onogi (2024), Japanese performance prediction, *J Anim Breed Genet*, https://doi.org/10.1111/jbg.12822 .
- Padilha et al. (2025), genetic versus permanent-environmental components in 23,290 racing records, *J Equine Vet Sci*, https://doi.org/10.1016/j.jevs.2024.105244 .
- Great Britain pedigree-based speed and genetic trends, *Scientific Reports* (2023), https://pmc.ncbi.nlm.nih.gov/articles/PMC10313675/ .

The narrower ecological extension is **time-forward transfer of individual early-GPS signatures via documented relatives**, with own-history, context and cold-start controls, then eventually family assortative competition.

## Private, local CSV schema

Observations.csv columns:

    horse_id,race_id,race_date,venue,first_marker_m,distance_m,going,race_class,early_section_s

Pedigree.csv columns:

    horse_id,sire_id,dam_id,known_on

* Use independently reconciled **stable horse IDs**; never fuzzy-match horse names. Each HORSE x race pair must be unique and any repeated race_id must have consistent date/context.
* Race dates and known_on are ISO dates. A pedigree entry is used only when known_on is **strictly before the training/prediction cutoff**. Document as-of availability with independent provenance; a retrospective date in a private file alone is not proof it was available then.
* Parentage must be verified against authorized pedigree data. Unknown parents are blank. Unrecorded ancestors are treated computationally as unrelated founders, which **underestimates** their biological relatedness.
* The measured early_section_s must be finite, positive, first-GPS **absolute seconds**, with exactly compatible marker, distance and venue. Do not impute missing GPS or DNF as zero.
* Full raw records remain local/private; only aggregate anonymous output is saved.

Run locally after obtaining permitted original data:

~~~bash
python scripts/ecology_pedigree_forward.py \
  --observations /private/horse-sectionals.csv \
  --pedigree /private/horse-pedigree.csv \
  --output /private/kin-forward-summary.json \
  --min-horses 20 --permutations 49

python -m unittest discover -s tests -p 'test_ecology_pedigree_forward.py' -v
~~~

The CLI cannot establish data-rights clearance, correct cross-source identity, certified starters, or certified finish status. These checks must be completed upstream.

## Implemented comparison

The numerator relationship A between outbred individuals is 0.5 for parent/offspring and full siblings, 0.25 for half siblings, and can reflect documented inbreeding on the diagonal. This is **pedigree-expected additive relatedness, not genomic similarity**.

For each exact venue × first-marker × distance × going × race-class context c, estimate training-only contextual mean μc, each horse's historical deviation dic, and number of its prior records nic. Context is usable only with >=4 past observations from >=3 horses. Fit:

    M0 = μc + [nic / (nic + 2)] dic

Compute kin residual from *other horses*, not from the focal's own prior rows:

    Kic = [sum_j Aij * djc * I(Aij >= 0.125)]
          / [2 + sum_j Aij * I(Aij >= 0.125)] ; j != i

One historical mean is used per relative horse, independent of number of their past starts. The 0.125 threshold is a fixed support screen, NOT a nonlinearity/phase transition inferred from data.

    M1 = M0 + λ * [2/(nic + 2)] * Kic

Select λ from {0, 0.25, 0.5, 1} on earlier **inner** validation dates only. Last 20% of distinct dates form the later outer test; never borrow same-day race outcomes into earlier predictions. Select λ = 0 if relatives are not useful in the inner data. This is a constrained **kin-shrinkage forecaster**, not a fitted additive-genetic variance-component animal model.

Report equal-horse-weighted RMSE (M0, M1, Δ=M0−M1) for all scored test rows, own-history, cold-start, kin-exposed, and cold-start + kin-exposed strata; record input and eligible denominators. A deterministic shuffle of mapping from recorded horses to pedigree positions is only a qualitative negative control; the observed fraction of better shuffled maps is **not a calibrated genetic p-value**.

## Required interpretation gates

| Pattern | Allowed interpretation | Forbidden inference |
| --- | --- | --- |
| M1 improves future RMSE and has enough related test horses | Additional **kin-associated historical predictive information** in this source/measurement cohort | Heritability, genetic causation, fitness, profitability |
| M1 does not improve | No detectable gain for THIS model, cutoff and population | No genetic influence |
| No validated source pedigree or low kin/context overlap | **HOLD** | Treat genuinely unknown ancestors as unrelated |
| Same pedigree gain as shuffled-parentage negative control | Genetic specificity unresolved | Claim true genetic transmission |

Strong competing explanations include: shared breeder, stable, trainer, owner or jockey; parental environment; race-entry sorting by class/venue/ground; age and sex; and GPS selection. Future formal pedigree animal model must add permanent environmental, maternal and stable/trainer terms, and ideally an independently sourced genomic G matrix. Report sire-/dam- and breeder-/trainer-stratified sensitivity tests separately, with independence of families explicitly audited.

## Actual cohort readiness

**HOLD_NO_VALIDATED_PEDIGREE_JOIN.** Racing Queensland's original SOAP GetHorsesForRace returns horse ID, horse name, weight and assigned rider/trainer but not sire/dam ID, per the checked published schema (see docs/ecology-rq-official-soap-vs-final-starters-jockey-data-scope.md). Racing Australia's public five-generation pedigree search at https://racingaustralia.horse/FreeServices/PedigreeSearch.aspx provides possible manual verification, **not permission for bulk harvesting/republishing**. An authorized pedigree export and an independently validated registry-ID crosswalk are prerequisites to any empirical claim.

Keep all market and betting odds evaluation in the separate docs/betting track unless pre-race odds and verified outcomes are available in a future independently frozen prediction design.


## Follow-up: kinship-vs-management falsification and public-source audit

[**Pedigree falsification results**](PEDIGREE_FALSIFICATION.md) now record the 3-seed *fabricated* stable-only counterexample, paternal versus maternal half-sib and full-sib prediction channels, and trainer-/breeder-exclusion controls. The published Dryad source API returned dataset metadata and CC0 declaration, but raw files stayed inaccessible (401/403): **no empirical horse kin gains were measured**.

## Independent empirical candidate — NOT downloaded or scored

Wilson (2022) deposited an anonymized real Thoroughbred dataset for a parental-age/speed paper at **Dryad DOI https://doi.org/10.5061/dryad.qbzkh18m0**. The companion publication (https://doi.org/10.1098/rsos.220691) describes **906,027 finishing-time records from 101,257 horses**, with known sire and dam identities. This is promising for an **independent pedigree × future full-race speed** verification. It cannot validate RQ **first-GPS early pacing** (a different outcome). At the time of this audit, the dataset landing page and metadata were available but the actual 15.89 MB parental_ageing_data.zip could not be retrieved in the current runtime (403 on file-stream download). Therefore no schema preflight, identity linkage, as-of ordering, reanalysis or novel numerical effects are claimed. Source-version, license, observation dates and phenotype columns must be validated after authorized acquisition. Do not present publication sample sizes as samples processed by this repository.
