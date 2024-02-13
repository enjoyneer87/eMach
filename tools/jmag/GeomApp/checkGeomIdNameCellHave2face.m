function checkGeomIdNameCellHave2face()
%% Find Only Solid Id Name
    SolidIndexList=find(contains(AssemPartStruct(1).AssemPartTable.IdentifierName,'Solid'))
    % SolidIndexList
    ListIdentifierName=AssemPartStruct(1).AssemPartTable.IdentifierName(SolidIndexList)
%% Check 'Face Contains Twice
    
    AssemPartStruct(1).AssemPartTable.ManualType(:)={'None'}
    % IdentifierName      =AssemPartStruct(1).AssemPartTable.IdentifierName{10}
    for SolidIndex=1:length(ListIdentifierName)
        splitedIdNameCell   =splitGeomIdName(ListIdentifierName{SolidIndex})
        if contains(IdentifierName,'Solid')
            faceNumber          =sum(strcmp(splitedIdNameCell,'face'))
            if faceNumber==2
                AssemPartStruct(1).AssemPartTable.ManualType{SolidIndexList(SolidIndex)}='faceofOriginSolid';
            else
                AssemPartStruct(1).AssemPartTable.ManualType{SolidIndexList(SolidIndex)}='None';
            end
        end
    end
end