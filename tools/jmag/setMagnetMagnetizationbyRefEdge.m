function setMagnetMagnetizationbyRefEdge(NewLayerTable,app)
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
            oneLayerMagnetTable=NewLayerTable.MagnetTable{LayerIndex};
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
                CurrentStudy.SetMaterialByName(MagnetName{LayerIndex}, "BJMT_N52UH");
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
end