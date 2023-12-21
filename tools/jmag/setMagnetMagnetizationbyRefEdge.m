function setMagnetMagnetizationbyRefEdge(NewLayerTable,app,MagNetMaterial)
% [Parallel Pattern (Any Circular Direction)] PartStruct -> PartStructByType-> AirBarrierTable ->VerTexTable -> vertexStruct
% 주어진 방향으로 자화 벡터가 설정된 극을 원주 방향으로 반복하면서 반복할 때마다 편광을 반전시켜 형성된 패턴입니다.
% 이 패턴을 선택하면 먼저 원통형 좌표계를 정의합니다. 그런 다음 원주 패턴 시작 위치([기준축으로부터의 각도])와 주기당 극 수를 설정합니다. 그런 다음 자화 방향을 지정합니다.
% 패턴 시작 위치([기준 축으로부터의 각도]) 및 [극 개수]
% [Use Mirror Copy against Angle from Reference Axis]
% 이 옵션을 사용할 때는 자석 자화 패턴을 설정하기 전에 두 영역의 자석을 포함하는 부품 그룹을 만들어야 합니다.
% if nargin<3
if isstruct(NewLayerTable)
NewLayerTable=NewLayerTable.NewLayerTable;
elseif istable(NewLayerTable)
NewLayerTable=NewLayerTable;
end
MagnetName=setMagnetNamePerLayer(NewLayerTable,app);
%% Equation
Model                   =app.GetCurrentModel;
CurrentStudy            =app.GetCurrentStudy;
ModelEquation           =Model.GetEquation(0);
ValueName               =ModelEquation.GetName;
value                   =ModelEquation.GetExpression;
value                   =str2double(value);
onePoleCenterAngle      =360/value/2;
% Radius가 큰거부터 선택 
      for LayerIndex=1:height(NewLayerTable)
          % MagnetLayer selection
            oneLayerMagnetTable=NewLayerTable.MagnetTable(LayerIndex,:);
            if iscell(oneLayerMagnetTable) && length(oneLayerMagnetTable)==1
            oneLayerMagnetTable=oneLayerMagnetTable{:};
            end
            selMagnetInner=Model.CreateSelection();

            % Edge  선택해야됨
            %% - 내측 Edge만 선택됨, referenceObject 만들기
            % make referenceobject Edge
            %2. 선택된 Edge들중 중심 Point의 Radius가 작은 Edge 선택 (불필요)
            MagEdgeIndex = oneLayerMagnetTable.Edge{1}(oneLayerMagnetTable.Edge{1}.MagnetMagnetizeEdge ==1, 1);
            PerpendicularEdge=MagEdgeIndex.EdgeIds(1);
            
            refTarget=Model.GetReferenceTargetList;
            EdgeRefTarget=refTarget.CreateEdgeReferenceTarget([MagnetName{LayerIndex},'MagEdge']);
            sel=EdgeRefTarget.GetSelection;
            sel.SelectEdge(PerpendicularEdge);
            EdgeRefTarget.AddSelected(sel);
            EdgeRefTarget.SetParallelDirection(0);
            OuterMagnetMagEdge=refTarget.GetReferenceTarget([MagnetName{LayerIndex},'MagEdge']);

            % Selection 후  하나식 셋팅이네
            for partIndex=1:height(oneLayerMagnetTable.partIndex)
                selMagnetInner.SelectPart(oneLayerMagnetTable.partIndex(partIndex));
                CurrentStudy.SetMaterialByName(MagnetName{LayerIndex}, MagNetMaterial);
                 % CurrentMaterial=CurrentStudy.GetMaterial(MagnetName{LayerIndex})
                 CurrentStudy.GetMaterial(MagnetName{LayerIndex}).SetPattern("ParallelCircularAnyDirection");
                 CurrentStudy.GetMaterial(MagnetName{LayerIndex}).SetValue(ValueName, value);
                 CurrentStudy.GetMaterial(MagnetName{LayerIndex}).SetValue("UseMirrorCopy", 1)
                 CurrentStudy.GetMaterial(MagnetName{LayerIndex}).SetValue("StartAngle", onePoleCenterAngle);
                 % CurrentStudy.GetMaterial(MagnetName{LayerIndex}).SetEdgeOrientation(0)
                 CurrentStudy.GetMaterial(MagnetName{LayerIndex}).SetDirectionFromReferenceTarget(OuterMagnetMagEdge);
            end
      end
      selMagnetInner.Clear
% end
end