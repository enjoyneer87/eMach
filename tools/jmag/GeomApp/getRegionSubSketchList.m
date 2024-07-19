

% % edgeRegion 4 faceRegion
% %
% faceregion()
% %


function StatorGeomAssemTable=getRegionSubSketchList(StatorGeomAssemTable)
    AssemRegionTable  =getRegionItemTable(StatorGeomAssemTable);

    for RegionIndex=1:height(AssemRegionTable)

        faceItemName=erase(AssemRegionTable.IdentifierName{RegionIndex},'faceregion(');
        faceItemName=erase(faceItemName,')');
        for AssemTableIndex=1:height(StatorGeomAssemTable)
            if isempty(StatorGeomAssemTable.Type{AssemTableIndex}) && contains(StatorGeomAssemTable.IdentifierName{AssemTableIndex},faceItemName)
            
                %
                if contains(StatorGeomAssemTable.IdentifierName{AssemTableIndex},'RegionItem')&&~contains(StatorGeomAssemTable.IdentifierName{AssemTableIndex},'Boolean')
            
                
                refIdLine2change=(StatorGeomAssemTable.IdentifierName{AssemTableIndex});
                refIdLine2change=erase(refIdLine2change,['edgeregion(',faceItemName,'+']);
                refIdLine2change=erase(refIdLine2change,')');
            
            
                StatorGeomAssemTable.SketchList{AssemTableIndex}={refIdLine2change};
                % StatorGeomAssemTable.SketchArcList{AssemTableIndex}={refIdLine2change}
                end
            end
        end
    end
end