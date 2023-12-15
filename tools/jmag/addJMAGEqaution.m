function addJMAGEqaution(EqName,Expression,studyObj)

studyObj.GetDesignTable().AddEquation(EqName)                              ; 
studyObj.GetDesignTable().GetEquation(EqName).SetType(1)                   ; 
studyObj.GetDesignTable().GetEquation(EqName).SetExpression(Expression)    ;             
studyObj.GetDesignTable().GetEquation(EqName).SetDescription("")           ;         
studyObj.GetDesignTable().GetEquation(EqName).SetModeling(false)           ;         
studyObj.GetDesignTable().GetEquation(EqName).SetTrueValue("")             ;     
studyObj.GetDesignTable().GetEquation(EqName).SetFalseValue("")            ;     
studyObj.GetDesignTable().GetEquation(EqName).SetDisplayName("")           ;         

end