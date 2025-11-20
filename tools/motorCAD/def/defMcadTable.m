function McadTable=defMcadTable(category2Out)
    %% getStruct From MatFile
    MCADStruct=defMcadTableStruct();
    fieldList=fieldnames(MCADStruct);
    %% 
    if nargin>0
    matchingIndex=contains(fieldList,category2Out,"IgnoreCase",true);
    matchingIndices=find(matchingIndex);
        %% 2 Table
        if numel(matchingIndices)>1
            McadTable=[];
            disp('유사한 이름이 여러개입니다');
            disp({fieldList{matchingIndices}}');
            for TableIndex=1:numel(matchingIndices)
                 tempMcadTable=MCADStruct.(fieldList{matchingIndices(TableIndex)});
                 McadTable=[McadTable;tempMcadTable];
            end
        elseif isscalar(matchingIndices)
            if  isfield(MCADStruct,category2Out)
                McadTable=MCADStruct.(category2Out);
            end
        disp(['유사한 이름이 있습니다  ' ,fieldList((matchingIndex))])
        McadTable=MCADStruct.(fieldList{matchingIndex});
        else 
        disp('유사한 이름이 없습니다');
        end
    else
    disp('입력된 이름이 없어 전체 Automation Table출력합니다');
    % 동일한 열 기준으로 테이블 병합\
    tables = struct2cell(MCADStruct);
    McadTable = vertcat(tables{:});
    end
end