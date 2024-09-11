function addJMAGEqaution(EqName,Expression,CurStudyObj)
% EqName='mu0'
% studyObj=Steady2
% Expression=[num2str(Housing_outer_radius),'*scaleFactor']
EqObj=CurStudyObj.GetDesignTable().GetEquation(EqName);
if isempty(EqObj)
    CurStudyObj.GetDesignTable().AddEquation(EqName);                          
end
EqObj=CurStudyObj.GetDesignTable().GetEquation(EqName);
EqObj.SetType(1)                   ; 
EqObj.SetExpression(Expression)    ;             
EqObj.SetDescription("")           ;         
EqObj.SetModeling(false)           ;         
EqObj.SetTrueValue("")             ;     
EqObj.SetFalseValue("")            ;     
EqObj.SetDisplayName("")           ;         

end