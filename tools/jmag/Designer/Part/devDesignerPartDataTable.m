function PartDataStruct=devDesignerPartDataTable(MachineData,app,isConductor)
%% devfunDesignerPartDataTable.mlx
% DEVDESIGNERPARTDATATABLE 2. Designer-PartStruct -> 
% 파트 현재정보
% 
% 
% devDesignerPartDataTable
% 
% defJMAGDesignerPartStruct
if nargin==3
isConductor=1;
end
  Poles              = MachineData.Poles               ;   
  StatorOneSlotAngle = MachineData.StatorOneSlotAngle  ;               
  PhaseNumber        = MachineData.PhaseNumber         ;       
  NSPP               = MachineData.NSPP                ;   
  q                  = MachineData.q                   ;
  slots              = MachineData.slots               ;   
  runnerType         = MachineData.runnerType          ;
PartStruct=getJMAGDesignerPartStruct(app);
deleteIndices = false(length(PartStruct), 1); % 삭제할 인덱스를 저장할 논리적 배열 초기화
for partIndex = 1:length(PartStruct)
    if isempty(PartStruct(partIndex).Vertex)
        deleteIndices(partIndex) = true;
    end
end
PartStruct(deleteIndices) = []; % 한 번에 모든 빈 요소 삭제
% 포지션 정보 테이블에 넣기
% 다른 파트들의 포지션정보도 따기 Edge(Line,Arc)와 Vertex 
PartStruct=getEdgeVertexIdwithXYZCheck(PartStruct,app);   
    MatchedVertexTable=findIntersectVertexinPartStruct(PartStruct);    
        % if strcmp(runnerType,'InnerRotor')
        % % 내전형
        % OutMostConductorEdgeDesignerTable=findOutMostConductorEdgeTable(PartStruct);
        % elseif strcmp(runnerType,'OuteRotor')
        % % 외전형
        % InnerMostConductorEdgeTable=findInnerMostConductorEdgeTable(PartStruct);
        % end
    tolerance=1e-5;
        if contains({PartStruct.Name},'Insulation','IgnoreCase',true)
            %% Insulation
            Name2="Insulation";
            isInsulation=contains({PartStruct.Name},Name2);
            InsulationStruct=PartStruct(isInsulation);
            
            % Find Center Vertex 
            % Theta is half of Max Angle of Stator
            InsulationTable=struct2Table(InsulationStruct)
            InsulVertexRadius(:)=InsulationStruct.Vertex.VertexPosition(:,4);
            InsulVertexTheta=InsulationStruct.Vertex.VertexPosition(:,5);
        else 
            Name2="Stator";
            isInsulation=contains({PartStruct.Name},Name2);
            InsulationStruct=PartStruct(isInsulation);
            % Find Center Vertex 
            % Theta is half of Max Angle of Stator
            InsulVertexRadius=InsulationStruct(1).Vertex.VertexPosition(:,4);
            InsulVertexTheta=InsulationStruct(1).Vertex.VertexPosition(:,5);
            % [~,RadiusIndex]=sort(InsulVertexRadius,'descend')
            % InsulationStruct.Vertex(RadiusIndex(1),:)
        end
        matchedAngleIndex=abs(uniquetol(InsulVertexTheta)-StatorOneSlotAngle/2)<tolerance;
        if any(matchedAngleIndex)
        StatorCenterVertexDesignerTable=InsulationStruct(matchedAngleIndex).Vertex;
        end
PartTable=struct2table(PartStruct)
ConductorTable=PartTable(contains(PartTable.Name,'Conductor'),:)
% Rotor Part 이름변경(내전형& [WIP]외전형)
% [NF]changeJMAGDesignerPartName Outer & Inner에 따라 내부 함수 차이있음
PartStruct=changeJMAGDesignerPartName(PartStruct,app,MachineData);
%% MagnetTable - LayerTable
  %   {'MagnetTable'        }
  %   {'MinimumRadiusMagnet'}
  %   {'MagnetCenterRadius' }
  %   {'object'             }
  %   {'partIndex'          }
  %   {'Name'               }
  %   {'Area'               }
  %   {'Edge'               }
  %   {'Vertex'             }
  %   {'CentroidPosition'   }
  %   {'FaceColor'          }
  %   {'CenterRadius'       }
  %   {'PointOuter'         }
  %   {'PointInner'         }
  % PartStruct로 부터 Magnet 불러오기 
% Layer별로 자석분류 (면적으로 sort)
% devTempConvert2LayerTable;
LayerTable=Convert2LayerTable(MachineData,PartStruct,app);

%% 자석방향 Edge 선택 알고리즘 > MagnetStruct, EdgeIdTable
%1. 중심축의 Edge의 Start Point와 EndPort의 각도가 같은 엣지들만 선택
%%  getCenterPointofAirBarrierVertex Layer별로Fix % Edge의 StartVertex 와  EndVertex 검사
% [FC] AirBarrier Check기능
LayerTable=getCenterPointofAirBarrierVertex(LayerTable);
% getMagnetizationEdgeFromLayerTable
NewLayerTable=getMagnetizationEdgeFromLayerTable(LayerTable,app) ;
NewLayerTable = sortrows(NewLayerTable,"MinimumRadiusMagnet","descend");
% setMagnetNamePerLayer % Layer별로 자석이름 변경 & Grouping(grouping 은 안함)
MagnetName=setMagnetNamePerLayer(NewLayerTable,app);
%% 
% %% PartDataStruct
PartDataStruct.PartStruct                           =PartStruct;
if isConductor==1
    if any(matchedAngleIndex)
    PartDataStruct.CenterVertexDesignerTable            =StatorCenterVertexDesignerTable;
    end
PartDataStruct.MatchedVertexTable                   =MatchedVertexTable;   
end
PartDataStruct.NewLayerTable                        =NewLayerTable;
%%
        if strcmp(runnerType,'InnerRotor')
        PartDataStruct.OutMostConductorEdgeDesignerTable    =OutMostConductorEdgeDesignerTable;               
        elseif strcmp(runnerType,'OuteRotor')
        PartDataStruct.InnerMostConductorEdgeTable          =InnerMostConductorEdgeTable;               
        end
end