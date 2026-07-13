# Surface-Forced Campaign Report: surface_forced_tall_001

Campaign ID: `surface_forced_tall_001`
Protocol: `docs/research/surface-forced-sounding-verification-protocol.md`
Matrix file: `surface_forced_tall_001.yaml` (runtime-local path omitted)
Generated: `2026-07-13T15:13:40.086342+00:00`

## Objective

Verify that numeric uniform lower-boundary heat/moisture forcing is preserved through package generation, CM1 execution, ingest, and reporting after correcting the CM1 vertical grid to an 18 km stretched domain; then gate deeper sounding-response checks on the Phase 1 evidence.

## Matrix Summary

- Runs planned: 10
- Status counts: `{"ingested": 4, "planned": 6}`
- Phase gate state: `forcing_wiring_verified_but_response_not_verified`

## Operator Overrides

No operator phase-gate overrides were recorded.

## Run Table

| Matrix ID | Status | Station/time | Forcing | Grid/domain | Key result |
| --- | --- | --- | --- | --- | --- |
| phase1_control_default_flux | ingested | VALLEY; NE. 2026-06-07T18:00:00Z | H 0.008 K m/s; M 5.2e-05 g/g m/s | wide_12km 128 dx 100.0 m | cloud top 1.087e+04; max w 4.209; surface rain True |
| phase1_control_high_sensible | ingested | VALLEY; NE. 2026-06-07T18:00:00Z | H 0.04 K m/s; M 5.2e-05 g/g m/s | wide_12km 128 dx 100.0 m | cloud top 4591; max w 9.897; surface rain True |
| phase1_control_high_moisture | ingested | VALLEY; NE. 2026-06-07T18:00:00Z | H 0.008 K m/s; M 0.0001 g/g m/s | wide_12km 128 dx 100.0 m | cloud top 1.087e+04; max w 9.921; surface rain True |
| phase1_control_high_both | ingested | VALLEY; NE. 2026-06-07T18:00:00Z | H 0.04 K m/s; M 0.0001 g/g m/s | wide_12km 128 dx 100.0 m | cloud top 5666; max w 12.34; surface rain True |
| phase2_easy_deep_default_12km_6h | planned | unavailable time unavailable | H 0.008 K m/s; M 5.2e-05 g/g m/s | wide_12km 128 dx 100.0 m | planned |
| phase2_easy_deep_strong_12km_6h | planned | unavailable time unavailable | H 0.04 K m/s; M 0.0001 g/g m/s | wide_12km 128 dx 100.0 m | planned |
| phase2_easy_deep_strong_12km_12h | planned | unavailable time unavailable | H 0.04 K m/s; M 0.0001 g/g m/s | wide_12km 128 dx 100.0 m | planned |
| phase2_easy_deep_strong_60km_12h | planned | unavailable time unavailable | H 0.04 K m/s; M 0.0001 g/g m/s | regional_60km 128 dx 468.75 m | planned |
| phase2_easy_deep_strong_120km_12h_optional | planned | unavailable time unavailable | H 0.04 K m/s; M 0.0001 g/g m/s | regional_120km 128 dx 937.5 m | planned |
| phase3_weak_control_strong_60km_12h | planned | unavailable time unavailable | H 0.04 K m/s; M 0.0001 g/g m/s | regional_60km 128 dx 468.75 m | planned |

## Per-Run Evidence

### phase1_control_default_flux

- Run ID: `surface_forced_tall_001-phase1_control_default_flux-08be7858a2`
- Result ID: `result-surface_forced_tall_001-phase1_control_default_flux-08be7858a2`
- Status: package `packaged`, run `completed_not_ingested`, ingest `ingested`
- Provenance: Cloud Chamber `e849de18abd9a63a41e492aea07483cea8a77a4d`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-f4fa3d80f08f03a8|USM00072558|2026-06-07T18:00:00Z`
- Candidate story: `shallow_cumulus_candidate`
- Required/missing fields: `qv, qc, w, qr, rain, dbz, hfx, qfx` / `none`
- Surface flux fields: hfx `True`, moisture flux `True` via `qfx`
- Surface flux stats: hfx `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`, moisture `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`
- Cloud/updraft: first cloud `6300`, max cloud top `1.087e+04`, max qc `0.005951`, max w `4.209`
- Precipitation/reflectivity: qr `True`, surface rain `True`, max dBZ `29.5`
- Low-level response: `low_level_response_diagnostic_not_implemented`
- Caveats: `surface_forcing_is_constant_uniform_proxy, low_level_response_diagnostic_not_implemented, surface_flux_proxy_constant_uniform_not_place_time_energy_budget, surface_flux_proxy_not_real_land_surface_or_evaporation_model, surface_flux_proxy_values_need_local_smoke_validation, science_run_configuration_minimum_duration_6h, configuration_better_suited_to_larger_compute, No artificial atmospheric trigger is applied., Surface heat/moisture fluxes are constant uniform lower-boundary proxy settings; they are not validated place/time surface-energy inputs., Radiation, terrain, GIS surface initialization, and large-scale forcing are not part of v0., Humid/rainy hypotheses remain partial until rain-water-aloft, surface-rain, and reflectivity outputs are present and inspected., CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG, IEEE_DIVIDE_BY_ZERO, IEEE_OVERFLOW_FLAG, IEEE_UNDERFLOW_FLAG, cloud_top_uses_total_hydrometeor_fields:qc,qr,qi,qs,qg, max_height_unavailable_missing_vertical_coordinate, non_finite_values_detected_in_qc, qc_field_entirely_non_finite, non_finite_values_detected_in_w, non_finite_values_detected_in_qr, qr_field_entirely_non_finite, non_finite_values_detected_in_surface_rain, surface_rain_field_entirely_non_finite`

### phase1_control_high_sensible

- Run ID: `surface_forced_tall_001-phase1_control_high_sensible-5affb21c4f`
- Result ID: `result-surface_forced_tall_001-phase1_control_high_sensible-5affb21c4f`
- Status: package `packaged`, run `completed_not_ingested`, ingest `ingested`
- Provenance: Cloud Chamber `e849de18abd9a63a41e492aea07483cea8a77a4d`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-f4fa3d80f08f03a8|USM00072558|2026-06-07T18:00:00Z`
- Candidate story: `shallow_cumulus_candidate`
- Required/missing fields: `qv, qc, w, qr, rain, dbz, hfx, qfx` / `none`
- Surface flux fields: hfx `True`, moisture flux `True` via `qfx`
- Surface flux stats: hfx `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`, moisture `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`
- Cloud/updraft: first cloud `1800`, max cloud top `4591`, max qc `0.002924`, max w `9.897`
- Precipitation/reflectivity: qr `True`, surface rain `True`, max dBZ `56.08`
- Low-level response: `low_level_response_diagnostic_not_implemented`
- Caveats: `surface_forcing_is_constant_uniform_proxy, low_level_response_diagnostic_not_implemented, surface_flux_proxy_constant_uniform_not_place_time_energy_budget, surface_flux_proxy_not_real_land_surface_or_evaporation_model, surface_flux_proxy_values_need_local_smoke_validation, science_run_configuration_minimum_duration_6h, configuration_better_suited_to_larger_compute, No artificial atmospheric trigger is applied., Surface heat/moisture fluxes are constant uniform lower-boundary proxy settings; they are not validated place/time surface-energy inputs., Radiation, terrain, GIS surface initialization, and large-scale forcing are not part of v0., Humid/rainy hypotheses remain partial until rain-water-aloft, surface-rain, and reflectivity outputs are present and inspected., CM1 stderr reported floating-point exception flags: IEEE_UNDERFLOW_FLAG, cloud_top_uses_total_hydrometeor_fields:qc,qr,qi,qs,qg, max_height_unavailable_missing_vertical_coordinate, no_deep_cloud_detected`

### phase1_control_high_moisture

- Run ID: `surface_forced_tall_001-phase1_control_high_moisture-7723f4bbb5`
- Result ID: `result-surface_forced_tall_001-phase1_control_high_moisture-7723f4bbb5`
- Status: package `packaged`, run `completed_not_ingested`, ingest `ingested`
- Provenance: Cloud Chamber `e849de18abd9a63a41e492aea07483cea8a77a4d`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-f4fa3d80f08f03a8|USM00072558|2026-06-07T18:00:00Z`
- Candidate story: `shallow_cumulus_candidate`
- Required/missing fields: `qv, qc, w, qr, rain, dbz, hfx, qfx` / `none`
- Surface flux fields: hfx `True`, moisture flux `True` via `qfx`
- Surface flux stats: hfx `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`, moisture `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`
- Cloud/updraft: first cloud `2700`, max cloud top `1.087e+04`, max qc `0.008663`, max w `9.921`
- Precipitation/reflectivity: qr `True`, surface rain `True`, max dBZ `57.01`
- Low-level response: `low_level_response_diagnostic_not_implemented`
- Caveats: `surface_forcing_is_constant_uniform_proxy, low_level_response_diagnostic_not_implemented, surface_flux_proxy_constant_uniform_not_place_time_energy_budget, surface_flux_proxy_not_real_land_surface_or_evaporation_model, surface_flux_proxy_values_need_local_smoke_validation, science_run_configuration_minimum_duration_6h, configuration_better_suited_to_larger_compute, No artificial atmospheric trigger is applied., Surface heat/moisture fluxes are constant uniform lower-boundary proxy settings; they are not validated place/time surface-energy inputs., Radiation, terrain, GIS surface initialization, and large-scale forcing are not part of v0., Humid/rainy hypotheses remain partial until rain-water-aloft, surface-rain, and reflectivity outputs are present and inspected., CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG, IEEE_UNDERFLOW_FLAG, cloud_top_uses_total_hydrometeor_fields:qc,qr,qi,qs,qg, max_height_unavailable_missing_vertical_coordinate`

### phase1_control_high_both

- Run ID: `surface_forced_tall_001-phase1_control_high_both-827ee2275b`
- Result ID: `result-surface_forced_tall_001-phase1_control_high_both-827ee2275b`
- Status: package `packaged`, run `completed_not_ingested`, ingest `ingested`
- Provenance: Cloud Chamber `e849de18abd9a63a41e492aea07483cea8a77a4d`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-f4fa3d80f08f03a8|USM00072558|2026-06-07T18:00:00Z`
- Candidate story: `shallow_cumulus_candidate`
- Required/missing fields: `qv, qc, w, qr, rain, dbz, hfx, qfx` / `none`
- Surface flux fields: hfx `True`, moisture flux `True` via `qfx`
- Surface flux stats: hfx `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`, moisture `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`
- Cloud/updraft: first cloud `1800`, max cloud top `5666`, max qc `0.003865`, max w `12.34`
- Precipitation/reflectivity: qr `True`, surface rain `True`, max dBZ `58.39`
- Low-level response: `low_level_response_diagnostic_not_implemented`
- Caveats: `surface_forcing_is_constant_uniform_proxy, low_level_response_diagnostic_not_implemented, surface_flux_proxy_constant_uniform_not_place_time_energy_budget, surface_flux_proxy_not_real_land_surface_or_evaporation_model, surface_flux_proxy_values_need_local_smoke_validation, science_run_configuration_minimum_duration_6h, configuration_better_suited_to_larger_compute, No artificial atmospheric trigger is applied., Surface heat/moisture fluxes are constant uniform lower-boundary proxy settings; they are not validated place/time surface-energy inputs., Radiation, terrain, GIS surface initialization, and large-scale forcing are not part of v0., Humid/rainy hypotheses remain partial until rain-water-aloft, surface-rain, and reflectivity outputs are present and inspected., CM1 stderr reported floating-point exception flags: IEEE_UNDERFLOW_FLAG, cloud_top_uses_total_hydrometeor_fields:qc,qr,qi,qs,qg, max_height_unavailable_missing_vertical_coordinate, no_deep_cloud_detected`

### phase2_easy_deep_default_12km_6h

- Run ID: `surface_forced_tall_001-phase2_easy_deep_default_12km_6h-980e50b066`
- Result ID: `not ingested`
- Status: package `planned`, run `planned`, ingest `not_started`
- Provenance: Cloud Chamber `unavailable`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-369ae4c88bb32672|USM00072357|2025-05-20T00:00:00Z`
- Candidate story: `supercell_environment`
- Required/missing fields: `unavailable` / `unavailable:until_result_ingested`
- Surface flux fields: hfx `False`, moisture flux `False` via `missing`
- Surface flux stats: hfx `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`, moisture `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`
- Cloud/updraft: first cloud `unavailable`, max cloud top `unavailable`, max qc `unavailable`, max w `unavailable`
- Precipitation/reflectivity: qr `None`, surface rain `None`, max dBZ `unavailable`
- Low-level response: `low_level_response_diagnostic_not_implemented`
- Caveats: `surface_forcing_is_constant_uniform_proxy, low_level_response_diagnostic_not_implemented, result_not_ingested`

### phase2_easy_deep_strong_12km_6h

- Run ID: `surface_forced_tall_001-phase2_easy_deep_strong_12km_6h-8b39476448`
- Result ID: `not ingested`
- Status: package `planned`, run `planned`, ingest `not_started`
- Provenance: Cloud Chamber `unavailable`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-369ae4c88bb32672|USM00072357|2025-05-20T00:00:00Z`
- Candidate story: `supercell_environment`
- Required/missing fields: `unavailable` / `unavailable:until_result_ingested`
- Surface flux fields: hfx `False`, moisture flux `False` via `missing`
- Surface flux stats: hfx `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`, moisture `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`
- Cloud/updraft: first cloud `unavailable`, max cloud top `unavailable`, max qc `unavailable`, max w `unavailable`
- Precipitation/reflectivity: qr `None`, surface rain `None`, max dBZ `unavailable`
- Low-level response: `low_level_response_diagnostic_not_implemented`
- Caveats: `surface_forcing_is_constant_uniform_proxy, low_level_response_diagnostic_not_implemented, result_not_ingested`

### phase2_easy_deep_strong_12km_12h

- Run ID: `surface_forced_tall_001-phase2_easy_deep_strong_12km_12h-dbd29c93ae`
- Result ID: `not ingested`
- Status: package `planned`, run `planned`, ingest `not_started`
- Provenance: Cloud Chamber `unavailable`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-369ae4c88bb32672|USM00072357|2025-05-20T00:00:00Z`
- Candidate story: `supercell_environment`
- Required/missing fields: `unavailable` / `unavailable:until_result_ingested`
- Surface flux fields: hfx `False`, moisture flux `False` via `missing`
- Surface flux stats: hfx `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`, moisture `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`
- Cloud/updraft: first cloud `unavailable`, max cloud top `unavailable`, max qc `unavailable`, max w `unavailable`
- Precipitation/reflectivity: qr `None`, surface rain `None`, max dBZ `unavailable`
- Low-level response: `low_level_response_diagnostic_not_implemented`
- Caveats: `surface_forcing_is_constant_uniform_proxy, low_level_response_diagnostic_not_implemented, result_not_ingested`

### phase2_easy_deep_strong_60km_12h

- Run ID: `surface_forced_tall_001-phase2_easy_deep_strong_60km_12h-e565ebb186`
- Result ID: `not ingested`
- Status: package `planned`, run `planned`, ingest `not_started`
- Provenance: Cloud Chamber `unavailable`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-369ae4c88bb32672|USM00072357|2025-05-20T00:00:00Z`
- Candidate story: `supercell_environment`
- Required/missing fields: `unavailable` / `unavailable:until_result_ingested`
- Surface flux fields: hfx `False`, moisture flux `False` via `missing`
- Surface flux stats: hfx `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`, moisture `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`
- Cloud/updraft: first cloud `unavailable`, max cloud top `unavailable`, max qc `unavailable`, max w `unavailable`
- Precipitation/reflectivity: qr `None`, surface rain `None`, max dBZ `unavailable`
- Low-level response: `low_level_response_diagnostic_not_implemented`
- Caveats: `surface_forcing_is_constant_uniform_proxy, low_level_response_diagnostic_not_implemented, result_not_ingested`

### phase2_easy_deep_strong_120km_12h_optional

- Run ID: `surface_forced_tall_001-phase2_easy_deep_strong_120km_12h_optional-049ecaf4b7`
- Result ID: `not ingested`
- Status: package `planned`, run `planned`, ingest `not_started`
- Provenance: Cloud Chamber `unavailable`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-369ae4c88bb32672|USM00072357|2025-05-20T00:00:00Z`
- Candidate story: `supercell_environment`
- Required/missing fields: `unavailable` / `unavailable:until_result_ingested`
- Surface flux fields: hfx `False`, moisture flux `False` via `missing`
- Surface flux stats: hfx `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`, moisture `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`
- Cloud/updraft: first cloud `unavailable`, max cloud top `unavailable`, max qc `unavailable`, max w `unavailable`
- Precipitation/reflectivity: qr `None`, surface rain `None`, max dBZ `unavailable`
- Low-level response: `low_level_response_diagnostic_not_implemented`
- Caveats: `surface_forcing_is_constant_uniform_proxy, low_level_response_diagnostic_not_implemented, optional_campaign_run, result_not_ingested`

### phase3_weak_control_strong_60km_12h

- Run ID: `surface_forced_tall_001-phase3_weak_control_strong_60km_12h-58265c71a6`
- Result ID: `not ingested`
- Status: package `planned`, run `planned`, ingest `not_started`
- Provenance: Cloud Chamber `unavailable`, CM1 `unavailable:cm1_version_not_recorded`
- Source: `cached_recommendation` `sounding-candidate-05af14d176e118b8|USM00072662|2025-07-09T18:00:00Z`
- Candidate story: `dry_failed_candidate`
- Required/missing fields: `unavailable` / `unavailable:until_result_ingested`
- Surface flux fields: hfx `False`, moisture flux `False` via `missing`
- Surface flux stats: hfx `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`, moisture `unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`/`unavailable:surface_flux_statistics_not_implemented`
- Cloud/updraft: first cloud `unavailable`, max cloud top `unavailable`, max qc `unavailable`, max w `unavailable`
- Precipitation/reflectivity: qr `None`, surface rain `None`, max dBZ `unavailable`
- Low-level response: `low_level_response_diagnostic_not_implemented`
- Caveats: `surface_forcing_is_constant_uniform_proxy, low_level_response_diagnostic_not_implemented, result_not_ingested`

## Forcing Response

Surface-flux output fields are present in at least one ingested result, but standardized low-level response diagnostics are not implemented yet.

## Matched Comparisons

### phase1_control_high_sensible vs phase1_control_default_flux

- Type: `heat_flux_sensitivity`
- Status: `inconclusive_missing_evidence`
- Varied fields: `surface_heat_flux_k_m_s, cm1_cnst_shflx`
- Equality failures: `[]`
- Unavailable evidence: `control:diagnostic_unavailable:low_level_response, experiment:diagnostic_unavailable:low_level_response`
- Interpretation: Runs are structurally comparable, but required output fields or diagnostics are unavailable.

### phase1_control_high_moisture vs phase1_control_default_flux

- Type: `moisture_flux_sensitivity`
- Status: `inconclusive_missing_evidence`
- Varied fields: `surface_moisture_flux_g_g_m_s, cm1_cnst_lhflx`
- Equality failures: `[]`
- Unavailable evidence: `control:diagnostic_unavailable:low_level_response, experiment:diagnostic_unavailable:low_level_response`
- Interpretation: Runs are structurally comparable, but required output fields or diagnostics are unavailable.

### phase1_control_high_both vs phase1_control_default_flux

- Type: `combined_flux_sensitivity`
- Status: `inconclusive_missing_evidence`
- Varied fields: `surface_heat_flux_k_m_s, surface_moisture_flux_g_g_m_s, cm1_cnst_shflx, cm1_cnst_lhflx`
- Equality failures: `[]`
- Unavailable evidence: `control:diagnostic_unavailable:low_level_response, experiment:diagnostic_unavailable:low_level_response`
- Interpretation: Runs are structurally comparable, but required output fields or diagnostics are unavailable.

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

- Implement standardized low-level qv/theta/temperature response diagnostics.
- Review campaign rows with unavailable required output fields before scientific conclusions.
