function addJMAGEqaution(EqName,Expression,studyObj)
% EqName="Housing_height"
% studyObj=Steady2
% Expression=[num2str(Housing_outer_radius),'*scaleFactor']
EqObj=studyObj.GetDesignTable().GetEquation(EqName);
if ~EqObj.IsValid
studyObj.GetDesignTable().AddEquation(EqName)                              ; 
end
studyObj.GetDesignTable().GetEquation(EqName).SetType(1)                   ; 
studyObj.GetDesignTable().GetEquation(EqName).SetExpression(Expression)    ;             
studyObj.GetDesignTable().GetEquation(EqName).SetDescription("")           ;         
studyObj.GetDesignTable().GetEquation(EqName).SetModeling(false)           ;         
studyObj.GetDesignTable().GetEquation(EqName).SetTrueValue("")             ;     
studyObj.GetDesignTable().GetEquation(EqName).SetFalseValue("")            ;     
studyObj.GetDesignTable().GetEquation(EqName).SetDisplayName("")           ;         

end