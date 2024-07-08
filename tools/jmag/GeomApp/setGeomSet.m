function newGeomSetTable=setGeomSet(,geomApp)
PartGeomTable=setGeomSet(PartGeomTable,geomApp);

geomDocu=geomApp.GetDocument;
% NewsetRefObj = geomTable.refObj   

%% Solid
newGeomSetTable = table([], {}, 'VariableNames', {'geomSetName', 'geomSetObj'});
for PartIndex=1:height(PartGeomTable)
    if isvarofTable(PartGeomTable,'GeomSetListTable')
    GeomSetListTable = PartGeomTable.GeomSetListTable{PartIndex};
        if ~isempty(GeomSetListTable)
            for IndexSetListTable=1:height(GeomSetListTable)        
                NewsetName   = GeomSetListTable.GeomSetName{IndexSetListTable};    
                GeomSetType  = GeomSetListTable.GeomSetType{IndexSetListTable};
                TargetList   = GeomSetListTable.Target{IndexSetListTable};
                if contains(GeomSetType,'Solid')        
                    NewGeomSolidRegionSet_Obj  = geomApp.GetDocument().GetAssembly().CreateSolidRegionSet();
                    if NewGeomSolidRegionSet_Obj.IsValid        
                     %% 전체 Solid
                     SolidIdentifierName         =TargetList;
                     NewGeomSolidRegionSet_Obj.SetName(NewsetName)        
                        for Index_Identifier=1:length(SolidIdentifierName)
                            refObj      =geomDocu.CreateReferenceFromIdentifier(SolidIdentifierName{Index_Identifier});
                            NewGeomSolidRegionSet_Obj.AddPropertyByReference("Targets",refObj);
                        end         
                     %% 2 Table
                     % newGeomSetTable.geomSetName = NewsetName;
                     % newGeomSetTable.SetObj      = NewGeomSolidRegionSet_Obj;
                    end
                elseif contains(GeomSetType,'face','IgnoreCase',true)
                    disp('will be developed');
                end
             end
        end
    end
end




            %% Middle Solid

            %% Front Solid

            %% Back Solid

            MiddlePartRef
            %%
            % SolidName='TExtrudeSolid306'
            % RegionItemName='TRegionItem305'
            % % case Origin Solid
            % subIdentifierName    =
(SolidName,RegionItemName)
            % SolidIdentifierName  =mkSolidIdentifierName(SolidName,subIdentifierName)
            % geomApp.GetDocument().GetAssembly().GetGeometrySet('Solid/Region Set.10').SetProperty('Targets', SolidIdentifierName)
            % 
            % % FaceExtrudeSolid
            % FaceExtrudeSolidName  ='TFaceExtrudeSolid308'
            % FaceExtrudeSolid      =mkSolidIdentifierName(FaceExtrudeSolidName,SolidIdentifierName)
            % geomApp.GetDocument().GetAssembly().GetGeometrySet('Solid/Region Set.10').SetProperty('Targets', FaceExtrudeSolid)
            % 
            % 
            % 
        end
    
    
%% 
% % SolidRegionSet

    % geomApp.GetDocument().GetAssembly().CreateSolidRegionSet()
    % faceIdentifierName= ['faceregion(','TRegionItem79',')'];
    % 
    % geomApp.GetDocument().GetAssembly().GetGeometrySet('Solid/Region Set').SetProperty('Targets', faceIdentifierName)
    % 
    % 
%% FaceSet

    elseif contains(NewsetName,'Face')
    % 
    % 
        NewGeomSet=geomApp.GetDocument().GetAssembly().CreateFaceSet();
        if NewGeomSet.IsValid
            NewGeomSet.SetName(NewsetName)
    % 
            NewSetName   = NewGeomSet.GetName();
    %         % Table 화
            % newGeomSetTable.geomSetName = NewSetName;
            % newGeomSetTable.geomSetObj  = NewGeomSet;
            newRow = {NewSetName, NewGeomSet}; % 새 행 데이터
            newGeomSetTable = [newGeomSetTable; newRow]; % 테이블에 행 추가
    
    %      %% ref target Obj     
            % NewGeomSet.SetProperty("Targets", refarray)
    % 
    %      %%
    % 
        end
    % geomApp.GetDocument().GetSelection().Add(geomApp.GetDocument().GetAssembly().GetGeometrySet('Face Set'))
    % geomApp.GetDocument().GetSelection().Delete()
    % 
    % 
    % geomApp.GetDocument().GetAssembly().CreateFaceSet()
    % SolidIdentifierName = 'face(TExtrudeSolid130+edge(TExtrudeSolid130+edge(TRegionItem79+TSketchArc51)))'
    % geomApp.GetDocument().GetAssembly().GetGeometrySet('Face Set').SetProperty('Targets', SolidIdentifierName)
%% 
% % edge Set

    % geomApp.GetDocument().GetAssembly().CreateEdgeSet()
    % SolidIdentifierName= ['edgeregion(',TSketchLine48,')'];
    % geomApp.GetDocument().GetAssembly().GetGeometrySet('Edge Set').SetProperty('Targets', SolidIdentifierName)
    % 
%% 
% % DirectionSet

    % geomApp.GetDocument().GetAssembly().CreateDirectionSet()
    % SolidIdentifierName = ['edgeregion(',TSketchArc51,')']
    % geomApp.GetDocument().GetAssembly().GetGeometrySet('Direction Set').SetProperty('RadialDirectionTargets', SolidIdentifierName)
    % 
%% 
% % VertexRegion

    % geomApp.GetDocument().GetAssembly().CreateVertexSet()
    % SolidIdentifierName = ['vertexregion(',TSketchVertex46,')']
    % geomApp.GetDocument().GetAssembly().GetGeometrySet('Vertex Set').SetProperty('Targets', SolidIdentifierName)
    % 
%% 
% % PointSet

    % geomApp.GetDocument().GetAssembly().CreatePointSet()
    % SolidIdentifierName = ['vertexregion(',TSketchVertex47,')']
    % geomApp.GetDocument().GetAssembly().GetGeometrySet('Point Set').SetProperty('Targets', SolidIdentifierName)
    % 
    end
end

end