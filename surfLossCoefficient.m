function surfLossCoefficient(phaseVec,currentVec,obj)
   for ii = 1:length(obj.CoeffName)
        figure
%         [X,Y] = meshgrid(1:size(obj.(fieldList{ii}),2), 1:size(obj.(fieldList{ii}),1));
        coeffIndex=obj.CoeffName{ii}
        objStruct=obj.CoeffValue
        

        CoeffiValue=getfield(objStruct,coeffIndex)
        surf(phaseVec,currentVec,CoeffiValue)
        
        if contains(obj.CoeffName{ii}, 'Eddy_Coefficient')
        zlabel(strcat('Eddy Coeffi',obj.CoeffUnit{ii}))
        elseif contains(obj.CoeffName{ii}, 'Hysteresis_Coefficient')
        zlabel(strcat('Hys Coeffi',obj.CoeffUnit{ii}))
        end
        title(strrep(coeffIndex,'_',''));
        
    end
end