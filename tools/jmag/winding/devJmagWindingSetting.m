

% winding .m !.csv !.dat !.mat !.mes !.mlh !.mot !.msv !.mo !.md !.m4 !.dxf  !.pdf !.mp4

% Winding

%
%% Geom
% 2D 후 Extend -> 코일은?
% [3D]Coil Template
% [2D] Wire Template
%% [WIP]Core 와 Slot Liner의 공통  Vertex 를 찾아서 이걸로 Edge위치 찾기
% Insulation의 외곽 edge 따기 - vertex 위치와 길이로 
% 
% - otherSlotTable -> (ArcTable참조)edge 고르기 ->  vertex 위치가지고 길이산출 -> 길이가 동등한게 
% 두개 이하인 edge 선택
% 
% conductor의 폭, 너비 따기
% 
% 첫번째와 마지막 중앙위치 따기 - 벡터산정
% 
% conductor와 wire Template의 첫 위치비교 - 맞추기
% 
% 턴수개수 세기
%% 
% * 권선 몇턴인지 어떻게 파악? 가능 -> Conductor개수
% * 


WireInfo                    =getWireInfo4GeomWireTemplate(SlotUniqueValueStruct,StatorGeomLineTable,PartStruct,CenterVertexDesignerTable,StatorOneSlotAngle)
faceRegionRefObjStruct      =setWireTemplate(MatchedLineTable,WireInfo,app)
MoveProperty                =getWireTemplateMoveProperty(StatorGeomLineTable,OutMostConductorEdgeDesignerTable,app)  
setWireMove4MatchDXF(faceRegionRefObjStruct,MoveProperty,app)
%% Delete Exist Conductor & Create Circular Pattern
ConductorIndex              =contains(StatorGeomAssemTable.Name,'Conductor');
StatorConductorAssemTable   =StatorGeomAssemTable(ConductorIndex,:)
geomsel=geomApp.GetDocument().GetSelection();
for ConductorIndex=1:height(StatorConductorAssemTable)
   geomsel.AddReferenceObject(StatorConductorAssemTable.ReferenceObj(ConductorIndex))
end
   geomsel.Delete();
   %%Circular Pattern
%% 
%% Designer - Winding Editor
% 
% 
% 
%% Circuit