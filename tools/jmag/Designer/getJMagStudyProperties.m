function [propertiesTable, StepTable]=getJMagStudyProperties(Study)

% •typeName
% gtypeNameh is the type name used for conditions and circuit components.
% 
% •propName
% “propName” is the name of the property that is used for various settings.

% •Flag
% “Flag” is an argument that is used to turn on/off the property. A flag is used to categorize patterns, such as A-1, B-2, and C-3. A flag is an integer that does not have a unit (cannot be converted to a unit).
% 
% •Double
% “Double” is the property of a real number type including decimal numbers.
% 
% 
% •String
% “String” is the property of the string type.
% 
% 
% •Table
% “Table” is the property of the point sequence type.
% 
% 
% •TableList
% “TableList” is the point sequence of the multidimensional type.
% 
% 
% •Vector
% “Vector” is the property of the Point type.



StudyPropertiesObj =Study.GetStudyProperties();
propertiesTable=defJMAG2DStudyPropertiesTable(StudyPropertiesObj);
propertiesTable=getJMagStudyPropertiesTableValue(propertiesTable,StudyPropertiesObj);

StepObj= Study.GetStep;
StepTable=defJMAG2DStudyPropertiesTable(StepObj);
StepTable=getJMagStudyPropertiesTableValue(StepTable,StepObj);



end