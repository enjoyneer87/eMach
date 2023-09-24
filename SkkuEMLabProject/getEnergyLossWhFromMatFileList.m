function DOE = getEnergyLossWhFromMatFileList(DutyCycleMatFileList, DOE)

for j=1:length(DutyCycleMatFileList)   
    str = DutyCycleMatFileList{j};
            newstartIndex = strfind(str, 'Design') + length('Design');
            if ~isempty(newstartIndex)             
                newstartIndex=newstartIndex(end);
%                 newEndIndex = strfind(str, 'Scaled\Lab') - 1;
                newEndIndex = strfind(str, '\Lab\MotorLAB') - 1;

                newnumberStr = str(newstartIndex:newEndIndex);
                caseNumberFromDriveMatlist = str2double(newnumberStr);
            end
            if ~isnan(caseNumberFromDriveMatlist)
                 structName = ['Design', num2str(caseNumberFromDriveMatlist)];

%             if  caseNumberFromDriveMatlist==number
               driveData=calcDutyCycleLossFromMatFile(DutyCycleMatFileList{j});
               DOE.(structName).SumofTotalLoss=driveData;
            else
            disp(['Invalid number in string: ', str]);
            end
end

end