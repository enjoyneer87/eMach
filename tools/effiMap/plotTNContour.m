function plotTNContour(matData1,fieldName,matData2)
if nargin>1
    plotAnyContourByNameinMotorcad(matData1,fieldName,1);
elseif nargin>2
    plotDifferenceBetweenTwoMCADElec(matData1, matData2, fieldName, errorType, addText);
end

end

