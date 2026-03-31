classDiagram
    %% Core Classes
    class EntityInfo {
        <<dataclass>>
        +str etype
        +str layer
        +list[tuple] points
        +float radius
        +tuple center
        +float start_angle 
        +float end_angle
        +bool is_closed
        +object raw
        +float r_min()
        +float r_max()
        +to_dict() dict
        +from_dict(d: dict) EntityInfo
    }

    class StatorRotorSplit{
        <<dataclass>>
        +list[EntityInfo] stator
        +list[EntityInfo] rotor
        +float airgap_r_inner
        +float airgap_r_outer
        +float airgap_r_mid
    }
    
    %% Helper / Utility modules loosely grouped
    class CoreTransforms {
        <<module: core>>
        +rotate_entity(ei, angle, origin)
        +mirror_entity(ei, axis_deg, origin)
        +translate_entity(ei, dx, dy)
        +normalize_angles(angle)
    }

    class ReaderModule {
        <<module: reader>>
        +read_entity_list(dxf_path)
        -extract_entities_from_layout()
        -explode_insert()
        -transform_point()
    }
    
    class HalfUnitModule {
        <<module: half_unit>>
        +extract_half_pole_entities()
        +extract_half_slot_entities()
        +reconstruct_from_half()
        -_clip_concentric_arc()
        -_make_concentric_radials()
    }

    ReaderModule ..> EntityInfo : generates
    CoreTransforms ..> EntityInfo : transforms
    HalfUnitModule ..> EntityInfo : extracts & reconstructs
    StatorRotorSplit --> EntityInfo : contains 