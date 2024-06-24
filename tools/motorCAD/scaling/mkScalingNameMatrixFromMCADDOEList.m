function SCMatrixName= mkScalingNameMatrixFromMCADDOEList(ListTable2Build)


num_designs=height(ListTable2Build);
for i = 1:num_designs
    for j = 1:num_designs
        if i ~= j

            [~,refModelMotFileName,~]=fileparts(ListTable2Build.MotFilePath(i));
            [~,scaledDesign,~]=fileparts(ListTable2Build.MotFilePath(j));

            DesignNumber=extractAfter(refModelMotFileName,'Design');
            DesignNumber=DesignNumber{:};

            DesignNumber2=extractAfter(scaledDesign,'Design');
            DesignNumber2=DesignNumber2{:};
            SCMatrixName{i, j} = [DesignNumber2,'by',DesignNumber ] ;
        end
    end
end

end