# Surface-Forced Campaign Report: surface_forced_tall_002

Campaign ID: `surface_forced_tall_002`
Protocol: `docs/research/surface-forced-sounding-verification-protocol.md`
Matrix file: `surface_forced_tall_002.yaml` (runtime-local path omitted)
Generated: `2026-07-14T14:43:04.705347+00:00`

## Objective

Verify that numeric uniform lower-boundary heat/moisture forcing is preserved through package generation, CM1 execution, ingest, hfx/qfx statistics, early low-level qv/theta response diagnostics, and reporting on the corrected 18 km stretched domain; then gate deeper sounding-response checks on the Phase 1 evidence.

## Matrix Summary

- Runs planned: 10
- Status counts: `{"ingested": 4, "planned": 6}`
- Phase gate state: `surface_flux_response_inconclusive_missing_evidence`
- Surface flux response: `surface_flux_response_inconclusive_missing_evidence`

## Operator Overrides

No operator phase-gate overrides were recorded.

## Run Table

| Matrix ID | Status | Station/time | Forcing | Grid/domain | Key result |
| --- | --- | --- | --- | --- | --- |
| phase1_control_default_flux | ingested | VALLEY; NE. 2026-06-07T18:00:00Z | H 0.008 K m/s; M 5.2e-05 g/g m/s | wide_12km 128 dx 100.0 m | cloud top unavailable (untrusted); max w 4.209 (caveated); surface rain unavailable (untrusted) |
| phase1_control_high_sensible | ingested | VALLEY; NE. 2026-06-07T18:00:00Z | H 0.04 K m/s; M 5.2e-05 g/g m/s | wide_12km 128 dx 100.0 m | cloud top 4591; max w 9.897; surface rain yes |
| phase1_control_high_moisture | ingested | VALLEY; NE. 2026-06-07T18:00:00Z | H 0.008 K m/s; M 0.0001 g/g m/s | wide_12km 128 dx 100.0 m | cloud top 1.087e+04; max w 9.921; surface rain yes |
| phase1_control_high_both | ingested | VALLEY; NE. 2026-06-07T18:00:00Z | H 0.04 K m/s; M 0.0001 g/g m/s | wide_12km 128 dx 100.0 m | cloud top 5666; max w 12.34; surface rain yes |
| phase2_easy_deep_default_12km_6h | planned | unavailable time unavailable | H 0.008 K m/s; M 5.2e-05 g/g m/s | wide_12km 128 dx 100.0 m | planned |
| phase2_easy_deep_strong_12km_6h | planned | unavailable time unavailable | H 0.04 K m/s; M 0.0001 g/g m/s | wide_12km 128 dx 100.0 m | planned |
| phase2_easy_deep_strong_12km_12h | planned | unavailable time unavailable | H 0.04 K m/s; M 0.0001 g/g m/s | wide_12km 128 dx 100.0 m | planned |
| phase2_easy_deep_strong_60km_12h | planned | unavailable time unavailable | H 0.04 K m/s; M 0.0001 g/g m/s | regional_60km 128 dx 468.75 m | planned |
| phase2_easy_deep_strong_120km_12h_optional | planned | unavailable time unavailable | H 0.04 K m/s; M 0.0001 g/g m/s | regional_120km 128 dx 937.5 m | planned |
| phase3_weak_control_strong_60km_12h | planned | unavailable time unavailable | H 0.04 K m/s; M 0.0001 g/g m/s | regional_60km 128 dx 468.75 m | planned |

## Per-Run Evidence

### phase1_control_default_flux

- Run ID: `surface_forced_tall_002-phase1_control_default_flux-4b99360e46`
- Result ID: `result-surface_forced_tall_002-phase1_control_default_flux-4b99360e46`
- Status: package `packaged`, run `completed_not_ingested`, ingest `ingested`
- Provenance: Cloud Chamber `c94520049bdb7e3c396dc9a26f33037c4a2762d8`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-f4fa3d80f08f03a8|USM00072558|2026-06-07T18:00:00Z`
- Candidate story: `shallow_cumulus_candidate`
- Required/missing fields: `qv, qc, w, qr, rain, dbz, hfx, qfx` / `none`
- Surface flux fields: hfx `True`, moisture flux `True` via `qfx`
- Surface flux stats: hfx `7.944224834442139`/`9.5802640914917`/`8.904636484635072`, qfx `5.134478851687163e-05`/`6.191877037053928e-05`/`5.7552083215108483e-05`; counts hfx `393216`/`16384`/`409600`, qfx `393216`/`16384`/`409600`
- Surface flux frame quality: hfx `affected frames [24] at 21600 s; initial ok; terminal affected; entirely non-finite frames 1`, qfx `affected frames [24] at 21600 s; initial ok; terminal affected; entirely non-finite frames 1`
- Terminal output contamination: `hfx, qc, qfx, qr, surface_rain`; warnings `CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG, IEEE_DIVIDE_BY_ZERO, IEEE_OVERFLOW_FLAG, IEEE_UNDERFLOW_FLAG`
- Cloud/updraft: first cloud unavailable (untrusted), max cloud top unavailable (untrusted), max qc unavailable (untrusted), max w 4.209 (caveated)
- Precipitation/reflectivity: qr unavailable (untrusted), surface rain unavailable (untrusted), max dBZ 29.5
- Diagnostic trust: `qc untrusted, w caveated, qr untrusted, surface_rain untrusted, dbz trusted`
- Field-quality warnings: `non_finite_values_detected_in_qc, non_finite_values_detected_in_w, non_finite_values_detected_in_qr, non_finite_values_detected_in_surface_rain, non_finite_values_detected_in_hfx, non_finite_values_detected_in_qfx, qc_terminal_output_frame_entirely_non_finite, qr_terminal_output_frame_entirely_non_finite, surface_rain_terminal_output_frame_entirely_non_finite, hfx_terminal_output_frame_entirely_non_finite, qfx_terminal_output_frame_entirely_non_finite`
- Low-level qv early response: `0.00014980878158591532` `kg/kg` via `0_1km_thickness_weighted_domain_mean_early_30_90min` (0.013558389163419874 -> 0.013708197945005789); quality `trusted`; full-run delta `unavailable:qv_low_level_response_final_endpoint_entirely_non_finite`
- Low-level theta/temperature early response: `-0.027736507558586254` `K` via `0_1km_thickness_weighted_domain_mean_early_30_90min` (300.6119450520672 -> 300.5842085445086); quality `trusted`; full-run delta `unavailable:th_low_level_response_final_endpoint_entirely_non_finite`
- Caveats: `surface_forcing_is_constant_uniform_proxy, surface_flux_proxy_constant_uniform_not_place_time_energy_budget, surface_flux_proxy_not_real_land_surface_or_evaporation_model, surface_flux_proxy_values_need_local_smoke_validation, science_run_configuration_minimum_duration_6h, configuration_better_suited_to_larger_compute, No artificial atmospheric trigger is applied., Surface heat/moisture fluxes are constant uniform lower-boundary proxy settings; they are not validated place/time surface-energy inputs., Radiation, terrain, GIS surface initialization, and large-scale forcing are not part of v0., Humid/rainy hypotheses remain partial until rain-water-aloft, surface-rain, and reflectivity outputs are present and inspected., CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG, IEEE_DIVIDE_BY_ZERO, IEEE_OVERFLOW_FLAG, IEEE_UNDERFLOW_FLAG, cloud_top_uses_total_hydrometeor_fields:qc,qr,qi,qs,qg, max_height_unavailable_missing_vertical_coordinate, non_finite_values_detected_in_qc, non_finite_values_detected_in_w, non_finite_values_detected_in_qr, non_finite_values_detected_in_surface_rain, non_finite_values_detected_in_hfx, non_finite_values_detected_in_qfx, qc_terminal_output_frame_entirely_non_finite, qr_terminal_output_frame_entirely_non_finite, surface_rain_terminal_output_frame_entirely_non_finite, hfx_terminal_output_frame_entirely_non_finite, qfx_terminal_output_frame_entirely_non_finite, interesting_time_source_field_untrusted`

### phase1_control_high_sensible

- Run ID: `surface_forced_tall_002-phase1_control_high_sensible-56821294e3`
- Result ID: `result-surface_forced_tall_002-phase1_control_high_sensible-56821294e3`
- Status: package `packaged`, run `completed_not_ingested`, ingest `ingested`
- Provenance: Cloud Chamber `c94520049bdb7e3c396dc9a26f33037c4a2762d8`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-f4fa3d80f08f03a8|USM00072558|2026-06-07T18:00:00Z`
- Candidate story: `shallow_cumulus_candidate`
- Required/missing fields: `qv, qc, w, qr, rain, dbz, hfx, qfx` / `none`
- Surface flux fields: hfx `True`, moisture flux `True` via `qfx`
- Surface flux stats: hfx `44.11780548095703`/`44.81328582763672`/`44.4474029038474`, qfx `5.70280863030348e-05`/`5.7927085435949266e-05`/`5.745413364151908e-05`; counts hfx `409600`/`0`/`409600`, qfx `409600`/`0`/`409600`
- Surface flux frame quality: hfx `all 25/25 frames finite`, qfx `all 25/25 frames finite`
- Terminal output contamination: `none`; warnings `CM1 stderr reported floating-point exception flags: IEEE_UNDERFLOW_FLAG`
- Cloud/updraft: first cloud 1800, max cloud top 4591, max qc 0.002924, max w 9.897
- Precipitation/reflectivity: qr yes, surface rain yes, max dBZ 56.08
- Diagnostic trust: `qc trusted, w trusted, qr trusted, surface_rain trusted, dbz trusted`
- Field-quality warnings: `none`
- Low-level qv early response: `0.00015244290594485996` `kg/kg` via `0_1km_thickness_weighted_domain_mean_early_30_90min` (0.013558389163419874 -> 0.013710832069364734); quality `trusted`; full-run delta `0.000244519849981549`
- Low-level theta/temperature early response: `0.0878617688522354` `K` via `0_1km_thickness_weighted_domain_mean_early_30_90min` (300.6119450520672 -> 300.69980682091943); quality `trusted`; full-run delta `0.846182611699362`
- Caveats: `surface_forcing_is_constant_uniform_proxy, surface_flux_proxy_constant_uniform_not_place_time_energy_budget, surface_flux_proxy_not_real_land_surface_or_evaporation_model, surface_flux_proxy_values_need_local_smoke_validation, science_run_configuration_minimum_duration_6h, configuration_better_suited_to_larger_compute, No artificial atmospheric trigger is applied., Surface heat/moisture fluxes are constant uniform lower-boundary proxy settings; they are not validated place/time surface-energy inputs., Radiation, terrain, GIS surface initialization, and large-scale forcing are not part of v0., Humid/rainy hypotheses remain partial until rain-water-aloft, surface-rain, and reflectivity outputs are present and inspected., CM1 stderr reported floating-point exception flags: IEEE_UNDERFLOW_FLAG, cloud_top_uses_total_hydrometeor_fields:qc,qr,qi,qs,qg, max_height_unavailable_missing_vertical_coordinate, no_deep_cloud_detected`

### phase1_control_high_moisture

- Run ID: `surface_forced_tall_002-phase1_control_high_moisture-6d46cf11d1`
- Result ID: `result-surface_forced_tall_002-phase1_control_high_moisture-6d46cf11d1`
- Status: package `packaged`, run `completed_not_ingested`, ingest `ingested`
- Provenance: Cloud Chamber `c94520049bdb7e3c396dc9a26f33037c4a2762d8`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-f4fa3d80f08f03a8|USM00072558|2026-06-07T18:00:00Z`
- Candidate story: `shallow_cumulus_candidate`
- Required/missing fields: `qv, qc, w, qr, rain, dbz, hfx, qfx` / `none`
- Surface flux fields: hfx `True`, moisture flux `True` via `qfx`
- Surface flux stats: hfx `8.318500518798828`/`9.38566780090332`/`8.891412899023853`, qfx `0.00010339190339436755`/`0.00011665589408949018`/`0.00011051272358503895`; counts hfx `409600`/`0`/`409600`, qfx `409600`/`0`/`409600`
- Surface flux frame quality: hfx `all 25/25 frames finite`, qfx `all 25/25 frames finite`
- Terminal output contamination: `none`; warnings `CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG, IEEE_UNDERFLOW_FLAG`
- Cloud/updraft: first cloud 2700, max cloud top 1.087e+04, max qc 0.008663, max w 9.921
- Precipitation/reflectivity: qr yes, surface rain yes, max dBZ 57.01
- Diagnostic trust: `qc trusted, w trusted, qr trusted, surface_rain trusted, dbz trusted`
- Field-quality warnings: `none`
- Low-level qv early response: `0.00032528001756211566` `kg/kg` via `0_1km_thickness_weighted_domain_mean_early_30_90min` (0.013558389163419874 -> 0.01388366918098199); quality `trusted`; full-run delta `0.0009690320854314344`
- Low-level theta/temperature early response: `-0.028184155874384942` `K` via `0_1km_thickness_weighted_domain_mean_early_30_90min` (300.6119450520672 -> 300.5837608961928); quality `trusted`; full-run delta `0.31267307259588506`
- Caveats: `surface_forcing_is_constant_uniform_proxy, surface_flux_proxy_constant_uniform_not_place_time_energy_budget, surface_flux_proxy_not_real_land_surface_or_evaporation_model, surface_flux_proxy_values_need_local_smoke_validation, science_run_configuration_minimum_duration_6h, configuration_better_suited_to_larger_compute, No artificial atmospheric trigger is applied., Surface heat/moisture fluxes are constant uniform lower-boundary proxy settings; they are not validated place/time surface-energy inputs., Radiation, terrain, GIS surface initialization, and large-scale forcing are not part of v0., Humid/rainy hypotheses remain partial until rain-water-aloft, surface-rain, and reflectivity outputs are present and inspected., CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG, IEEE_UNDERFLOW_FLAG, cloud_top_uses_total_hydrometeor_fields:qc,qr,qi,qs,qg, max_height_unavailable_missing_vertical_coordinate`

### phase1_control_high_both

- Run ID: `surface_forced_tall_002-phase1_control_high_both-1c5b253ffb`
- Result ID: `result-surface_forced_tall_002-phase1_control_high_both-1c5b253ffb`
- Status: package `packaged`, run `completed_not_ingested`, ingest `ingested`
- Provenance: Cloud Chamber `c94520049bdb7e3c396dc9a26f33037c4a2762d8`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-f4fa3d80f08f03a8|USM00072558|2026-06-07T18:00:00Z`
- Candidate story: `shallow_cumulus_candidate`
- Required/missing fields: `qv, qc, w, qr, rain, dbz, hfx, qfx` / `none`
- Surface flux fields: hfx `True`, moisture flux `True` via `qfx`
- Surface flux stats: hfx `43.95238494873047`/`44.59759521484375`/`44.39683862362988`, qfx `0.000109258180600591`/`0.00011086207086918876`/`0.00011036302276258069`; counts hfx `409600`/`0`/`409600`, qfx `409600`/`0`/`409600`
- Surface flux frame quality: hfx `all 25/25 frames finite`, qfx `all 25/25 frames finite`
- Terminal output contamination: `none`; warnings `CM1 stderr reported floating-point exception flags: IEEE_UNDERFLOW_FLAG`
- Cloud/updraft: first cloud 1800, max cloud top 5666, max qc 0.003865, max w 12.34
- Precipitation/reflectivity: qr yes, surface rain yes, max dBZ 58.39
- Diagnostic trust: `qc trusted, w trusted, qr trusted, surface_rain trusted, dbz trusted`
- Field-quality warnings: `none`
- Low-level qv early response: `0.00032863593977465813` `kg/kg` via `0_1km_thickness_weighted_domain_mean_early_30_90min` (0.013558389163419874 -> 0.013887025103194532); quality `trusted`; full-run delta `0.0006861705547625309`
- Low-level theta/temperature early response: `0.08773937005958032` `K` via `0_1km_thickness_weighted_domain_mean_early_30_90min` (300.6119450520672 -> 300.6996844221268); quality `trusted`; full-run delta `1.0857133591252364`
- Caveats: `surface_forcing_is_constant_uniform_proxy, surface_flux_proxy_constant_uniform_not_place_time_energy_budget, surface_flux_proxy_not_real_land_surface_or_evaporation_model, surface_flux_proxy_values_need_local_smoke_validation, science_run_configuration_minimum_duration_6h, configuration_better_suited_to_larger_compute, No artificial atmospheric trigger is applied., Surface heat/moisture fluxes are constant uniform lower-boundary proxy settings; they are not validated place/time surface-energy inputs., Radiation, terrain, GIS surface initialization, and large-scale forcing are not part of v0., Humid/rainy hypotheses remain partial until rain-water-aloft, surface-rain, and reflectivity outputs are present and inspected., CM1 stderr reported floating-point exception flags: IEEE_UNDERFLOW_FLAG, cloud_top_uses_total_hydrometeor_fields:qc,qr,qi,qs,qg, max_height_unavailable_missing_vertical_coordinate, no_deep_cloud_detected`

### phase2_easy_deep_default_12km_6h

- Run ID: `surface_forced_tall_002-phase2_easy_deep_default_12km_6h-8bf3806780`
- Result ID: `not ingested`
- Status: package `planned`, run `planned`, ingest `not_started`
- Provenance: Cloud Chamber `unavailable`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-369ae4c88bb32672|USM00072357|2025-05-20T00:00:00Z`
- Candidate story: `supercell_environment`
- Required/missing fields: `unavailable` / `unavailable:until_result_ingested`
- Surface flux fields: hfx `False`, moisture flux `False` via `missing`
- Surface flux stats: hfx `unavailable:until_result_ingested`/`unavailable:until_result_ingested`/`unavailable:until_result_ingested`, qfx `unavailable:until_result_ingested`/`unavailable:until_result_ingested`/`unavailable:until_result_ingested`; counts hfx `0`/`0`/`0`, qfx `0`/`0`/`0`
- Surface flux frame quality: hfx `not assessed`, qfx `not assessed`
- Terminal output contamination: `none`; warnings `none`
- Cloud/updraft: first cloud unavailable, max cloud top unavailable, max qc unavailable, max w unavailable
- Precipitation/reflectivity: qr unavailable, surface rain unavailable, max dBZ unavailable
- Diagnostic trust: `qc unavailable, w unavailable, qr unavailable, surface_rain unavailable, dbz unavailable`
- Field-quality warnings: `none`
- Low-level qv early response: `unavailable:until_result_ingested` `` via `unavailable:until_result_ingested` (unavailable:until_result_ingested -> unavailable:until_result_ingested); quality `unavailable`; full-run delta `unavailable:until_result_ingested`
- Low-level theta/temperature early response: `unavailable:until_result_ingested` `` via `unavailable:until_result_ingested` (unavailable:until_result_ingested -> unavailable:until_result_ingested); quality `unavailable`; full-run delta `unavailable:until_result_ingested`
- Caveats: `surface_forcing_is_constant_uniform_proxy, result_not_ingested`

### phase2_easy_deep_strong_12km_6h

- Run ID: `surface_forced_tall_002-phase2_easy_deep_strong_12km_6h-5ad9bcd1fd`
- Result ID: `not ingested`
- Status: package `planned`, run `planned`, ingest `not_started`
- Provenance: Cloud Chamber `unavailable`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-369ae4c88bb32672|USM00072357|2025-05-20T00:00:00Z`
- Candidate story: `supercell_environment`
- Required/missing fields: `unavailable` / `unavailable:until_result_ingested`
- Surface flux fields: hfx `False`, moisture flux `False` via `missing`
- Surface flux stats: hfx `unavailable:until_result_ingested`/`unavailable:until_result_ingested`/`unavailable:until_result_ingested`, qfx `unavailable:until_result_ingested`/`unavailable:until_result_ingested`/`unavailable:until_result_ingested`; counts hfx `0`/`0`/`0`, qfx `0`/`0`/`0`
- Surface flux frame quality: hfx `not assessed`, qfx `not assessed`
- Terminal output contamination: `none`; warnings `none`
- Cloud/updraft: first cloud unavailable, max cloud top unavailable, max qc unavailable, max w unavailable
- Precipitation/reflectivity: qr unavailable, surface rain unavailable, max dBZ unavailable
- Diagnostic trust: `qc unavailable, w unavailable, qr unavailable, surface_rain unavailable, dbz unavailable`
- Field-quality warnings: `none`
- Low-level qv early response: `unavailable:until_result_ingested` `` via `unavailable:until_result_ingested` (unavailable:until_result_ingested -> unavailable:until_result_ingested); quality `unavailable`; full-run delta `unavailable:until_result_ingested`
- Low-level theta/temperature early response: `unavailable:until_result_ingested` `` via `unavailable:until_result_ingested` (unavailable:until_result_ingested -> unavailable:until_result_ingested); quality `unavailable`; full-run delta `unavailable:until_result_ingested`
- Caveats: `surface_forcing_is_constant_uniform_proxy, result_not_ingested`

### phase2_easy_deep_strong_12km_12h

- Run ID: `surface_forced_tall_002-phase2_easy_deep_strong_12km_12h-4afcd6e8d8`
- Result ID: `not ingested`
- Status: package `planned`, run `planned`, ingest `not_started`
- Provenance: Cloud Chamber `unavailable`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-369ae4c88bb32672|USM00072357|2025-05-20T00:00:00Z`
- Candidate story: `supercell_environment`
- Required/missing fields: `unavailable` / `unavailable:until_result_ingested`
- Surface flux fields: hfx `False`, moisture flux `False` via `missing`
- Surface flux stats: hfx `unavailable:until_result_ingested`/`unavailable:until_result_ingested`/`unavailable:until_result_ingested`, qfx `unavailable:until_result_ingested`/`unavailable:until_result_ingested`/`unavailable:until_result_ingested`; counts hfx `0`/`0`/`0`, qfx `0`/`0`/`0`
- Surface flux frame quality: hfx `not assessed`, qfx `not assessed`
- Terminal output contamination: `none`; warnings `none`
- Cloud/updraft: first cloud unavailable, max cloud top unavailable, max qc unavailable, max w unavailable
- Precipitation/reflectivity: qr unavailable, surface rain unavailable, max dBZ unavailable
- Diagnostic trust: `qc unavailable, w unavailable, qr unavailable, surface_rain unavailable, dbz unavailable`
- Field-quality warnings: `none`
- Low-level qv early response: `unavailable:until_result_ingested` `` via `unavailable:until_result_ingested` (unavailable:until_result_ingested -> unavailable:until_result_ingested); quality `unavailable`; full-run delta `unavailable:until_result_ingested`
- Low-level theta/temperature early response: `unavailable:until_result_ingested` `` via `unavailable:until_result_ingested` (unavailable:until_result_ingested -> unavailable:until_result_ingested); quality `unavailable`; full-run delta `unavailable:until_result_ingested`
- Caveats: `surface_forcing_is_constant_uniform_proxy, result_not_ingested`

### phase2_easy_deep_strong_60km_12h

- Run ID: `surface_forced_tall_002-phase2_easy_deep_strong_60km_12h-aaa54b1010`
- Result ID: `not ingested`
- Status: package `planned`, run `planned`, ingest `not_started`
- Provenance: Cloud Chamber `unavailable`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-369ae4c88bb32672|USM00072357|2025-05-20T00:00:00Z`
- Candidate story: `supercell_environment`
- Required/missing fields: `unavailable` / `unavailable:until_result_ingested`
- Surface flux fields: hfx `False`, moisture flux `False` via `missing`
- Surface flux stats: hfx `unavailable:until_result_ingested`/`unavailable:until_result_ingested`/`unavailable:until_result_ingested`, qfx `unavailable:until_result_ingested`/`unavailable:until_result_ingested`/`unavailable:until_result_ingested`; counts hfx `0`/`0`/`0`, qfx `0`/`0`/`0`
- Surface flux frame quality: hfx `not assessed`, qfx `not assessed`
- Terminal output contamination: `none`; warnings `none`
- Cloud/updraft: first cloud unavailable, max cloud top unavailable, max qc unavailable, max w unavailable
- Precipitation/reflectivity: qr unavailable, surface rain unavailable, max dBZ unavailable
- Diagnostic trust: `qc unavailable, w unavailable, qr unavailable, surface_rain unavailable, dbz unavailable`
- Field-quality warnings: `none`
- Low-level qv early response: `unavailable:until_result_ingested` `` via `unavailable:until_result_ingested` (unavailable:until_result_ingested -> unavailable:until_result_ingested); quality `unavailable`; full-run delta `unavailable:until_result_ingested`
- Low-level theta/temperature early response: `unavailable:until_result_ingested` `` via `unavailable:until_result_ingested` (unavailable:until_result_ingested -> unavailable:until_result_ingested); quality `unavailable`; full-run delta `unavailable:until_result_ingested`
- Caveats: `surface_forcing_is_constant_uniform_proxy, result_not_ingested`

### phase2_easy_deep_strong_120km_12h_optional

- Run ID: `surface_forced_tall_002-phase2_easy_deep_strong_120km_12h_optional-477214201d`
- Result ID: `not ingested`
- Status: package `planned`, run `planned`, ingest `not_started`
- Provenance: Cloud Chamber `unavailable`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-369ae4c88bb32672|USM00072357|2025-05-20T00:00:00Z`
- Candidate story: `supercell_environment`
- Required/missing fields: `unavailable` / `unavailable:until_result_ingested`
- Surface flux fields: hfx `False`, moisture flux `False` via `missing`
- Surface flux stats: hfx `unavailable:until_result_ingested`/`unavailable:until_result_ingested`/`unavailable:until_result_ingested`, qfx `unavailable:until_result_ingested`/`unavailable:until_result_ingested`/`unavailable:until_result_ingested`; counts hfx `0`/`0`/`0`, qfx `0`/`0`/`0`
- Surface flux frame quality: hfx `not assessed`, qfx `not assessed`
- Terminal output contamination: `none`; warnings `none`
- Cloud/updraft: first cloud unavailable, max cloud top unavailable, max qc unavailable, max w unavailable
- Precipitation/reflectivity: qr unavailable, surface rain unavailable, max dBZ unavailable
- Diagnostic trust: `qc unavailable, w unavailable, qr unavailable, surface_rain unavailable, dbz unavailable`
- Field-quality warnings: `none`
- Low-level qv early response: `unavailable:until_result_ingested` `` via `unavailable:until_result_ingested` (unavailable:until_result_ingested -> unavailable:until_result_ingested); quality `unavailable`; full-run delta `unavailable:until_result_ingested`
- Low-level theta/temperature early response: `unavailable:until_result_ingested` `` via `unavailable:until_result_ingested` (unavailable:until_result_ingested -> unavailable:until_result_ingested); quality `unavailable`; full-run delta `unavailable:until_result_ingested`
- Caveats: `surface_forcing_is_constant_uniform_proxy, optional_campaign_run, result_not_ingested`

### phase3_weak_control_strong_60km_12h

- Run ID: `surface_forced_tall_002-phase3_weak_control_strong_60km_12h-96fe6460b1`
- Result ID: `not ingested`
- Status: package `planned`, run `planned`, ingest `not_started`
- Provenance: Cloud Chamber `unavailable`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-05af14d176e118b8|USM00072662|2025-07-09T18:00:00Z`
- Candidate story: `dry_failed_candidate`
- Required/missing fields: `unavailable` / `unavailable:until_result_ingested`
- Surface flux fields: hfx `False`, moisture flux `False` via `missing`
- Surface flux stats: hfx `unavailable:until_result_ingested`/`unavailable:until_result_ingested`/`unavailable:until_result_ingested`, qfx `unavailable:until_result_ingested`/`unavailable:until_result_ingested`/`unavailable:until_result_ingested`; counts hfx `0`/`0`/`0`, qfx `0`/`0`/`0`
- Surface flux frame quality: hfx `not assessed`, qfx `not assessed`
- Terminal output contamination: `none`; warnings `none`
- Cloud/updraft: first cloud unavailable, max cloud top unavailable, max qc unavailable, max w unavailable
- Precipitation/reflectivity: qr unavailable, surface rain unavailable, max dBZ unavailable
- Diagnostic trust: `qc unavailable, w unavailable, qr unavailable, surface_rain unavailable, dbz unavailable`
- Field-quality warnings: `none`
- Low-level qv early response: `unavailable:until_result_ingested` `` via `unavailable:until_result_ingested` (unavailable:until_result_ingested -> unavailable:until_result_ingested); quality `unavailable`; full-run delta `unavailable:until_result_ingested`
- Low-level theta/temperature early response: `unavailable:until_result_ingested` `` via `unavailable:until_result_ingested` (unavailable:until_result_ingested -> unavailable:until_result_ingested); quality `unavailable`; full-run delta `unavailable:until_result_ingested`
- Caveats: `surface_forcing_is_constant_uniform_proxy, result_not_ingested`

## Forcing Response

Phase 1 produced finite hfx/qfx means that can be directionally reviewed, but emitted surface-flux verification remains blocked because terminal output-frame contamination makes at least one matched run untrusted.

## Surface Flux Response

- `phase1_control_high_sensible` vs `phase1_control_default_flux`: `surface_flux_response_inconclusive_missing_evidence`
  - Unavailable evidence: `control:hfx_terminal_output_frame_entirely_non_finite, control:qfx_terminal_output_frame_entirely_non_finite`
- `phase1_control_high_moisture` vs `phase1_control_default_flux`: `surface_flux_response_inconclusive_missing_evidence`
  - Unavailable evidence: `control:hfx_terminal_output_frame_entirely_non_finite, control:qfx_terminal_output_frame_entirely_non_finite`
- `phase1_control_high_both` vs `phase1_control_default_flux`: `surface_flux_response_inconclusive_missing_evidence`
  - Unavailable evidence: `control:hfx_terminal_output_frame_entirely_non_finite, control:qfx_terminal_output_frame_entirely_non_finite`

## Low-Level Response

- `phase1_control_high_sensible` vs `phase1_control_default_flux`: `low_level_response_verified`
  - low_level_theta_or_temperature_early_response_delta: required; expected `increase`, observed `increase`; `verified`; quality `trusted`
  - low_level_qv_early_response_delta: informational; expected `comparable`, observed `increase`; `informational`; quality `trusted`
- `phase1_control_high_moisture` vs `phase1_control_default_flux`: `low_level_response_verified`
  - low_level_theta_or_temperature_early_response_delta: informational; expected `comparable`, observed `decrease`; `informational`; quality `trusted`
  - low_level_qv_early_response_delta: required; expected `increase`, observed `increase`; `verified`; quality `trusted`
- `phase1_control_high_both` vs `phase1_control_default_flux`: `low_level_response_verified`
  - low_level_theta_or_temperature_early_response_delta: required; expected `increase`, observed `increase`; `verified`; quality `trusted`
  - low_level_qv_early_response_delta: required; expected `increase`, observed `increase`; `verified`; quality `trusted`

## Matched Comparisons

### phase1_control_high_sensible vs phase1_control_default_flux

- Type: `heat_flux_sensitivity`
- Status: `comparable`
- Varied fields: `surface_heat_flux_k_m_s, cm1_cnst_shflx`
- Equality failures: `[]`
- Unavailable evidence: `none`
- Interpretation: Required comparison gates passed; inspect supported differences without treating them as predicted-vs-actual verdicts.

### phase1_control_high_moisture vs phase1_control_default_flux

- Type: `moisture_flux_sensitivity`
- Status: `comparable`
- Varied fields: `surface_moisture_flux_g_g_m_s, cm1_cnst_lhflx`
- Equality failures: `[]`
- Unavailable evidence: `none`
- Interpretation: Required comparison gates passed; inspect supported differences without treating them as predicted-vs-actual verdicts.

### phase1_control_high_both vs phase1_control_default_flux

- Type: `combined_flux_sensitivity`
- Status: `comparable`
- Varied fields: `surface_heat_flux_k_m_s, surface_moisture_flux_g_g_m_s, cm1_cnst_shflx, cm1_cnst_lhflx`
- Equality failures: `[]`
- Unavailable evidence: `none`
- Interpretation: Required comparison gates passed; inspect supported differences without treating them as predicted-vs-actual verdicts.

### phase2_easy_deep_strong_12km_6h vs phase2_easy_deep_default_12km_6h

- Type: `forcing_sensitivity_same_duration`
- Status: `inconclusive_missing_evidence`
- Varied fields: `surface_heat_flux_k_m_s, surface_moisture_flux_g_g_m_s, cm1_cnst_shflx, cm1_cnst_lhflx`
- Equality failures: `[]`
- Unavailable evidence: `control:result_not_ingested, control:missing_required_field:hfx, control:missing_required_field:qfx, control:missing_required_field:qv, control:missing_required_field:th_or_temperature, control:missing_required_field:qc, control:missing_required_field:w, control:diagnostic_unavailable:surface_fluxes, control:diagnostic_unavailable:low_level_response, control:diagnostic_unavailable:cloud, control:diagnostic_unavailable:vertical_velocity, experiment:result_not_ingested, experiment:missing_required_field:hfx, experiment:missing_required_field:qfx, experiment:missing_required_field:qv, experiment:missing_required_field:th_or_temperature, experiment:missing_required_field:qc, experiment:missing_required_field:w, experiment:diagnostic_unavailable:surface_fluxes, experiment:diagnostic_unavailable:low_level_response, experiment:diagnostic_unavailable:cloud, experiment:diagnostic_unavailable:vertical_velocity`
- Interpretation: Runs are structurally comparable, but required output fields or diagnostics are unavailable.

### phase2_easy_deep_strong_12km_12h vs phase2_easy_deep_strong_12km_6h

- Type: `duration_sensitivity_same_forcing`
- Status: `inconclusive_missing_evidence`
- Varied fields: `duration, runtime_seconds, expected_output_frames, expected_output_volume`
- Equality failures: `[]`
- Unavailable evidence: `control:result_not_ingested, control:missing_required_field:hfx, control:missing_required_field:qfx, control:missing_required_field:qv, control:missing_required_field:th_or_temperature, control:missing_required_field:qc, control:missing_required_field:w, control:diagnostic_unavailable:surface_fluxes, control:diagnostic_unavailable:low_level_response, control:diagnostic_unavailable:cloud, control:diagnostic_unavailable:vertical_velocity, experiment:result_not_ingested, experiment:missing_required_field:hfx, experiment:missing_required_field:qfx, experiment:missing_required_field:qv, experiment:missing_required_field:th_or_temperature, experiment:missing_required_field:qc, experiment:missing_required_field:w, experiment:diagnostic_unavailable:surface_fluxes, experiment:diagnostic_unavailable:low_level_response, experiment:diagnostic_unavailable:cloud, experiment:diagnostic_unavailable:vertical_velocity`
- Interpretation: Runs are structurally comparable, but required output fields or diagnostics are unavailable.

### phase2_easy_deep_strong_60km_12h vs phase2_easy_deep_strong_12km_12h

- Type: `domain_grid_bundle_sensitivity`
- Status: `inconclusive_missing_evidence`
- Varied fields: `domain_size, nx, ny, nz, dx_m, dy_m, dz_m, stretch_z, str_bot_m, str_top_m, dz_bot_m, dz_top_m, model_top_m, expected_output_volume`
- Equality failures: `[]`
- Unavailable evidence: `control:result_not_ingested, control:missing_required_field:hfx, control:missing_required_field:qfx, control:missing_required_field:qv, control:missing_required_field:th_or_temperature, control:missing_required_field:qc, control:missing_required_field:w, control:diagnostic_unavailable:surface_fluxes, control:diagnostic_unavailable:low_level_response, control:diagnostic_unavailable:cloud, control:diagnostic_unavailable:vertical_velocity, experiment:result_not_ingested, experiment:missing_required_field:hfx, experiment:missing_required_field:qfx, experiment:missing_required_field:qv, experiment:missing_required_field:th_or_temperature, experiment:missing_required_field:qc, experiment:missing_required_field:w, experiment:diagnostic_unavailable:surface_fluxes, experiment:diagnostic_unavailable:low_level_response, experiment:diagnostic_unavailable:cloud, experiment:diagnostic_unavailable:vertical_velocity`
- Interpretation: Runs are structurally comparable, but required output fields or diagnostics are unavailable.

### phase2_easy_deep_strong_120km_12h_optional vs phase2_easy_deep_strong_60km_12h

- Type: `domain_grid_bundle_sensitivity`
- Status: `inconclusive_missing_evidence`
- Varied fields: `domain_size, nx, ny, nz, dx_m, dy_m, dz_m, stretch_z, str_bot_m, str_top_m, dz_bot_m, dz_top_m, model_top_m, expected_output_volume`
- Equality failures: `[]`
- Unavailable evidence: `control:result_not_ingested, control:missing_required_field:hfx, control:missing_required_field:qfx, control:missing_required_field:qv, control:missing_required_field:th_or_temperature, control:missing_required_field:qc, control:missing_required_field:w, control:diagnostic_unavailable:surface_fluxes, control:diagnostic_unavailable:low_level_response, control:diagnostic_unavailable:cloud, control:diagnostic_unavailable:vertical_velocity, experiment:result_not_ingested, experiment:missing_required_field:hfx, experiment:missing_required_field:qfx, experiment:missing_required_field:qv, experiment:missing_required_field:th_or_temperature, experiment:missing_required_field:qc, experiment:missing_required_field:w, experiment:diagnostic_unavailable:surface_fluxes, experiment:diagnostic_unavailable:low_level_response, experiment:diagnostic_unavailable:cloud, experiment:diagnostic_unavailable:vertical_velocity`
- Interpretation: Runs are structurally comparable, but required output fields or diagnostics are unavailable.

### phase3_weak_control_strong_60km_12h vs phase2_easy_deep_strong_60km_12h

- Type: `cross_sounding_discrimination`
- Status: `inconclusive_missing_evidence`
- Varied fields: `selection_id, station_id, valid_time_utc, candidate_id, candidate_story, candidate_score, candidate_evidence, candidate_caveats`
- Equality failures: `[]`
- Unavailable evidence: `control:result_not_ingested, control:missing_required_field:hfx, control:missing_required_field:qfx, control:missing_required_field:qv, control:missing_required_field:th_or_temperature, control:missing_required_field:qc, control:missing_required_field:w, control:diagnostic_unavailable:surface_fluxes, control:diagnostic_unavailable:low_level_response, control:diagnostic_unavailable:cloud, control:diagnostic_unavailable:vertical_velocity, experiment:result_not_ingested, experiment:missing_required_field:hfx, experiment:missing_required_field:qfx, experiment:missing_required_field:qv, experiment:missing_required_field:th_or_temperature, experiment:missing_required_field:qc, experiment:missing_required_field:w, experiment:diagnostic_unavailable:surface_fluxes, experiment:diagnostic_unavailable:low_level_response, experiment:diagnostic_unavailable:cloud, experiment:diagnostic_unavailable:vertical_velocity`
- Interpretation: Runs are structurally comparable, but required output fields or diagnostics are unavailable.

## Deepening And Class Differences

Deepening and class-difference evidence is listed per run above. This report does not convert those diagnostics into predicted-vs-actual verdicts.

## Unavailable Or Missing Diagnostics

- low_level_qv_response
- low_level_theta_or_temperature_response

## Preliminary Diagnosis Categories

- cloud_depth_evidence_available
- ingested_results_available_for_review
- surface_flux_outputs_present_in_at_least_one_result

## Recommended Follow-Up Issues

- Review campaign rows with unavailable required output fields before scientific conclusions.
- Resolve Phase 1 surface-flux response comparisons before treating selected forcing changes as verified in CM1 output.
- Review caveated or untrusted non-finite fields before using cloud, updraft, rain-water, surface-rain, or reflectivity outcomes as scientific evidence.
