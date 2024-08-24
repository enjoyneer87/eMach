function settedConductorData=getConductorData(mcad)
     %% Winding
        settedConductorData =struct();
        [~,settedConductorData.Armature_CoilStyle         ] = mcad.GetVariable('Armature_CoilStyle'          ) ;% Coil Style : Hairpin
        [~,settedConductorData.Insulation_Thickness       ] = mcad.GetVariable('Insulation_Thickness'        ) ;% 도체 절연체 두께
        [~,settedConductorData.Liner_Thickness            ] = mcad.GetVariable('Liner_Thickness'             ) ;% 절연지 두께
        [~,settedConductorData.WindingLayers              ] = mcad.GetVariable('WindingLayers'               ); % 슬롯 내 턴 수
        [~,settedConductorData.ParallelPaths_Hairpin      ] = mcad.GetVariable('ParallelPaths_Hairpin'       ) ; % 병렬 수
        [~,settedConductorData.ConductorSeparation        ] = mcad.GetVariable('ConductorSeparation'         );% 방사방향 도체 사이 거리
        [~,settedConductorData.HairpinWindingPatternMethod] = mcad.GetVariable('HairpinWindingPatternMethod' ) ; % Improved
        [~,settedConductorData.MagThrow                   ] = mcad.GetVariable('MagThrow'                    );% 권선 피치
        [~,settedConductorData.temp_fillfactor            ] = mcad.GetVariable('Copper_Slot_Fill_(Wdg_Area)'                    );% 권선 피치

        
        % Hair-pin coil
        validGeometry=mcad.CheckIfGeometryIsValid(1);  % Motor-CAD 자체 기능
        [~,settedConductorData.Area_Slot]                     =mcad.GetVariable('Area_Slot');                  % 슬롯 영역 넓이
        [~,settedConductorData.Area_Winding_With_Liner]       =mcad.GetVariable('Area_Winding_With_Liner');    % 직사각각형 슬롯 영역 넓이
        [~,settedConductorData.Slot_Width]                    =mcad.GetVariable('Slot_Width');                 % 슬롯 너비 (회전방향)
        [~,settedConductorData.Winding_Depth]                 =mcad.GetVariable('Winding_Depth');              % 직사각형 슬롯 깊이 (방사방향)
end