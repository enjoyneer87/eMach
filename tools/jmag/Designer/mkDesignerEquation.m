function mkDesignerEquation(EqName,freqDataorString,Study,equationType)
desingTabObj=Study.GetDesignTable();
if ~isempty(desingTabObj.GetEquation(EqName))
    if ~desingTabObj.GetEquation(EqName).IsValid
    Study.GetDesignTable().AddEquation(EqName)
    end
else
    Study.GetDesignTable().AddEquation(EqName)
end

if nargin<4
    equationType='value';
end
% if Value
if strcmp(equationType,'value')
Study.GetDesignTable().GetEquation(EqName).SetType(0)
elseif strcmp(equationType,'equation')
Study.GetDesignTable().GetEquation(EqName).SetType(1)
end

Study.GetDesignTable().GetEquation(EqName).SetExpression(freqDataorString)
Study.GetDesignTable().GetEquation(EqName).SetDescription("")
Study.GetDesignTable().GetEquation(EqName).SetModeling(false)
Study.GetDesignTable().GetEquation(EqName).SetTrueValue("")
Study.GetDesignTable().GetEquation(EqName).SetFalseValue("")
Study.GetDesignTable().GetEquation(EqName).SetDisplayName("")
end
% 
