# Canonical Deep-Convection Run Report

## 1. Status, decision question, and non-product boundary

**Status:** one exact Gate B process completed and was evaluated. **Disposition:** `advance_to_storm_examination_validation`.

Decision question: does the stock CM1 r21.1 quarter-circle benchmark produce a trustworthy deep precipitating rotating supercell suitable for later examination? This is research evidence, not a World, Recipe, UX, or product approval.

## 2. Controlling Gate A artifact and accepted identity

- Case and scenario ID: `cm1_r21_1_quarter_circle_supercell_official_v0`
- Run ID: `quarter-circle-supercell-official-20260722T142521Z`
- Gate A artifact SHA-256: `a9a4b3829ed9d6c03238702613f20ce8ee0721fe7f999b158311df7253427965`
- Accepted identity: official CM1 r21.1 quarter-circle-hodograph supercell case

## 3. Implementation and report commits

The package and process used implementation commit `b465c35aa39a54bca46a869668da38caa45d2556`. The completed output was evaluated at `96e6fa221247c3c815dd5619df0a294f561e26cb`. This report is committed later and does not alter the executed package or retained output.

## 4. CM1 provenance and controlling hashes

- Release: `21.1`
- Official commit: `0f734f64efa89a684963a66d2ac32db67617912b`
- Source manifest: `fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e`
- Executable: `5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1`
- README.namelist: `7b95be56db51f5c9396c59dca252cf96b918a312cc70107451f91149a34ab3b5`
- Official supercell namelist: `3854f731efe6a6a9d56d6aa3db198434ccaba85bc5584b5e8ce1c5edfd3b56a4`
- Official supercell README: `3292aef3f7cdc49701015609626f55a3fd64162c88929d0992f9635dfb230200`
- `src/base.F`: `9c88a1021ddde22d02680786246c52bcffb040cbd72c3c4708f24fe24eec32ef`
- `src/init3d.F`: `9c45c0982ba194ea6ea74afd6a2516445cdd011fc90902091d089f4cb92dfd28`
- `src/param.F`: `cac64a6cb4363c6b88367b5cb9391f1bcf2130c63ffedef6e5973c03b190c349`
- `src/writeout_nc.F`: `5023244d7ce4f9a0dde7df9c780cf5c70b675097e8467c4fbfc8125e254f4710`
- `src/writeout.F`: `bef128e897d09dbc9ae86ec13bb156794e605a7c2da1596058de53c71d640dbd`

## 5. Complete official-versus-generated namelist diff

All 343 assignments were audited. Restoring the two approved transport values makes the generated file byte-identical to the official file.

| Assignment | Official | Generated | Classification |
|---|---:|---:|---|
| `nx` | `120` | `120` | unchanged |
| `ny` | `120` | `120` | unchanged |
| `nz` | `40` | `40` | unchanged |
| `ppnode` | `128` | `128` | unchanged |
| `timeformat` | `2` | `2` | unchanged |
| `timestats` | `1` | `1` | unchanged |
| `terrain_flag` | `.false.` | `.false.` | unchanged |
| `procfiles` | `.false.` | `.false.` | unchanged |
| `dx` | `1000.0` | `1000.0` | unchanged |
| `dy` | `1000.0` | `1000.0` | unchanged |
| `dz` | `500.0` | `500.0` | unchanged |
| `dtl` | `6.000` | `6.000` | unchanged |
| `timax` | `7200.0` | `7200.0` | unchanged |
| `run_time` | `-999.9` | `-999.9` | unchanged |
| `tapfrq` | `900.0` | `900.0` | unchanged |
| `rstfrq` | `-3600.0` | `-3600.0` | unchanged |
| `statfrq` | `60.0` | `60.0` | unchanged |
| `prclfrq` | `60.0` | `60.0` | unchanged |
| `cm1setup` | `1` | `1` | unchanged |
| `testcase` | `0` | `0` | unchanged |
| `adapt_dt` | `0` | `0` | unchanged |
| `irst` | `0` | `0` | unchanged |
| `rstnum` | `1` | `1` | unchanged |
| `iconly` | `0` | `0` | unchanged |
| `hadvordrs` | `5` | `5` | unchanged |
| `vadvordrs` | `5` | `5` | unchanged |
| `hadvordrv` | `5` | `5` | unchanged |
| `vadvordrv` | `5` | `5` | unchanged |
| `advwenos` | `2` | `2` | unchanged |
| `advwenov` | `0` | `0` | unchanged |
| `weno_order` | `5` | `5` | unchanged |
| `apmasscon` | `1` | `1` | unchanged |
| `idiff` | `0` | `0` | unchanged |
| `mdiff` | `0` | `0` | unchanged |
| `difforder` | `6` | `6` | unchanged |
| `imoist` | `1` | `1` | unchanged |
| `ipbl` | `0` | `0` | unchanged |
| `sgsmodel` | `1` | `1` | unchanged |
| `tconfig` | `1` | `1` | unchanged |
| `bcturbs` | `1` | `1` | unchanged |
| `horizturb` | `0` | `0` | unchanged |
| `doimpl` | `1` | `1` | unchanged |
| `irdamp` | `1` | `1` | unchanged |
| `hrdamp` | `0` | `0` | unchanged |
| `psolver` | `3` | `3` | unchanged |
| `ptype` | `5` | `5` | unchanged |
| `ihail` | `1` | `1` | unchanged |
| `iautoc` | `1` | `1` | unchanged |
| `cuparam` | `0` | `0` | unchanged |
| `icor` | `0` | `0` | unchanged |
| `lspgrad` | `0` | `0` | unchanged |
| `eqtset` | `2` | `2` | unchanged |
| `idiss` | `1` | `1` | unchanged |
| `efall` | `0` | `0` | unchanged |
| `rterm` | `0` | `0` | unchanged |
| `wbc` | `2` | `2` | unchanged |
| `ebc` | `2` | `2` | unchanged |
| `sbc` | `2` | `2` | unchanged |
| `nbc` | `2` | `2` | unchanged |
| `bbc` | `1` | `1` | unchanged |
| `tbc` | `1` | `1` | unchanged |
| `irbc` | `4` | `4` | unchanged |
| `roflux` | `0` | `0` | unchanged |
| `nudgeobc` | `0` | `0` | unchanged |
| `isnd` | `5` | `5` | unchanged |
| `iwnd` | `2` | `2` | unchanged |
| `itern` | `0` | `0` | unchanged |
| `iinit` | `1` | `1` | unchanged |
| `irandp` | `0` | `0` | unchanged |
| `ibalance` | `0` | `0` | unchanged |
| `iorigin` | `2` | `2` | unchanged |
| `axisymm` | `0` | `0` | unchanged |
| `imove` | `1` | `1` | unchanged |
| `iptra` | `0` | `0` | unchanged |
| `npt` | `1` | `1` | unchanged |
| `pdtra` | `1` | `1` | unchanged |
| `iprcl` | `0` | `0` | unchanged |
| `nparcels` | `1` | `1` | unchanged |
| `kdiff2` | `75.0` | `75.0` | unchanged |
| `kdiff6` | `0.040` | `0.040` | unchanged |
| `fcor` | `0.00005` | `0.00005` | unchanged |
| `kdiv` | `0.10` | `0.10` | unchanged |
| `alph` | `0.60` | `0.60` | unchanged |
| `rdalpha` | `3.3333333333e-3` | `3.3333333333e-3` | unchanged |
| `zd` | `15000.0` | `15000.0` | unchanged |
| `xhd` | `100000.0` | `100000.0` | unchanged |
| `alphobc` | `60.0` | `60.0` | unchanged |
| `umove` | `12.5` | `12.5` | unchanged |
| `vmove` | `3.0` | `3.0` | unchanged |
| `v_t` | `7.0` | `7.0` | unchanged |
| `l_h` | `100.0` | `100.0` | unchanged |
| `lhref1` | `100.0` | `100.0` | unchanged |
| `lhref2` | `1000.0` | `1000.0` | unchanged |
| `l_inf` | `75.0` | `75.0` | unchanged |
| `ndcnst` | `250.0` | `250.0` | unchanged |
| `nt_c` | `250.0` | `250.0` | unchanged |
| `csound` | `300.0` | `300.0` | unchanged |
| `cstar` | `30.0` | `30.0` | unchanged |
| `radopt` | `0` | `0` | unchanged |
| `dtrad` | `300.0` | `300.0` | unchanged |
| `ctrlat` | `36.68` | `36.68` | unchanged |
| `ctrlon` | `-98.35` | `-98.35` | unchanged |
| `year` | `2009` | `2009` | unchanged |
| `month` | `5` | `5` | unchanged |
| `day` | `15` | `15` | unchanged |
| `hour` | `21` | `21` | unchanged |
| `minute` | `38` | `38` | unchanged |
| `second` | `00` | `00` | unchanged |
| `isfcflx` | `0` | `0` | unchanged |
| `sfcmodel` | `0` | `0` | unchanged |
| `oceanmodel` | `0` | `0` | unchanged |
| `initsfc` | `1` | `1` | unchanged |
| `tsk0` | `299.28` | `299.28` | unchanged |
| `tmn0` | `297.28` | `297.28` | unchanged |
| `xland0` | `2.0` | `2.0` | unchanged |
| `lu0` | `16` | `16` | unchanged |
| `season` | `1` | `1` | unchanged |
| `cecd` | `3` | `3` | unchanged |
| `pertflx` | `0` | `0` | unchanged |
| `cnstce` | `0.001` | `0.001` | unchanged |
| `cnstcd` | `0.001` | `0.001` | unchanged |
| `isftcflx` | `0` | `0` | unchanged |
| `iz0tlnd` | `0` | `0` | unchanged |
| `oml_hml0` | `50.0` | `50.0` | unchanged |
| `oml_gamma` | `0.14` | `0.14` | unchanged |
| `set_flx` | `0` | `0` | unchanged |
| `cnst_shflx` | `0.24` | `0.24` | unchanged |
| `cnst_lhflx` | `5.2e-5` | `5.2e-5` | unchanged |
| `set_znt` | `0` | `0` | unchanged |
| `cnst_znt` | `0.16` | `0.16` | unchanged |
| `set_ust` | `0` | `0` | unchanged |
| `cnst_ust` | `0.25` | `0.25` | unchanged |
| `ramp_sgs` | `1` | `1` | unchanged |
| `ramp_time` | `1800.0` | `1800.0` | unchanged |
| `t2p_avg` | `1` | `1` | unchanged |
| `stretch_x` | `0` | `0` | unchanged |
| `dx_inner` | `1000.0` | `1000.0` | unchanged |
| `dx_outer` | `7000.0` | `7000.0` | unchanged |
| `nos_x_len` | `40000.0` | `40000.0` | unchanged |
| `tot_x_len` | `120000.0` | `120000.0` | unchanged |
| `stretch_y` | `0` | `0` | unchanged |
| `dy_inner` | `1000.0` | `1000.0` | unchanged |
| `dy_outer` | `7000.0` | `7000.0` | unchanged |
| `nos_y_len` | `40000.0` | `40000.0` | unchanged |
| `tot_y_len` | `120000.0` | `120000.0` | unchanged |
| `stretch_z` | `0` | `0` | unchanged |
| `ztop` | `18000.0` | `18000.0` | unchanged |
| `str_bot` | `0.0` | `0.0` | unchanged |
| `str_top` | `2000.0` | `2000.0` | unchanged |
| `dz_bot` | `125.0` | `125.0` | unchanged |
| `dz_top` | `500.0` | `500.0` | unchanged |
| `bc_temp` | `1` | `1` | unchanged |
| `ptc_top` | `250.0` | `250.0` | unchanged |
| `ptc_bot` | `300.0` | `300.0` | unchanged |
| `viscosity` | `25.0` | `25.0` | unchanged |
| `pr_num` | `0.72` | `0.72` | unchanged |
| `var1` | `0.0` | `0.0` | unchanged |
| `var2` | `0.0` | `0.0` | unchanged |
| `var3` | `0.0` | `0.0` | unchanged |
| `var4` | `0.0` | `0.0` | unchanged |
| `var5` | `0.0` | `0.0` | unchanged |
| `var6` | `0.0` | `0.0` | unchanged |
| `var7` | `0.0` | `0.0` | unchanged |
| `var8` | `0.0` | `0.0` | unchanged |
| `var9` | `0.0` | `0.0` | unchanged |
| `var10` | `0.0` | `0.0` | unchanged |
| `var11` | `0.0` | `0.0` | unchanged |
| `var12` | `0.0` | `0.0` | unchanged |
| `var13` | `0.0` | `0.0` | unchanged |
| `var14` | `0.0` | `0.0` | unchanged |
| `var15` | `0.0` | `0.0` | unchanged |
| `var16` | `0.0` | `0.0` | unchanged |
| `var17` | `0.0` | `0.0` | unchanged |
| `var18` | `0.0` | `0.0` | unchanged |
| `var19` | `0.0` | `0.0` | unchanged |
| `var20` | `0.0` | `0.0` | unchanged |
| `output_format` | `1` | `2` | approved_output_transport_change |
| `output_filetype` | `1` | `2` | approved_output_transport_change |
| `output_interp` | `0` | `0` | unchanged |
| `output_rain` | `1` | `1` | unchanged |
| `output_sws` | `1` | `1` | unchanged |
| `output_svs` | `1` | `1` | unchanged |
| `output_sps` | `1` | `1` | unchanged |
| `output_srs` | `1` | `1` | unchanged |
| `output_sgs` | `1` | `1` | unchanged |
| `output_sus` | `1` | `1` | unchanged |
| `output_shs` | `1` | `1` | unchanged |
| `output_coldpool` | `0` | `0` | unchanged |
| `output_sfcflx` | `0` | `0` | unchanged |
| `output_sfcparams` | `0` | `0` | unchanged |
| `output_sfcdiags` | `0` | `0` | unchanged |
| `output_psfc` | `0` | `0` | unchanged |
| `output_zs` | `0` | `0` | unchanged |
| `output_zh` | `0` | `0` | unchanged |
| `output_basestate` | `0` | `0` | unchanged |
| `output_th` | `1` | `1` | unchanged |
| `output_thpert` | `0` | `0` | unchanged |
| `output_prs` | `1` | `1` | unchanged |
| `output_prspert` | `0` | `0` | unchanged |
| `output_pi` | `0` | `0` | unchanged |
| `output_pipert` | `0` | `0` | unchanged |
| `output_rho` | `0` | `0` | unchanged |
| `output_rhopert` | `0` | `0` | unchanged |
| `output_tke` | `1` | `1` | unchanged |
| `output_km` | `1` | `1` | unchanged |
| `output_kh` | `1` | `1` | unchanged |
| `output_qv` | `1` | `1` | unchanged |
| `output_qvpert` | `0` | `0` | unchanged |
| `output_q` | `1` | `1` | unchanged |
| `output_dbz` | `1` | `1` | unchanged |
| `output_buoyancy` | `0` | `0` | unchanged |
| `output_u` | `1` | `1` | unchanged |
| `output_upert` | `0` | `0` | unchanged |
| `output_uinterp` | `1` | `1` | unchanged |
| `output_v` | `1` | `1` | unchanged |
| `output_vpert` | `0` | `0` | unchanged |
| `output_vinterp` | `1` | `1` | unchanged |
| `output_w` | `1` | `1` | unchanged |
| `output_winterp` | `1` | `1` | unchanged |
| `output_vort` | `1` | `1` | unchanged |
| `output_pv` | `0` | `0` | unchanged |
| `output_uh` | `1` | `1` | unchanged |
| `output_pblten` | `0` | `0` | unchanged |
| `output_dissten` | `0` | `0` | unchanged |
| `output_fallvel` | `0` | `0` | unchanged |
| `output_nm` | `0` | `0` | unchanged |
| `output_def` | `0` | `0` | unchanged |
| `output_radten` | `0` | `0` | unchanged |
| `output_cape` | `0` | `0` | unchanged |
| `output_cin` | `0` | `0` | unchanged |
| `output_lcl` | `0` | `0` | unchanged |
| `output_lfc` | `0` | `0` | unchanged |
| `output_pwat` | `0` | `0` | unchanged |
| `output_lwp` | `0` | `0` | unchanged |
| `output_thbudget` | `0` | `0` | unchanged |
| `output_qvbudget` | `0` | `0` | unchanged |
| `output_ubudget` | `0` | `0` | unchanged |
| `output_vbudget` | `0` | `0` | unchanged |
| `output_wbudget` | `0` | `0` | unchanged |
| `output_pdcomp` | `0` | `0` | unchanged |
| `restart_format` | `1` | `1` | unchanged |
| `restart_filetype` | `2` | `2` | unchanged |
| `restart_reset_frqtim` | `.true.` | `.true.` | unchanged |
| `restart_file_theta` | `.false.` | `.false.` | unchanged |
| `restart_file_dbz` | `.false.` | `.false.` | unchanged |
| `restart_file_th0` | `.false.` | `.false.` | unchanged |
| `restart_file_prs0` | `.false.` | `.false.` | unchanged |
| `restart_file_pi0` | `.false.` | `.false.` | unchanged |
| `restart_file_rho0` | `.false.` | `.false.` | unchanged |
| `restart_file_qv0` | `.false.` | `.false.` | unchanged |
| `restart_file_u0` | `.false.` | `.false.` | unchanged |
| `restart_file_v0` | `.false.` | `.false.` | unchanged |
| `restart_file_zs` | `.false.` | `.false.` | unchanged |
| `restart_file_zh` | `.false.` | `.false.` | unchanged |
| `restart_file_zf` | `.false.` | `.false.` | unchanged |
| `restart_file_diags` | `.false.` | `.false.` | unchanged |
| `restart_use_theta` | `.false.` | `.false.` | unchanged |
| `stat_w` | `1` | `1` | unchanged |
| `stat_wlevs` | `1` | `1` | unchanged |
| `stat_u` | `1` | `1` | unchanged |
| `stat_v` | `1` | `1` | unchanged |
| `stat_rmw` | `0` | `0` | unchanged |
| `stat_pipert` | `1` | `1` | unchanged |
| `stat_prspert` | `1` | `1` | unchanged |
| `stat_thpert` | `1` | `1` | unchanged |
| `stat_q` | `1` | `1` | unchanged |
| `stat_tke` | `1` | `1` | unchanged |
| `stat_km` | `1` | `1` | unchanged |
| `stat_kh` | `1` | `1` | unchanged |
| `stat_div` | `1` | `1` | unchanged |
| `stat_rh` | `1` | `1` | unchanged |
| `stat_rhi` | `1` | `1` | unchanged |
| `stat_the` | `1` | `1` | unchanged |
| `stat_cloud` | `1` | `1` | unchanged |
| `stat_sfcprs` | `1` | `1` | unchanged |
| `stat_wsp` | `1` | `1` | unchanged |
| `stat_cfl` | `1` | `1` | unchanged |
| `stat_vort` | `1` | `1` | unchanged |
| `stat_tmass` | `1` | `1` | unchanged |
| `stat_tmois` | `1` | `1` | unchanged |
| `stat_qmass` | `1` | `1` | unchanged |
| `stat_tenerg` | `1` | `1` | unchanged |
| `stat_mo` | `1` | `1` | unchanged |
| `stat_tmf` | `1` | `1` | unchanged |
| `stat_pcn` | `1` | `1` | unchanged |
| `stat_qsrc` | `1` | `1` | unchanged |
| `prcl_th` | `1` | `1` | unchanged |
| `prcl_t` | `1` | `1` | unchanged |
| `prcl_prs` | `1` | `1` | unchanged |
| `prcl_ptra` | `1` | `1` | unchanged |
| `prcl_q` | `1` | `1` | unchanged |
| `prcl_nc` | `1` | `1` | unchanged |
| `prcl_km` | `1` | `1` | unchanged |
| `prcl_kh` | `1` | `1` | unchanged |
| `prcl_tke` | `1` | `1` | unchanged |
| `prcl_dbz` | `1` | `1` | unchanged |
| `prcl_b` | `1` | `1` | unchanged |
| `prcl_vpg` | `1` | `1` | unchanged |
| `prcl_vort` | `1` | `1` | unchanged |
| `prcl_rho` | `1` | `1` | unchanged |
| `prcl_qsat` | `1` | `1` | unchanged |
| `prcl_sfc` | `1` | `1` | unchanged |
| `dodomaindiag` | `.false.` | `.false.` | unchanged |
| `diagfrq` | `60.0` | `60.0` | unchanged |
| `doazimavg` | `.false.` | `.false.` | unchanged |
| `azimavgfrq` | `3600.0` | `3600.0` | unchanged |
| `rlen` | `300000.0` | `300000.0` | unchanged |
| `do_adapt_move` | `.false.` | `.false.` | unchanged |
| `adapt_move_frq` | `3600.0` | `3600.0` | unchanged |
| `les_subdomain_shape` | `1` | `1` | unchanged |
| `les_subdomain_xlen` | `200000.0` | `200000.0` | unchanged |
| `les_subdomain_ylen` | `200000.0` | `200000.0` | unchanged |
| `les_subdomain_dlen` | `200000.0` | `200000.0` | unchanged |
| `les_subdomain_trnslen` | `5000.0` | `5000.0` | unchanged |
| `do_recycle_w` | `.false.` | `.false.` | unchanged |
| `do_recycle_s` | `.false.` | `.false.` | unchanged |
| `do_recycle_e` | `.false.` | `.false.` | unchanged |
| `do_recycle_n` | `.false.` | `.false.` | unchanged |
| `recycle_width_dx` | `6.0` | `6.0` | unchanged |
| `recycle_depth_m` | `1500.0` | `1500.0` | unchanged |
| `recycle_cap_loc_m` | `4000.0` | `4000.0` | unchanged |
| `recycle_inj_loc_m` | `0.0` | `0.0` | unchanged |
| `do_lsnudge` | `.false.` | `.false.` | unchanged |
| `do_lsnudge_u` | `.false.` | `.false.` | unchanged |
| `do_lsnudge_v` | `.false.` | `.false.` | unchanged |
| `do_lsnudge_th` | `.false.` | `.false.` | unchanged |
| `do_lsnudge_qv` | `.false.` | `.false.` | unchanged |
| `lsnudge_tau` | `1800.0` | `1800.0` | unchanged |
| `lsnudge_start` | `3600.0` | `3600.0` | unchanged |
| `lsnudge_end` | `7200.0` | `7200.0` | unchanged |
| `lsnudge_ramp_time` | `600.0` | `600.0` | unchanged |
| `do_ib` | `.false.` | `.false.` | unchanged |
| `ib_init` | `4` | `4` | unchanged |
| `top_cd` | `0.4` | `0.4` | unchanged |
| `side_cd` | `0.4` | `0.4` | unchanged |
| `hurr_vg` | `40.0` | `40.0` | unchanged |
| `hurr_rad` | `40000.0` | `40000.0` | unchanged |
| `hurr_vgpl` | `-0.70` | `-0.70` | unchanged |
| `hurr_rotate` | `0.0` | `0.0` | unchanged |
| `alphah` | `0` | `0` | unchanged |
| `alphahl` | `0.5` | `0.5` | unchanged |
| `cnor` | `8.e6` | `8.e6` | unchanged |
| `cnoh` | `4.e4` | `4.e4` | unchanged |

## 6. External scientific runtime-file inventory

Empty. No `input_sounding`, terrain file, land-use table, or other scientific runtime file was created or staged. Sounding, hodograph, and bubble came from the hash-pinned CM1 analytic source paths.

## 7. Package, storage, and free-space preflight

The field-derived uncompressed history floor was 572,140,800 bytes for nine histories. No compression was credited. The retained planning band was 650,000,000-900,000,000 bytes; 25,430,798,336 bytes were free against a 2,147,483,648-byte requirement.

## 8. Run identity, command, process, and lifecycle

- Command: `configured_cm1_run_directory/cm1.exe`
- Execution mode: single_local_non_mpi_process
- Process ID: 92376
- Start: 2026-07-22 14:26:04.871635+00:00
- Finish: 2026-07-22 14:35:17.523418+00:00
- Wall time: 552.652 s
- Exit code: 0
- Normal termination marker: True

## 9. File and time inventory

| File | Time (s) | Bytes |
|---|---:|---:|
| `cm1out_000001.nc` | 0 | 544,019 |
| `cm1out_000002.nc` | 900 | 14,496,437 |
| `cm1out_000003.nc` | 1800 | 16,672,636 |
| `cm1out_000004.nc` | 2700 | 19,307,201 |
| `cm1out_000005.nc` | 3600 | 21,456,397 |
| `cm1out_000006.nc` | 4500 | 24,082,000 |
| `cm1out_000007.nc` | 5400 | 26,801,263 |
| `cm1out_000008.nc` | 6300 | 29,309,646 |
| `cm1out_000009.nc` | 7200 | 31,509,304 |
| `cm1out_stats.nc` | 0-7200 at 60-s cadence | 1,052,565 |

## 10. Native variable inventory and integrity

Every required field was read from every numbered history. Rows below retain native dimensions, units, precision, staggering, fill counts, finite counts, and global ranges.

| Time | Field | Dimensions | Units | Dtype | Staggering | Fill | Non-finite | Min | Max |
|---:|---|---|---|---|---|---:|---:|---:|---:|
| 0 | `th` | `1 x 40 x 120 x 120` | K | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 300.34 | 489.138 |
| 0 | `prs` | `1 x 40 x 120 x 120` | Pa | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 6004.57 | 97212.7 |
| 0 | `qv` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 2.56644e-05 | 0.014 |
| 0 | `qc` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 0 | `qr` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 0 | `qi` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 0 | `qs` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 0 | `qg` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 0 | `nci` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 0 | `ncs` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 0 | `ncr` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 0 | `ncg` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 0 | `dbz` | `1 x 40 x 120 x 120` | dBZ | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 0 | `uinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -12.3655 | 18.5 |
| 0 | `vinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -1.63437 | 4 |
| 0 | `winterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 0 | `xvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.00504672 | 0 |
| 0 | `yvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.006 |
| 0 | `zvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 0 | `tke` | `1 x 41 x 120 x 120` | m^2/s^2 | float32 | native_z_staggered | 0 | 0 | 0 | 0 |
| 0 | `kmh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 7.93701e-09 |
| 0 | `kmv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 7.93701e-09 |
| 0 | `khh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 7.95288e-09 |
| 0 | `khv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 7.95288e-09 |
| 0 | `w` | `1 x 41 x 120 x 120` | m/s | float32 | native_z_staggered | 0 | 0 | 0 | 0 |
| 0 | `u` | `1 x 40 x 120 x 121` | m/s | float32 | native_x_staggered | 0 | 0 | -12.3655 | 18.5 |
| 0 | `v` | `1 x 40 x 121 x 120` | m/s | float32 | native_y_staggered | 0 | 0 | -1.63437 | 4 |
| 0 | `uh` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 0 |
| 0 | `rain` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 0 |
| 0 | `sws` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 0 | 0 |
| 0 | `svs` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | -1000 | -1000 |
| 0 | `sps` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | 200000 | 200000 |
| 0 | `srs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0 |
| 0 | `sgs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0 |
| 0 | `sus` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | -1000 | -1000 |
| 0 | `shs` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 0 |
| 0 | `rain2` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 0 |
| 0 | `sws2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 0 | 0 |
| 0 | `svs2` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | -1000 | -1000 |
| 0 | `sps2` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | 200000 | 200000 |
| 0 | `srs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0 |
| 0 | `sgs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0 |
| 0 | `sus2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | -1000 | -1000 |
| 0 | `shs2` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 0 |
| 900 | `th` | `1 x 40 x 120 x 120` | K | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 300.134 | 489.146 |
| 900 | `prs` | `1 x 40 x 120 x 120` | Pa | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 6004.25 | 97220.4 |
| 900 | `qv` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 2.56638e-05 | 0.0140001 |
| 900 | `qc` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.0016496 |
| 900 | `qr` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 8.65197e-07 |
| 900 | `qi` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 900 | `qs` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 900 | `qg` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 900 | `nci` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 900 | `ncs` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 900 | `ncr` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 10911.8 |
| 900 | `ncg` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0 |
| 900 | `dbz` | `1 x 40 x 120 x 120` | dBZ | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -36.9896 | -22.811 |
| 900 | `uinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -13.739 | 18.8833 |
| 900 | `vinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -2.87508 | 6.6334 |
| 900 | `winterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -1.30339 | 3.91009 |
| 900 | `xvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.00613532 | 0.00493332 |
| 900 | `yvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.000251088 | 0.0108974 |
| 900 | `zvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.00148831 | 0.00141066 |
| 900 | `tke` | `1 x 41 x 120 x 120` | m^2/s^2 | float32 | native_z_staggered | 0 | 0 | 0 | 5.0774 |
| 900 | `kmh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 89.4227 |
| 900 | `kmv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 89.4227 |
| 900 | `khh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 268.268 |
| 900 | `khv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 268.268 |
| 900 | `w` | `1 x 41 x 120 x 120` | m/s | float32 | native_z_staggered | 0 | 0 | -1.34963 | 4.1021 |
| 900 | `u` | `1 x 40 x 120 x 121` | m/s | float32 | native_x_staggered | 0 | 0 | -13.7467 | 18.8922 |
| 900 | `v` | `1 x 40 x 121 x 120` | m/s | float32 | native_y_staggered | 0 | 0 | -2.88356 | 6.83611 |
| 900 | `uh` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 4.6804 |
| 900 | `rain` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 5.22824e-13 |
| 900 | `sws` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 1.36237 | 2.33749 |
| 900 | `svs` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | -4.41074e-08 | 0.000156095 |
| 900 | `sps` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | -38.8203 | -0.101562 |
| 900 | `srs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0 |
| 900 | `sgs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0 |
| 900 | `sus` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 1.6655e-21 | 0.310214 |
| 900 | `shs` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 4.6804 |
| 900 | `rain2` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 6.09484e-13 |
| 900 | `sws2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 1.36279 | 2.32751 |
| 900 | `svs2` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | -4.08844e-07 | 0.000155859 |
| 900 | `sps2` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | -39.1543 | -0.119865 |
| 900 | `srs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0 |
| 900 | `sgs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0 |
| 900 | `sus2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | -7.4684e-07 | 0.311885 |
| 900 | `shs2` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 4.50508 |
| 1800 | `th` | `1 x 40 x 120 x 120` | K | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 300.015 | 489.174 |
| 1800 | `prs` | `1 x 40 x 120 x 120` | Pa | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 6005.58 | 97220.9 |
| 1800 | `qv` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 2.56651e-05 | 0.0140046 |
| 1800 | `qc` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00319843 |
| 1800 | `qr` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00779185 |
| 1800 | `qi` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00126636 |
| 1800 | `qs` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00130439 |
| 1800 | `qg` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00820899 |
| 1800 | `nci` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 892367 |
| 1800 | `ncs` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 64865.1 |
| 1800 | `ncr` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 42030.8 |
| 1800 | `ncg` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 27389 |
| 1800 | `dbz` | `1 x 40 x 120 x 120` | dBZ | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -38.9733 | 65.4041 |
| 1800 | `uinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -15.39 | 28.9106 |
| 1800 | `vinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -11.5036 | 17.9916 |
| 1800 | `winterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -6.94396 | 27.8283 |
| 1800 | `xvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0218746 | 0.0272985 |
| 1800 | `yvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0222817 | 0.035728 |
| 1800 | `zvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0159787 | 0.020612 |
| 1800 | `tke` | `1 x 41 x 120 x 120` | m^2/s^2 | float32 | native_z_staggered | 0 | 0 | 0 | 70.1678 |
| 1800 | `kmh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 664.853 |
| 1800 | `kmv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 664.853 |
| 1800 | `khh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 1994.56 |
| 1800 | `khv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 1994.56 |
| 1800 | `w` | `1 x 41 x 120 x 120` | m/s | float32 | native_z_staggered | 0 | 0 | -7.27259 | 29.3726 |
| 1800 | `u` | `1 x 40 x 120 x 121` | m/s | float32 | native_x_staggered | 0 | 0 | -15.445 | 29.6297 |
| 1800 | `v` | `1 x 40 x 121 x 120` | m/s | float32 | native_y_staggered | 0 | 0 | -12.3065 | 19.3404 |
| 1800 | `uh` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 901.322 |
| 1800 | `rain` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 0.001892 |
| 1800 | `sws` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 1.37165 | 5.44776 |
| 1800 | `svs` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | -1.3113e-09 | 0.000496851 |
| 1800 | `sps` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | -110.148 | -0.101562 |
| 1800 | `srs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 2.83286e-05 |
| 1800 | `sgs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 1.69295e-05 |
| 1800 | `sus` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 0.00022928 | 25.1045 |
| 1800 | `shs` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 901.874 |
| 1800 | `rain2` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 0.00193721 |
| 1800 | `sws2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 1.37224 | 5.43289 |
| 1800 | `svs2` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | -8.92722e-07 | 0.000463951 |
| 1800 | `sps2` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | -109.005 | -0.124623 |
| 1800 | `srs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 2.83258e-05 |
| 1800 | `sgs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 1.69804e-05 |
| 1800 | `sus2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | -3.90168e-06 | 25.0448 |
| 1800 | `shs2` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 887.501 |
| 2700 | `th` | `1 x 40 x 120 x 120` | K | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 297.652 | 489.684 |
| 2700 | `prs` | `1 x 40 x 120 x 120` | Pa | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 6000.71 | 97272.7 |
| 2700 | `qv` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 4.9414e-06 | 0.0150076 |
| 2700 | `qc` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00478753 |
| 2700 | `qr` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00776022 |
| 2700 | `qi` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00210316 |
| 2700 | `qs` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00127286 |
| 2700 | `qg` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.0110301 |
| 2700 | `nci` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 1.22688e+06 |
| 2700 | `ncs` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 118051 |
| 2700 | `ncr` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 109717 |
| 2700 | `ncg` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 38641.4 |
| 2700 | `dbz` | `1 x 40 x 120 x 120` | dBZ | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -38.5889 | 67.2454 |
| 2700 | `uinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -17.1114 | 52.3791 |
| 2700 | `vinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -21.6701 | 24.8823 |
| 2700 | `winterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -24.2832 | 48.9974 |
| 2700 | `xvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0330558 | 0.0306445 |
| 2700 | `yvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0516419 | 0.04076 |
| 2700 | `zvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0224754 | 0.0208234 |
| 2700 | `tke` | `1 x 41 x 120 x 120` | m^2/s^2 | float32 | native_z_staggered | 0 | 0 | 0 | 91.6216 |
| 2700 | `kmh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 721.848 |
| 2700 | `kmv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 721.848 |
| 2700 | `khh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 2165.54 |
| 2700 | `khv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 2165.54 |
| 2700 | `w` | `1 x 41 x 120 x 120` | m/s | float32 | native_z_staggered | 0 | 0 | -24.2874 | 49.0179 |
| 2700 | `u` | `1 x 40 x 120 x 121` | m/s | float32 | native_x_staggered | 0 | 0 | -17.1305 | 52.7219 |
| 2700 | `v` | `1 x 40 x 121 x 120` | m/s | float32 | native_y_staggered | 0 | 0 | -26.6294 | 26.8224 |
| 2700 | `uh` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 663 |
| 2700 | `rain` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 1.50274 |
| 2700 | `sws` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 1.37224 | 7.52762 |
| 2700 | `svs` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | 0 | 0.00122494 |
| 2700 | `sps` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | -113.68 | -0.101562 |
| 2700 | `srs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.00536376 |
| 2700 | `sgs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.000287927 |
| 2700 | `sus` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 0.00022928 | 31.1511 |
| 2700 | `shs` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 901.874 |
| 2700 | `rain2` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 0.945512 |
| 2700 | `sws2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 1.37229 | 7.50696 |
| 2700 | `svs2` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | -1.0088e-05 | 0.00123493 |
| 2700 | `sps2` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | -113.835 | -0.146591 |
| 2700 | `srs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.0053678 |
| 2700 | `sgs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.000287139 |
| 2700 | `sus2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | -1.09631e-05 | 31.7256 |
| 2700 | `shs2` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 784.262 |
| 3600 | `th` | `1 x 40 x 120 x 120` | K | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 295.406 | 490.797 |
| 3600 | `prs` | `1 x 40 x 120 x 120` | Pa | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 5992.83 | 97264.1 |
| 3600 | `qv` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 1.48316e-06 | 0.0150171 |
| 3600 | `qc` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.0069199 |
| 3600 | `qr` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00797172 |
| 3600 | `qi` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00162849 |
| 3600 | `qs` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00129113 |
| 3600 | `qg` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.0130698 |
| 3600 | `nci` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 1.63687e+06 |
| 3600 | `ncs` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 103916 |
| 3600 | `ncr` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 282090 |
| 3600 | `ncg` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 45374.4 |
| 3600 | `dbz` | `1 x 40 x 120 x 120` | dBZ | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -39.2205 | 68.3169 |
| 3600 | `uinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -22.245 | 45.1211 |
| 3600 | `vinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -38.3057 | 42.4114 |
| 3600 | `winterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -27.12 | 55.0896 |
| 3600 | `xvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.048145 | 0.0402606 |
| 3600 | `yvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0587958 | 0.0509728 |
| 3600 | `zvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0275094 | 0.0250577 |
| 3600 | `tke` | `1 x 41 x 120 x 120` | m^2/s^2 | float32 | native_z_staggered | 0 | 0 | 0 | 70.6429 |
| 3600 | `kmh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 667.1 |
| 3600 | `kmv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 667.1 |
| 3600 | `khh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 2001.3 |
| 3600 | `khv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 2001.3 |
| 3600 | `w` | `1 x 41 x 120 x 120` | m/s | float32 | native_z_staggered | 0 | 0 | -27.5297 | 55.2545 |
| 3600 | `u` | `1 x 40 x 120 x 121` | m/s | float32 | native_x_staggered | 0 | 0 | -27.7521 | 45.3582 |
| 3600 | `v` | `1 x 40 x 121 x 120` | m/s | float32 | native_y_staggered | 0 | 0 | -41.0631 | 43.2863 |
| 3600 | `uh` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 647.618 |
| 3600 | `rain` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 3.78559 |
| 3600 | `sws` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 1.37229 | 14.3925 |
| 3600 | `svs` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | 0 | 0.00324143 |
| 3600 | `sps` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | -154.453 | -0.101562 |
| 3600 | `srs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.00538315 |
| 3600 | `sgs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.000288241 |
| 3600 | `sus` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 0.00022928 | 32.7313 |
| 3600 | `shs` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 901.874 |
| 3600 | `rain2` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 1.44547 |
| 3600 | `sws2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 1.37237 | 14.2917 |
| 3600 | `svs2` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | -1.12982e-05 | 0.00322226 |
| 3600 | `sps2` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | -154.381 | -0.146415 |
| 3600 | `srs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.00517899 |
| 3600 | `sgs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.000218005 |
| 3600 | `sus2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | -7.54912e-07 | 32.7121 |
| 3600 | `shs2` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 715.169 |
| 4500 | `th` | `1 x 40 x 120 x 120` | K | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 293.996 | 490.507 |
| 4500 | `prs` | `1 x 40 x 120 x 120` | Pa | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 5993.4 | 97325.8 |
| 4500 | `qv` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 3.65585e-06 | 0.0158717 |
| 4500 | `qc` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00786212 |
| 4500 | `qr` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.0085243 |
| 4500 | `qi` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00201651 |
| 4500 | `qs` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00152619 |
| 4500 | `qg` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.0136529 |
| 4500 | `nci` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 1.60913e+06 |
| 4500 | `ncs` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 109478 |
| 4500 | `ncr` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 378788 |
| 4500 | `ncg` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 72774 |
| 4500 | `dbz` | `1 x 40 x 120 x 120` | dBZ | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -39.5188 | 69.5315 |
| 4500 | `uinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -26.351 | 50.3167 |
| 4500 | `vinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -44.9697 | 38.6787 |
| 4500 | `winterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -28.8427 | 60.0868 |
| 4500 | `xvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0540987 | 0.0419035 |
| 4500 | `yvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0585783 | 0.0628652 |
| 4500 | `zvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0241976 | 0.0266864 |
| 4500 | `tke` | `1 x 41 x 120 x 120` | m^2/s^2 | float32 | native_z_staggered | 0 | 0 | 0 | 107.117 |
| 4500 | `kmh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 741.41 |
| 4500 | `kmv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 741.41 |
| 4500 | `khh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 2103.04 |
| 4500 | `khv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 2103.04 |
| 4500 | `w` | `1 x 41 x 120 x 120` | m/s | float32 | native_z_staggered | 0 | 0 | -29.7879 | 60.1981 |
| 4500 | `u` | `1 x 40 x 120 x 121` | m/s | float32 | native_x_staggered | 0 | 0 | -30.3563 | 53.2699 |
| 4500 | `v` | `1 x 40 x 121 x 120` | m/s | float32 | native_y_staggered | 0 | 0 | -45.9693 | 39.9721 |
| 4500 | `uh` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 701.606 |
| 4500 | `rain` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 6.54609 |
| 4500 | `sws` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 1.3723 | 16.945 |
| 4500 | `svs` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | 0 | 0.00805381 |
| 4500 | `sps` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | -159.273 | -0.101562 |
| 4500 | `srs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.00538315 |
| 4500 | `sgs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.000523958 |
| 4500 | `sus` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 0.00022928 | 36.5139 |
| 4500 | `shs` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 5.17893e-14 | 901.874 |
| 4500 | `rain2` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 1.74017 |
| 4500 | `sws2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 1.37239 | 16.8815 |
| 4500 | `svs2` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | -2.1171e-05 | 0.00784592 |
| 4500 | `sps2` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | -158.89 | -0.147865 |
| 4500 | `srs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.00522091 |
| 4500 | `sgs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.000524747 |
| 4500 | `sus2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 9.88879e-06 | 35.9874 |
| 4500 | `shs2` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 722.445 |
| 5400 | `th` | `1 x 40 x 120 x 120` | K | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 294.072 | 490.57 |
| 5400 | `prs` | `1 x 40 x 120 x 120` | Pa | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 5993.94 | 97428.5 |
| 5400 | `qv` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 2.92872e-06 | 0.0159855 |
| 5400 | `qc` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00744907 |
| 5400 | `qr` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00788695 |
| 5400 | `qi` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00278883 |
| 5400 | `qs` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00128617 |
| 5400 | `qg` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.0127385 |
| 5400 | `nci` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 1.67092e+06 |
| 5400 | `ncs` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 102191 |
| 5400 | `ncr` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 344357 |
| 5400 | `ncg` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 80573.8 |
| 5400 | `dbz` | `1 x 40 x 120 x 120` | dBZ | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -39.9493 | 67.6092 |
| 5400 | `uinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -40.1327 | 50.4822 |
| 5400 | `vinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -47.4491 | 42.7908 |
| 5400 | `winterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -32.5997 | 58.7166 |
| 5400 | `xvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0610365 | 0.04169 |
| 5400 | `yvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0585443 | 0.0651523 |
| 5400 | `zvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0305439 | 0.0308061 |
| 5400 | `tke` | `1 x 41 x 120 x 120` | m^2/s^2 | float32 | native_z_staggered | 0 | 0 | 0 | 102.992 |
| 5400 | `kmh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 805.488 |
| 5400 | `kmv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 805.488 |
| 5400 | `khh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 2416.46 |
| 5400 | `khv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 2416.46 |
| 5400 | `w` | `1 x 41 x 120 x 120` | m/s | float32 | native_z_staggered | 0 | 0 | -34.692 | 58.8914 |
| 5400 | `u` | `1 x 40 x 120 x 121` | m/s | float32 | native_x_staggered | 0 | 0 | -41.8135 | 51.0081 |
| 5400 | `v` | `1 x 40 x 121 x 120` | m/s | float32 | native_y_staggered | 0 | 0 | -48.8727 | 43.8349 |
| 5400 | `uh` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 627.651 |
| 5400 | `rain` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 7.64438 |
| 5400 | `sws` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 1.3724 | 18.6255 |
| 5400 | `svs` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | 0 | 0.0100438 |
| 5400 | `sps` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | -159.273 | -0.101562 |
| 5400 | `srs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.00538315 |
| 5400 | `sgs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.000711148 |
| 5400 | `sus` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 0.000233153 | 37.9741 |
| 5400 | `shs` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 1.64977e-10 | 901.874 |
| 5400 | `rain2` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 1.83353 |
| 5400 | `sws2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 1.37239 | 18.7001 |
| 5400 | `svs2` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | -0.000207324 | 0.00865044 |
| 5400 | `sps2` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | -158.544 | -0.206283 |
| 5400 | `srs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.00528516 |
| 5400 | `sgs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.000677686 |
| 5400 | `sus2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 0.000310588 | 37.4796 |
| 5400 | `shs2` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 821.734 |
| 6300 | `th` | `1 x 40 x 120 x 120` | K | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 292.645 | 490.681 |
| 6300 | `prs` | `1 x 40 x 120 x 120` | Pa | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 5994.09 | 97350.4 |
| 6300 | `qv` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 4.45475e-06 | 0.0160224 |
| 6300 | `qc` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00787277 |
| 6300 | `qr` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00876461 |
| 6300 | `qi` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00283404 |
| 6300 | `qs` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00188471 |
| 6300 | `qg` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.013402 |
| 6300 | `nci` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 1.78149e+06 |
| 6300 | `ncs` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 130675 |
| 6300 | `ncr` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 387169 |
| 6300 | `ncg` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 60821.5 |
| 6300 | `dbz` | `1 x 40 x 120 x 120` | dBZ | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -42.8066 | 67.4353 |
| 6300 | `uinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -38.0867 | 55.206 |
| 6300 | `vinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -44.5917 | 49.6972 |
| 6300 | `winterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -33.3583 | 59.1737 |
| 6300 | `xvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0645529 | 0.0501186 |
| 6300 | `yvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0734965 | 0.0692033 |
| 6300 | `zvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.030556 | 0.0307449 |
| 6300 | `tke` | `1 x 41 x 120 x 120` | m^2/s^2 | float32 | native_z_staggered | 0 | 0 | 0 | 89.9791 |
| 6300 | `kmh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 752.883 |
| 6300 | `kmv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 752.883 |
| 6300 | `khh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 2258.65 |
| 6300 | `khv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 2258.65 |
| 6300 | `w` | `1 x 41 x 120 x 120` | m/s | float32 | native_z_staggered | 0 | 0 | -35.5982 | 59.481 |
| 6300 | `u` | `1 x 40 x 120 x 121` | m/s | float32 | native_x_staggered | 0 | 0 | -38.7672 | 57.6428 |
| 6300 | `v` | `1 x 40 x 121 x 120` | m/s | float32 | native_y_staggered | 0 | 0 | -50.9475 | 50.0588 |
| 6300 | `uh` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 752.324 |
| 6300 | `rain` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 7.84485 |
| 6300 | `sws` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 1.3724 | 21.9051 |
| 6300 | `svs` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | 0 | 0.0114461 |
| 6300 | `sps` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | -243.258 | -0.148438 |
| 6300 | `srs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.00538315 |
| 6300 | `sgs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.000763931 |
| 6300 | `sus` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 0.000233153 | 38.3384 |
| 6300 | `shs` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 2.21904e-10 | 901.874 |
| 6300 | `rain2` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 2.15135 |
| 6300 | `sws2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 1.3737 | 21.9167 |
| 6300 | `svs2` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | -8.41601e-06 | 0.00973382 |
| 6300 | `sps2` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | -243.042 | -0.20542 |
| 6300 | `srs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.00537148 |
| 6300 | `sgs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.000759669 |
| 6300 | `sus2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | -0.0149898 | 38.2083 |
| 6300 | `shs2` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 795.984 |
| 7200 | `th` | `1 x 40 x 120 x 120` | K | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 292.116 | 490.474 |
| 7200 | `prs` | `1 x 40 x 120 x 120` | Pa | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 5982.03 | 97358.5 |
| 7200 | `qv` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 4.02018e-06 | 0.0159767 |
| 7200 | `qc` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00811363 |
| 7200 | `qr` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00973085 |
| 7200 | `qi` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00266138 |
| 7200 | `qs` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.00205958 |
| 7200 | `qg` | `1 x 40 x 120 x 120` | kg/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 0.0142001 |
| 7200 | `nci` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 1.78594e+06 |
| 7200 | `ncs` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 126885 |
| 7200 | `ncr` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 405575 |
| 7200 | `ncg` | `1 x 40 x 120 x 120` | #/kg | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | 0 | 86276.9 |
| 7200 | `dbz` | `1 x 40 x 120 x 120` | dBZ | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -39.9976 | 67.7478 |
| 7200 | `uinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -29.2731 | 59.9547 |
| 7200 | `vinterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -49.574 | 42.9598 |
| 7200 | `winterp` | `1 x 40 x 120 x 120` | m/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -36.3916 | 55.7397 |
| 7200 | `xvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0492678 | 0.0486143 |
| 7200 | `yvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0501326 | 0.0537852 |
| 7200 | `zvort` | `1 x 40 x 120 x 120` | 1/s | float32 | scalar_interpolated_or_scalar_native | 0 | 0 | -0.0261078 | 0.0229284 |
| 7200 | `tke` | `1 x 41 x 120 x 120` | m^2/s^2 | float32 | native_z_staggered | 0 | 0 | 0 | 101.11 |
| 7200 | `kmh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 782.738 |
| 7200 | `kmv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 782.738 |
| 7200 | `khh` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 2348.22 |
| 7200 | `khv` | `1 x 41 x 120 x 120` | m^2/s | float32 | native_z_staggered | 0 | 0 | 0 | 2348.22 |
| 7200 | `w` | `1 x 41 x 120 x 120` | m/s | float32 | native_z_staggered | 0 | 0 | -38.8165 | 55.7548 |
| 7200 | `u` | `1 x 40 x 120 x 121` | m/s | float32 | native_x_staggered | 0 | 0 | -30.148 | 60.9074 |
| 7200 | `v` | `1 x 40 x 121 x 120` | m/s | float32 | native_y_staggered | 0 | 0 | -52.7423 | 44.3816 |
| 7200 | `uh` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 661.214 |
| 7200 | `rain` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 8.0913 |
| 7200 | `sws` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 1.3724 | 22.4126 |
| 7200 | `svs` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | 0 | 0.0131319 |
| 7200 | `sps` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | -269.094 | -0.148438 |
| 7200 | `srs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.00538315 |
| 7200 | `sgs` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.000763931 |
| 7200 | `sus` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 0.050811 | 38.3384 |
| 7200 | `shs` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 4.60845e-10 | 901.874 |
| 7200 | `rain2` | `1 x 120 x 120` | cm | float32 | scalar_surface | 0 | 0 | 0 | 2.57441 |
| 7200 | `sws2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 1.37617 | 22.2362 |
| 7200 | `svs2` | `1 x 120 x 120` | 1/s | float32 | scalar_surface | 0 | 0 | -2.65625e-05 | 0.0124376 |
| 7200 | `sps2` | `1 x 120 x 120` | Pa | float32 | scalar_surface | 0 | 0 | -268.91 | -0.204781 |
| 7200 | `srs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.00530488 |
| 7200 | `sgs2` | `1 x 120 x 120` | kg/kg | float32 | scalar_surface | 0 | 0 | 0 | 0.0006658 |
| 7200 | `sus2` | `1 x 120 x 120` | m/s | float32 | scalar_surface | 0 | 0 | 0.0719268 | 37.9767 |
| 7200 | `shs2` | `1 x 120 x 120` | m2/s2 | float32 | scalar_surface | 0 | 0 | 0 | 780.859 |

### Statistics stream inventory

| Variable | Dimensions | Units | Dtype | Fill | Non-finite | Min | Max |
|---|---|---|---|---:|---:|---:|---:|
| `mtime` | `121` | s | float32 | 0 | 0 | 0 | 7200 |
| `wmax` | `121` | m/s | float32 | 0 | 0 | 0 | 60.4823 |
| `wmin` | `121` | m/s | float32 | 0 | 0 | -45.3874 | 0 |
| `zwmax` | `121` | m AGL | float32 | 0 | 0 | 0 | 12000 |
| `zwmin` | `121` | m AGL | float32 | 0 | 0 | 0 | 13500 |
| `wmax500` | `121` | m/s | float32 | 0 | 0 | 0 | 7.39299 |
| `wmin500` | `121` | m/s | float32 | 0 | 0 | -8.08801 | 0 |
| `wmax1000` | `121` | m/s | float32 | 0 | 0 | 0 | 12.0159 |
| `wmin1000` | `121` | m/s | float32 | 0 | 0 | -12.1646 | 0 |
| `wmax2500` | `121` | m/s | float32 | 0 | 0 | 0 | 21.3487 |
| `wmin2500` | `121` | m/s | float32 | 0 | 0 | -13.0634 | 0 |
| `wmax5000` | `121` | m/s | float32 | 0 | 0 | 0 | 38.3137 |
| `wmin5000` | `121` | m/s | float32 | 0 | 0 | -15.9521 | 0 |
| `wmax10k` | `121` | m/s | float32 | 0 | 0 | 0 | 60.1981 |
| `wmin10k` | `121` | m/s | float32 | 0 | 0 | -30.4307 | 0 |
| `umax` | `121` | m/s | float32 | 0 | 0 | 18.5 | 62.2967 |
| `umin` | `121` | m/s | float32 | 0 | 0 | -45.5636 | -12.3655 |
| `sumax` | `121` | m/s | float32 | 0 | 0 | -12.3655 | 7.90847 |
| `sumin` | `121` | m/s | float32 | 0 | 0 | -27.2231 | -12.3655 |
| `vmax` | `121` | m/s | float32 | 0 | 0 | 4 | 52.8504 |
| `vmin` | `121` | m/s | float32 | 0 | 0 | -63.4385 | -1.63437 |
| `svmax` | `121` | m/s | float32 | 0 | 0 | -1.63437 | 17.0751 |
| `svmin` | `121` | m/s | float32 | 0 | 0 | -25.0397 | -1.63437 |
| `ppimax` | `121` | nondimensional | float32 | 0 | 0 | 0 | 0.00342911 |
| `ppimin` | `121` | nondimensional | float32 | 0 | 0 | -0.00324792 | 0 |
| `ppmax` | `121` | Pa | float32 | 0 | 0 | 0.0033226 | 342.052 |
| `ppmin` | `121` | Pa | float32 | 0 | 0 | -562.599 | -0.00175095 |
| `thpmax` | `121` | K | float32 | 0 | 0 | 0.526843 | 40.4263 |
| `thpmin` | `121` | K | float32 | 0 | 0 | -48.7283 | 0 |
| `sthpmax` | `121` | K | float32 | 0 | 0 | 0.0127071 | 1.30594 |
| `sthpmin` | `121` | K | float32 | 0 | 0 | -8.22412 | 0 |
| `maxqv` | `121` | kg/kg | float32 | 0 | 0 | 0.014 | 0.0165046 |
| `minqv` | `121` | kg/kg | float32 | 0 | 0 | 1.47156e-06 | 2.56654e-05 |
| `maxqc` | `121` | kg/kg | float32 | 0 | 0 | 0 | 0.00827046 |
| `minqc` | `121` | kg/kg | float32 | 0 | 0 | 0 | 0 |
| `maxqr` | `121` | kg/kg | float32 | 0 | 0 | 0 | 0.0102806 |
| `minqr` | `121` | kg/kg | float32 | 0 | 0 | 0 | 0 |
| `maxqi` | `121` | kg/kg | float32 | 0 | 0 | 0 | 0.0033299 |
| `minqi` | `121` | kg/kg | float32 | 0 | 0 | 0 | 0 |
| `maxqs` | `121` | kg/kg | float32 | 0 | 0 | 0 | 0.00252312 |
| `minqs` | `121` | kg/kg | float32 | 0 | 0 | 0 | 0 |
| `maxqg` | `121` | kg/kg | float32 | 0 | 0 | 0 | 0.0142001 |
| `minqg` | `121` | kg/kg | float32 | 0 | 0 | 0 | 0 |
| `maxnci` | `121` | #/kg | float32 | 0 | 0 | 0 | 2.20442e+06 |
| `minnci` | `121` | #/kg | float32 | 0 | 0 | 0 | 0 |
| `maxncs` | `121` | #/kg | float32 | 0 | 0 | 0 | 147074 |
| `minncs` | `121` | #/kg | float32 | 0 | 0 | 0 | 0 |
| `maxncr` | `121` | #/kg | float32 | 0 | 0 | 0 | 426978 |
| `minncr` | `121` | #/kg | float32 | 0 | 0 | 0 | 0 |
| `maxncg` | `121` | #/kg | float32 | 0 | 0 | 0 | 86276.9 |
| `minncg` | `121` | #/kg | float32 | 0 | 0 | 0 | 0 |
| `pratemax` | `121` | kg/m2/s | float32 | 0 | 0 | 0 | 0.0440886 |
| `pratemin` | `121` | kg/m2/s | float32 | 0 | 0 | -3.3424e-17 | 0 |
| `tkemax` | `121` | m^2/s^2 | float32 | 0 | 0 | 0 | 161.831 |
| `tkemin` | `121` | m^2/s^2 | float32 | 0 | 0 | 0 | 0 |
| `kmhmax` | `121` | m^2/s | float32 | 0 | 0 | 7.93701e-09 | 1009.69 |
| `kmhmin` | `121` | m^2/s | float32 | 0 | 0 | 0 | 0 |
| `kmvmax` | `121` | m^2/s | float32 | 0 | 0 | 7.93701e-09 | 1009.69 |
| `kmvmin` | `121` | m^2/s | float32 | 0 | 0 | 0 | 0 |
| `khhmax` | `121` | m^2/s | float32 | 0 | 0 | 7.95288e-09 | 3029.07 |
| `khhmin` | `121` | m^2/s | float32 | 0 | 0 | 0 | 0 |
| `khvmax` | `121` | m^2/s | float32 | 0 | 0 | 7.95288e-09 | 3029.07 |
| `khvmin` | `121` | m^2/s | float32 | 0 | 0 | 0 | 0 |
| `divmax` | `121` | 1/s | float32 | 0 | 0 | 4.59565e-10 | 0.000662977 |
| `divmin` | `121` | 1/s | float32 | 0 | 0 | -0.00066118 | -3.57628e-10 |
| `rhmax` | `121` | nondimensional | float32 | 0 | 0 | 0.956581 | 1.00158 |
| `rhmin` | `121` | nondimensional | float32 | 0 | 0 | 0.0398839 | 0.250031 |
| `rhimax` | `121` | nondimensional | float32 | 0 | 0 | 0.827855 | 2.08245 |
| `rhimin` | `121` | nondimensional | float32 | 0 | 0 | 0.0561745 | 0.433417 |
| `themax` | `121` | K | float32 | 0 | 0 | 343.879 | 353.588 |
| `themin` | `121` | K | float32 | 0 | 0 | 320.435 | 323.303 |
| `sthemax` | `121` | K | float32 | 0 | 0 | 341.425 | 344.722 |
| `sthemin` | `121` | K | float32 | 0 | 0 | 320.719 | 341.41 |
| `qctop` | `121` | m | float32 | 0 | 0 | 0 | 18250 |
| `qcbot` | `121` | m | float32 | 0 | 0 | 0 | 1750 |
| `sprsmax` | `121` | Pa | float32 | 0 | 0 | 97212.7 | 97445.4 |
| `sprsmin` | `121` | Pa | float32 | 0 | 0 | 96943.6 | 97212.7 |
| `psfcmax` | `121` | Pa | float32 | 0 | 0 | 100006 | 100285 |
| `psfcmin` | `121` | Pa | float32 | 0 | 0 | 99753.2 | 100006 |
| `wspmax` | `121` | m/s | float32 | 0 | 0 | 31.7805 | 75.6081 |
| `wspmin` | `121` | m/s | float32 | 0 | 0 | 0.0045643 | 1.37224 |
| `zwspmax` | `121` | m AGL | float32 | 0 | 0 | 6250 | 13750 |
| `zwspmin` | `121` | m AGL | float32 | 0 | 0 | 250 | 2250 |
| `swspmax` | `121` | m/s | float32 | 0 | 0 | 1.37224 | 22.4032 |
| `swspmin` | `121` | m/s | float32 | 0 | 0 | 0.0045643 | 1.37224 |
| `cflmax` | `121` | nondimensional | float32 | 0 | 0 | 0.113565 | 0.732732 |
| `kshmax` | `121` | nondimensional | float32 | 0 | 0 | 4.77173e-14 | 0.0181744 |
| `ksvmax` | `121` | nondimensional | float32 | 0 | 0 | 1.90869e-13 | 0.0726977 |
| `vortsfc` | `121` | 1/s | float32 | 0 | 0 | 0 | 0.0131319 |
| `vort1km` | `121` | 1/s | float32 | 0 | 0 | 0 | 0.0194462 |
| `vort2km` | `121` | 1/s | float32 | 0 | 0 | 0 | 0.0268747 |
| `vort3km` | `121` | 1/s | float32 | 0 | 0 | 0 | 0.032507 |
| `vort4km` | `121` | 1/s | float32 | 0 | 0 | 0 | 0.0372882 |
| `vort5km` | `121` | 1/s | float32 | 0 | 0 | 0 | 0.0396727 |
| `tmass` | `121` | kg | float32 | 0 | 0 | 1.37658e+14 | 1.37658e+14 |
| `tmois` | `121` | kg | float32 | 0 | 0 | 6.58994e+11 | 6.97597e+11 |
| `massqv` | `121` | kg | float32 | 0 | 0 | 6.4464e+11 | 6.58995e+11 |
| `massqc` | `121` | kg | float32 | 0 | 0 | 0 | 4.66139e+09 |
| `massqr` | `121` | kg | float32 | 0 | 0 | 0 | 7.47342e+09 |
| `massqi` | `121` | kg | float32 | 0 | 0 | 0 | 4.9849e+09 |
| `massqs` | `121` | kg | float32 | 0 | 0 | 0 | 7.86339e+09 |
| `massqg` | `121` | kg | float32 | 0 | 0 | 0 | 2.79745e+10 |
| `ek` | `121` | kg m^2/s^2 | float32 | 0 | 0 | 1.49988e+16 | 1.79873e+16 |
| `ei` | `121` | kg m^2/s^2 | float32 | 0 | 0 | 2.58664e+19 | 2.58933e+19 |
| `ep` | `121` | kg m^2/s^2 | float32 | 0 | 0 | 8.65337e+18 | 8.66014e+18 |
| `le` | `121` | kg m^2/s^2 | float32 | 0 | 0 | -1.20967e+17 | 0 |
| `et` | `121` | kg m^2/s^2 | float32 | 0 | 0 | 3.44338e+19 | 3.45348e+19 |
| `tmu` | `121` | kg m/s | float32 | 0 | 0 | 2.72184e+15 | 2.83116e+15 |
| `tmv` | `121` | kg m/s | float32 | 0 | 0 | 8.80055e+14 | 8.92882e+14 |
| `tmw` | `121` | kg m/s | float32 | 0 | 0 | -5.76576e+09 | 2.6571e+13 |
| `tmfu` | `121` | kg m/s | float32 | 0 | 0 | 0 | 1.35224e+11 |
| `tmfd` | `121` | kg m/s | float32 | 0 | 0 | -8.26777e+10 | 0 |
| `tcond` | `121` | unk | float32 | 0 | 0 | 0 | 1.1886e+11 |
| `tevac` | `121` | unk | float32 | 0 | 0 | 0 | 1.29007e+10 |
| `tauto` | `121` | unk | float32 | 0 | 0 | 0 | 0 |
| `taccr` | `121` | unk | float32 | 0 | 0 | 0 | 0 |
| `tevar` | `121` | unk | float32 | 0 | 0 | 0 | 1.72834e+10 |
| `train` | `121` | unk | float32 | 0 | 0 | 0 | 3.70884e+10 |
| `erain` | `121` | unk | float32 | 0 | 0 | 0 | 0 |
| `qsfc` | `121` | unk | float32 | 0 | 0 | 0 | 0 |
| `esfc` | `121` | unk | float32 | 0 | 0 | 0 | 0 |
| `erad` | `121` | unk | float32 | 0 | 0 | 0 | 0 |
| `asqv` | `121` | kg | float32 | 0 | 0 | 0 | 0 |
| `asqc` | `121` | kg | float32 | 0 | 0 | 0 | 4.53956e+06 |
| `asqr` | `121` | kg | float32 | 0 | 0 | -0.00163693 | 5801.98 |
| `asqi` | `121` | kg | float32 | 0 | 0 | -9.00948e-05 | 5301.85 |
| `asqs` | `121` | kg | float32 | 0 | 0 | -1.82177e-05 | 11345 |
| `asqg` | `121` | kg | float32 | 0 | 0 | -7.50968e-05 | 24915.5 |
| `asnci` | `121` | kg | float32 | 0 | 0 | 0 | 0 |
| `asncs` | `121` | kg | float32 | 0 | 0 | 0 | 0 |
| `asncr` | `121` | kg | float32 | 0 | 0 | 0 | 0 |
| `asncg` | `121` | kg | float32 | 0 | 0 | 0 | 0 |
| `bsqv` | `121` | kg | float32 | 0 | 0 | 0 | 7.54615e+10 |
| `bsqc` | `121` | kg | float32 | 0 | 0 | -1.9549e+06 | 48198.5 |
| `bsqr` | `121` | kg | float32 | 0 | 0 | -569.37 | 1.83062e+06 |
| `bsqi` | `121` | kg | float32 | 0 | 0 | -1.12535e+09 | 7.16076e-05 |
| `bsqs` | `121` | kg | float32 | 0 | 0 | -9.39321e+08 | 6.11926e-07 |
| `bsqg` | `121` | kg | float32 | 0 | 0 | -2.76612e+06 | 0.000349633 |
| `bsnci` | `121` | kg | float32 | 0 | 0 | -1.51516e+18 | 91963.2 |
| `bsncs` | `121` | kg | float32 | 0 | 0 | -8.79469e+16 | 417164 |
| `bsncr` | `121` | kg | float32 | 0 | 0 | -9.05237e+12 | 2.70216e+11 |
| `bsncg` | `121` | kg | float32 | 0 | 0 | -4.01726e+15 | 0 |
| `xh` | `1` | degree_east | float32 | 0 | 0 | 0 | 0 |
| `yh` | `1` | degree_north | float32 | 0 | 0 | 0 | 0 |
| `zh` | `1` | m | float32 | 0 | 0 | 0 | 0 |
| `time` | `121` | seconds | float32 | 0 | 0 | 0 | 7200 |

All statistics times were finite and covered 0-7,200 s at the stock 60-s cadence.

## 11. Grid, active top, coordinates, and moving domain

The scalar grid was 120 x 120 x 40; scalar spacing was 1000 x 1000 x 500 m. Native x/y/z staggered dimensions were preserved. The unstretched emitted z-face top was 20000 m. The inactive namelist `ztop=18000` did not control the active grid. Coordinates were invariant across all histories. Terrain was flat and no terrain field was requested.

Native `u`, `v`, and `w` are on `xf`, `yf`, and `zf`; `uinterp`, `vinterp`, and `winterp` are scalar-grid products. Native winds are model-relative. Ground-relative winds add `(12.5, 3.0) m/s`.

## 12. Analytic thermodynamic, hodograph, frame, and trigger verification

The hash-pinned `isnd=5` source defines the Weisman-Klemp analytic thermodynamic profile; `iwnd=2` defines the quarter-circle wind through 2 km, an increase to the 6-km wind, and constant wind aloft. The emitted surface-to-6-km vector difference was [29.36549663543701, 5.6343677043914795] m/s, with magnitude 29.901 m/s versus the Gate A 31.78 m/s reference.

The deterministic `iinit=1` bubble was source-verified at domain center, 1,400 m AGL, with 10,000 m horizontal and 1,400 m vertical radii, 1 K maximum perturbation, no random perturbation, no pressure balancing, and `maintain_rh=false`. The initial history's sampled maximum theta perturbation was 0.9599 K at {'x_m': -500.0, 'y_m': -500.0, 'z_m': 1250.0}.

No CAPE/CIN value was promoted from the paper; emitted theta, pressure, and moisture profiles are the native benchmark evidence.

### Initial native profile

| z (m) | theta (K) | pressure (Pa) | qv (kg/kg) | u model | v model | u ground | v ground |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 250 | 300.34 | 97212.66 | 0.014 | -12.365 | -1.6344 | 0.1345 | 1.3656 |
| 750 | 301.34 | 91803.53 | 0.014 | -11.32 | 0.88899 | 1.1797 | 3.889 |
| 1250 | 302.54 | 86631.27 | 0.013813 | -9.389 | 2.8203 | 3.111 | 5.8203 |
| 1750 | 303.88 | 81687.11 | 0.011323 | -6.8656 | 3.8655 | 5.6344 | 6.8655 |
| 2250 | 305.31 | 76962.77 | 0.0092519 | -4 | 4 | 8.5 | 7 |
| 2750 | 306.82 | 72453.28 | 0.0075268 | -1 | 4 | 11.5 | 7 |
| 3250 | 308.4 | 68153.13 | 0.0060914 | 2 | 4 | 14.5 | 7 |
| 3750 | 310.05 | 64056.38 | 0.0049002 | 5 | 4 | 17.5 | 7 |
| 4250 | 311.75 | 60156.84 | 0.0039154 | 8 | 4 | 20.5 | 7 |
| 4750 | 313.5 | 56448.11 | 0.0031052 | 11 | 4 | 23.5 | 7 |
| 5250 | 315.3 | 52923.75 | 0.0024424 | 14 | 4 | 26.5 | 7 |
| 5750 | 317.14 | 49577.23 | 0.0019039 | 17 | 4 | 29.5 | 7 |
| 6250 | 319.03 | 46402.07 | 0.0014697 | 18.5 | 4 | 31 | 7 |
| 6750 | 320.95 | 43391.82 | 0.0011224 | 18.5 | 4 | 31 | 7 |
| 7250 | 322.9 | 40540.11 | 0.00084726 | 18.5 | 4 | 31 | 7 |
| 7750 | 324.9 | 37840.64 | 0.00063149 | 18.5 | 4 | 31 | 7 |
| 8250 | 326.92 | 35287.28 | 0.00046417 | 18.5 | 4 | 31 | 7 |
| 8750 | 328.97 | 32873.97 | 0.00033602 | 18.5 | 4 | 31 | 7 |
| 9250 | 331.06 | 30594.82 | 0.00023919 | 18.5 | 4 | 31 | 7 |
| 9750 | 333.17 | 28444.1 | 0.00016711 | 18.5 | 4 | 31 | 7 |
| 10250 | 335.31 | 26416.21 | 0.00011434 | 18.5 | 4 | 31 | 7 |
| 10750 | 337.48 | 24505.71 | 7.6405e-05 | 18.5 | 4 | 31 | 7 |
| 11250 | 339.67 | 22707.35 | 4.9687e-05 | 18.5 | 4 | 31 | 7 |
| 11750 | 341.88 | 21016.01 | 3.1299e-05 | 18.5 | 4 | 31 | 7 |
| 12250 | 346.95 | 19433.08 | 2.5664e-05 | 18.5 | 4 | 31 | 7 |
| 12750 | 354.99 | 17964.38 | 2.811e-05 | 18.5 | 4 | 31 | 7 |
| 13250 | 363.21 | 16607.31 | 3.0796e-05 | 18.5 | 4 | 31 | 7 |
| 13750 | 371.62 | 15353.33 | 3.3747e-05 | 18.5 | 4 | 31 | 7 |
| 14250 | 380.23 | 14194.6 | 3.6991e-05 | 18.5 | 4 | 31 | 7 |
| 14750 | 389.03 | 13123.84 | 4.0555e-05 | 18.5 | 4 | 31 | 7 |
| 15250 | 398.05 | 12134.34 | 4.4476e-05 | 18.5 | 4 | 31 | 7 |
| 15750 | 407.26 | 11219.92 | 4.8788e-05 | 18.5 | 4 | 31 | 7 |
| 16250 | 416.7 | 10374.86 | 5.3533e-05 | 18.5 | 4 | 31 | 7 |
| 16750 | 426.35 | 9593.854 | 5.8755e-05 | 18.5 | 4 | 31 | 7 |
| 17250 | 436.22 | 8872.041 | 6.4506e-05 | 18.5 | 4 | 31 | 7 |
| 17750 | 446.33 | 8204.909 | 7.0839e-05 | 18.5 | 4 | 31 | 7 |
| 18250 | 456.67 | 7588.295 | 7.7818e-05 | 18.5 | 4 | 31 | 7 |
| 18750 | 467.24 | 7018.357 | 8.551e-05 | 18.5 | 4 | 31 | 7 |
| 19250 | 478.06 | 6491.542 | 9.3991e-05 | 18.5 | 4 | 31 | 7 |
| 19750 | 489.14 | 6004.571 | 0.00010335 | 18.5 | 4 | 31 | 7 |

## 13. Deep cloud, hydrometeors, precipitation, reflectivity, and motion

| Time (min) | w min | w max | Cloud top (km) | dBZ max | Rain max | qc | qr | qi | qs | qg |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | n/a | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 15 | -1.35 | 4.1 | 4.75 | -22.8 | 5.23e-13 | 0.00165 | 8.65e-07 | 0 | 0 | 0 |
| 30 | -7.27 | 29.4 | 12.25 | 65.4 | 0.00189 | 0.0032 | 0.00779 | 0.00127 | 0.0013 | 0.00821 |
| 45 | -24.3 | 49 | 17.25 | 67.2 | 1.5 | 0.00479 | 0.00776 | 0.0021 | 0.00127 | 0.011 |
| 60 | -27.5 | 55.3 | 18.75 | 68.3 | 3.79 | 0.00692 | 0.00797 | 0.00163 | 0.00129 | 0.0131 |
| 75 | -29.8 | 60.2 | 18.75 | 69.5 | 6.55 | 0.00786 | 0.00852 | 0.00202 | 0.00153 | 0.0137 |
| 90 | -34.7 | 58.9 | 19.25 | 67.6 | 7.64 | 0.00745 | 0.00789 | 0.00279 | 0.00129 | 0.0127 |
| 105 | -35.6 | 59.5 | 18.75 | 67.4 | 7.84 | 0.00787 | 0.00876 | 0.00283 | 0.00188 | 0.0134 |
| 120 | -38.8 | 55.8 | 18.75 | 67.7 | 8.09 | 0.00811 | 0.00973 | 0.00266 | 0.00206 | 0.0142 |

Materially evolving hydrometeor categories: qc, qr, qi, qs, qg. `qg`/`ncg` are treated as one hail-configured large-ice category, not double-counted.

### Number-concentration maxima by time (#/kg)

| Time (min) | nci | ncs | ncr | ncg |
|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 0 |
| 15 | 0 | 0 | 10912 | 0 |
| 30 | 8.9237e+05 | 64865 | 42031 | 27389 |
| 45 | 1.2269e+06 | 1.1805e+05 | 1.0972e+05 | 38641 |
| 60 | 1.6369e+06 | 1.0392e+05 | 2.8209e+05 | 45374 |
| 75 | 1.6091e+06 | 1.0948e+05 | 3.7879e+05 | 72774 |
| 90 | 1.6709e+06 | 1.0219e+05 | 3.4436e+05 | 80574 |
| 105 | 1.7815e+06 | 1.3067e+05 | 3.8717e+05 | 60821 |
| 120 | 1.7859e+06 | 1.2689e+05 | 4.0558e+05 | 86277 |

## 14. Vorticity, updraft helicity, swaths, and organized rotation

| Time (min) | Primary w | zvort at primary w | zvort max | UH max | Rotating-updraft cells |
|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 0 | 0 |
| 15 | 3.91 | 0.00017 | 0.00141 | 4.68 | 0 |
| 30 | 27.8 | 0.00083 | 0.0206 | 901 | 188 |
| 45 | 49 | 0.00844 | 0.0208 | 663 | 283 |
| 60 | 55.1 | 0.00735 | 0.0251 | 648 | 595 |
| 75 | 60.1 | 0.0131 | 0.0267 | 702 | 854 |
| 90 | 58.7 | 0.0135 | 0.0308 | 628 | 851 |
| 105 | 59.2 | 0.0156 | 0.0307 | 752 | 949 |
| 120 | 55.7 | 0.0107 | 0.0229 | 661 | 998 |

Joint mature-frame screen: [2700.0, 3600.0, 4500.0, 5400.0, 6300.0, 7200.0] s. Sustained organized rotation: True. This combines structure, signed motion, vorticity collocation, UH, reflectivity, rain, and hydrometeors rather than approving one maximum.

### Native and translated surface-product maxima

| Time (min) | Product | Maximum | Nonzero cells |
|---:|---|---:|---:|
| 0 | `sws` | 0 | 0 |
| 0 | `svs` | -1000 | 14400 |
| 0 | `sps` | 2e+05 | 14400 |
| 0 | `srs` | 0 | 0 |
| 0 | `sgs` | 0 | 0 |
| 0 | `sus` | -1000 | 14400 |
| 0 | `shs` | 0 | 0 |
| 0 | `rain2` | 0 | 0 |
| 0 | `sws2` | 0 | 0 |
| 0 | `svs2` | -1000 | 14400 |
| 0 | `sps2` | 2e+05 | 14400 |
| 0 | `srs2` | 0 | 0 |
| 0 | `sgs2` | 0 | 0 |
| 0 | `sus2` | -1000 | 14400 |
| 0 | `shs2` | 0 | 0 |
| 15 | `sws` | 2.3375 | 14400 |
| 15 | `svs` | 0.00015609 | 14149 |
| 15 | `sps` | -0.10156 | 14400 |
| 15 | `srs` | 0 | 0 |
| 15 | `sgs` | 0 | 0 |
| 15 | `sus` | 0.31021 | 14400 |
| 15 | `shs` | 4.6804 | 13636 |
| 15 | `rain2` | 6.0948e-13 | 1112 |
| 15 | `sws2` | 2.3275 | 14400 |
| 15 | `svs2` | 0.00015586 | 14400 |
| 15 | `sps2` | -0.11986 | 14400 |
| 15 | `srs2` | 0 | 0 |
| 15 | `sgs2` | 0 | 0 |
| 15 | `sus2` | 0.31188 | 14400 |
| 15 | `shs2` | 4.5051 | 14220 |
| 30 | `sws` | 5.4478 | 14400 |
| 30 | `svs` | 0.00049685 | 14155 |
| 30 | `sps` | -0.10156 | 14400 |
| 30 | `srs` | 2.8329e-05 | 199 |
| 30 | `sgs` | 1.693e-05 | 45 |
| 30 | `sus` | 25.104 | 14400 |
| 30 | `shs` | 901.87 | 13963 |
| 30 | `rain2` | 0.0019372 | 3996 |
| 30 | `sws2` | 5.4329 | 14400 |
| 30 | `svs2` | 0.00046395 | 14400 |
| 30 | `sps2` | -0.12462 | 14400 |
| 30 | `srs2` | 2.8326e-05 | 3650 |
| 30 | `sgs2` | 1.698e-05 | 1968 |
| 30 | `sus2` | 25.045 | 14400 |
| 30 | `shs2` | 887.5 | 14310 |
| 45 | `sws` | 7.5276 | 14400 |
| 45 | `svs` | 0.0012249 | 14339 |
| 45 | `sps` | -0.10156 | 14400 |
| 45 | `srs` | 0.0053638 | 711 |
| 45 | `sgs` | 0.00028793 | 242 |
| 45 | `sus` | 31.151 | 14400 |
| 45 | `shs` | 901.87 | 13977 |
| 45 | `rain2` | 0.94551 | 6456 |
| 45 | `sws2` | 7.507 | 14400 |
| 45 | `svs2` | 0.0012349 | 14400 |
| 45 | `sps2` | -0.14659 | 14400 |
| 45 | `srs2` | 0.0053678 | 6194 |
| 45 | `sgs2` | 0.00028714 | 4956 |
| 45 | `sus2` | 31.726 | 14400 |
| 45 | `shs2` | 784.26 | 14329 |
| 60 | `sws` | 14.392 | 14400 |
| 60 | `svs` | 0.0032414 | 14389 |
| 60 | `sps` | -0.10156 | 14400 |
| 60 | `srs` | 0.0053831 | 1391 |
| 60 | `sgs` | 0.00028824 | 494 |
| 60 | `sus` | 32.731 | 14400 |
| 60 | `shs` | 901.87 | 14305 |
| 60 | `rain2` | 1.4455 | 8473 |
| 60 | `sws2` | 14.292 | 14400 |
| 60 | `svs2` | 0.0032223 | 14400 |
| 60 | `sps2` | -0.14641 | 14400 |
| 60 | `srs2` | 0.005179 | 8298 |
| 60 | `sgs2` | 0.000218 | 6946 |
| 60 | `sus2` | 32.712 | 14400 |
| 60 | `shs2` | 715.17 | 14366 |
| 75 | `sws` | 16.945 | 14400 |
| 75 | `svs` | 0.0080538 | 14397 |
| 75 | `sps` | -0.10156 | 14400 |
| 75 | `srs` | 0.0053831 | 2676 |
| 75 | `sgs` | 0.00052396 | 1001 |
| 75 | `sus` | 36.514 | 14400 |
| 75 | `shs` | 901.87 | 14400 |
| 75 | `rain2` | 1.7402 | 10156 |
| 75 | `sws2` | 16.882 | 14400 |
| 75 | `svs2` | 0.0078459 | 14400 |
| 75 | `sps2` | -0.14786 | 14400 |
| 75 | `srs2` | 0.0052209 | 10009 |
| 75 | `sgs2` | 0.00052475 | 8485 |
| 75 | `sus2` | 35.987 | 14400 |
| 75 | `shs2` | 722.45 | 14381 |
| 90 | `sws` | 18.626 | 14400 |
| 90 | `svs` | 0.010044 | 14398 |
| 90 | `sps` | -0.10156 | 14400 |
| 90 | `srs` | 0.0053831 | 4420 |
| 90 | `sgs` | 0.00071115 | 1450 |
| 90 | `sus` | 37.974 | 14400 |
| 90 | `shs` | 901.87 | 14400 |
| 90 | `rain2` | 1.8335 | 11450 |
| 90 | `sws2` | 18.7 | 14400 |
| 90 | `svs2` | 0.0086504 | 14400 |
| 90 | `sps2` | -0.20628 | 14400 |
| 90 | `srs2` | 0.0052852 | 11345 |
| 90 | `sgs2` | 0.00067769 | 9490 |
| 90 | `sus2` | 37.48 | 14400 |
| 90 | `shs2` | 821.73 | 14392 |
| 105 | `sws` | 21.905 | 14400 |
| 105 | `svs` | 0.011446 | 14398 |
| 105 | `sps` | -0.14844 | 14400 |
| 105 | `srs` | 0.0053831 | 6132 |
| 105 | `sgs` | 0.00076393 | 1876 |
| 105 | `sus` | 38.338 | 14400 |
| 105 | `shs` | 901.87 | 14400 |
| 105 | `rain2` | 2.1514 | 12406 |
| 105 | `sws2` | 21.917 | 14400 |
| 105 | `svs2` | 0.0097338 | 14400 |
| 105 | `sps2` | -0.20542 | 14400 |
| 105 | `srs2` | 0.0053715 | 12409 |
| 105 | `sgs2` | 0.00075967 | 10106 |
| 105 | `sus2` | 38.208 | 14400 |
| 105 | `shs2` | 795.98 | 14397 |
| 120 | `sws` | 22.413 | 14400 |
| 120 | `svs` | 0.013132 | 14398 |
| 120 | `sps` | -0.14844 | 14400 |
| 120 | `srs` | 0.0053831 | 7661 |
| 120 | `sgs` | 0.00076393 | 2424 |
| 120 | `sus` | 38.338 | 14400 |
| 120 | `shs` | 901.87 | 14400 |
| 120 | `rain2` | 2.5744 | 13034 |
| 120 | `sws2` | 22.236 | 14400 |
| 120 | `svs2` | 0.012438 | 14400 |
| 120 | `sps2` | -0.20478 | 14400 |
| 120 | `srs2` | 0.0053049 | 12956 |
| 120 | `sgs2` | 0.0006658 | 10647 |
| 120 | `sus2` | 37.977 | 14400 |
| 120 | `shs2` | 780.86 | 14398 |

## 15. Structural checkpoints near 45, 75/90, and 120 minutes

- **45 min:** primary scalar w 49 m/s at {'x_m': -7500.000476837158, 'y_m': 5500.000476837158, 'z_m': 10250.000953674316}; max UH 663 m2/s2; max dBZ 67.2; rain-positive cells 707.
- **75 min:** primary scalar w 60.1 m/s at {'x_m': -7500.000476837158, 'y_m': 2500.0, 'z_m': 10250.000953674316}; max UH 702 m2/s2; max dBZ 69.5; rain-positive cells 2669.
- **90 min:** primary scalar w 58.7 m/s at {'x_m': -6500.000476837158, 'y_m': -1500.0001192092896, 'z_m': 10250.000953674316}; max UH 628 m2/s2; max dBZ 67.6; rain-positive cells 4464.
- **120 min:** primary scalar w 55.7 m/s at {'x_m': -1500.0001192092896, 'y_m': -11500.000953674316, 'z_m': 9250.0}; max UH 661 m2/s2; max dBZ 67.7; rain-positive cells 8384.

The 15-minute history cadence supports 45, 75/90, and 120-minute inspection. It does not support claims of exact 40- or 80-minute figure reproduction.

## 16. Lateral boundaries, translation, and upper damping

The minimum saved-frame distance from the primary updraft to any open lateral boundary was 48000 m. The 5-km screen is descriptive because the source provides no pointwise tolerance. Native fields are in the translating model frame; the `*2` products are the emitted translated swath/rain/wind products.

Vertical motion and condensate maxima were recorded separately below 15 km and inside the 15-20 km Rayleigh layer for every history. No absence of top reflection is inferred from the namelist alone.

| Time (min) | w max below 15 km | w max 15-20 km | condensate max below | condensate max 15-20 km |
|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 0 |
| 15 | 3.9101 | 0.082236 | 0.0016505 | 0 |
| 30 | 27.828 | 0.22662 | 0.0098157 | 0 |
| 45 | 48.997 | 9.9501 | 0.012985 | 6.8256e-06 |
| 60 | 55.09 | 22.559 | 0.014742 | 0.0078144 |
| 75 | 60.087 | 17.481 | 0.015201 | 0.0052686 |
| 90 | 58.717 | 21.123 | 0.014514 | 0.0049696 |
| 105 | 59.174 | 16.059 | 0.014968 | 0.0024074 |
| 120 | 55.74 | 16.235 | 0.01551 | 0.001937 |

## 17. Runtime integrity, storage, warnings, and cost

The process ran for 552.652 s and retained 186,849,921 bytes. History output used 184,178,903 bytes; statistics used 1,052,565; logs used 779,923. Floating-point flags: ['IEEE_UNDERFLOW_FLAG']. Normal termination and finite required fields were both verified. Peak memory was not captured by the current launcher.

## 18. Qualitative lineage and stock-versus-paper differences

The official README links this case to Weisman and Rotunno (2000), and the analytic sounding lineage is Weisman and Klemp (1982). This run reproduces the stock CM1 r21.1 configuration, not the paper's exact numerical implementation or saved figure times. Grid, microphysics, output cadence, and other stock-r21.1 details therefore remain distinct from a pixel-level paper reproduction.

## 19. Cloud Chamber implications and limits

This gate establishes mechanics and practical cost for one source-locked storm benchmark. It does not select a permanent World, Recipe, UI, trigger, sounding, or general storm framework. Examination and product meaning remain later decisions.

## 20. Unresolved questions

- PM/scientific review must inspect the retained spatial evidence before accepting the structural judgment.
- The launcher does not currently record peak memory.
- The source supplies no pointwise boundary- or damping-contamination tolerance.
- A later gate would need to define examination, not rerun or tune this benchmark.

## 21. Final disposition

`advance_to_storm_examination_validation`
