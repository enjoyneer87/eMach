function StudyTable=devgetJMAGStudyListTable(Model)

% StudyObj   - 
% StudyName  - Cell
% propertiesTableWithValue
% Part

    % Cases
        % Material 
        % Condition
        % Circuit
        
NumStudies=Model.NumStudies;
StudyTable=table();
for StudyIndex=1:NumStudies
StudyTable.StudyObj(StudyIndex)                  = Model.GetStudy(StudyIndex-1);
StudyTable.StudyName(StudyIndex)                 = {StudyTable.StudyObj(StudyIndex).GetName};
[tempPropTable,tempStepTable] =getJMagStudyProperties(StudyTable.StudyObj(StudyIndex));
 
StudyTable.propertiesTable(StudyIndex)={tempPropTable};
StudyTable.StepTable(StudyIndex)      ={tempStepTable};
end

end