function exportFilePath=exportJMAGResultTable(JMAG,Simulation,caseNumber,selectObj,Num_condition_slice,ResultType)
            if ResultType==0
                ResultType="MagneticFluxDensity";
                export_data_name='BField';
                path=fullfile(pwd,'fluxData');
            elseif ResultType=="force"
                ResultType='Nodalforce';
                export_data_name='Nodalforce';
            end

            JStudy=JMAG.GetModel(Simulation.ModelName).GetStudy(Simulation.StudyName);
            parameter = JStudy.CreateTableDefinition();
            %  안되면 파이썬 코드로 아래 변경 하기 
            if Num_condition_slice ==0
                parameter.SetResultType(ResultType ,"<Slice 1>");
                parameter.SetCoordinate("Global Rectangular")
                parameter.SetComponent(selectObj)
                parameter.SetAllSteps()
                parameter.SetIsShownMinMaxInfo(false)
                parameter.SetIsShownPositionInfo(true)
                
                exportFilePath=strcat(path,"\",export_data_name,num2str(caseNumber),".csv");
                JStudy.ExportTable(parameter, exportFilePath, 0);
            else
%                 parameter.SetResultType("MagneticFluxDensity", " <Slice 1>");
%                 parameter.SetCoordinate("Global Rectangular");            
%                 export_data_name='B_Field_skew1';
%                 parameter.SetComponent(Component);
%                 parameter.SetAllSteps();
%                 parameter.SetIsShownMinMaxInfo(true);
%                 parameter.SetIsShownPositionInfo(true);
%             
%                 path=fullfile(pwd,'fluxDataSkew');
%                 exportFilePath=strcat(path,"\",export_data_name,".csv");
%                 exportFilePath
%                 jApp.GetCurrentStudy().ExportTable(parameter, exportFilePath, 0);
            end
end