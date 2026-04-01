# Notebook Function Inventory (Baseline)

Source notebook:
- mlxperPJT/pyMotorGeo_v1.ipynb

Captured on:
- 2026-03-31

## Summary

- Inline function definitions found: ~47
- Main cluster: fallback-safe environment cell
- Additional helper: `_manual_parse_dxf_entities`

## Detected Function Names (baseline)

1. `_calc_r_bounds`
2. `read_entity_list`
3. `find_origin_candidates`
4. `find_concentric_radii`
5. `classify_inner_outer_rotor`
6. `split_stator_rotor_by_arc_span`
7. `_estimate_repeat_from_angles`
8. `count_poles`
9. `count_slots`
10. `count_poles_by_regions`
11. `estimate_poles_robust`
12. `count_slots_by_regions`
13. `estimate_slots_robust`
14. `detect_slot_conductors`
15. `detect_circular_array_pattern`
16. `extract_single_pole_entities`
17. `extract_single_slot_entities`
18. `classify_pole_topology`
19. `analyze_rotor_topology`
20. `_angle_deg`
21. `extract_half_pole_entities`
22. `extract_half_slot_entities`
23. `rotate_entity`
24. `mirror_entity`
25. `reconstruct_from_half`
26. `classify_rotor_entities`
27. `classify_stator_entities`
28. `reassign_rotor_region`
29. `get_rotor_region_summary`
30. `reassign_stator_region`
31. `get_stator_region_summary`
32. `check_pyleecan_available`
33. `extract_dimensions_from_dxf`
34. `create_pyleecan_machine`
35. `dims_to_summary`
36. `create_radial_line`
37. `create_arc_boundary`
38. `close_rotor_period`
39. `close_stator_period`
40. `close_period_model`
41. `close_one_pole`
42. `close_one_slot`
43. `detect_closed_faces`
44. `auto_name_faces`
45. `get_face_summary`
46. `plot_faces_static`
47. `_manual_parse_dxf_entities`

## Planned Migration Buckets

- Reader/import: 1, 2, 47
- Airgap/split: 3, 4, 5, 6
- Pole/slot estimation: 7-13, 15
- Half-unit/symmetry: 20-25
- Topology/regions: 18, 19, 26-31
- Region closing/faces: 36-46
- Bridge: 32-35

## Notes

- Notebook visualization function block already migrated separately to package wrapper call.
- This inventory is the baseline reference for migration progress tracking.
