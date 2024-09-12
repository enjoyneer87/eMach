function csvPath=mkJMAGResponseTable(app,curStudyObj,DataSetName,BoolAllCases,PartName)
%% dev
% DataSetName='Torque'
% DataSetName='Joule'
% DataSetName='[Cases] Joule Loss'
ProjectFolderPath=app.GetProjectFolderPath;
% [~,JPJTName,~]=fileparts(ProjectFolderPath);
% curStudyObj      =app.GetCurrentStudy;
parentPath='D:\KangDH\Emlab_emach\mlxperPJT\JEET\From38100';
StudyName=curStudyObj.GetName;
AllDataSet=[...
    {'Circuit Current'              },...
    {'Circuit Electric Power'       },...
    {'Circuit Voltage'              },...
    {'FEM Conductor Flux-Linkage'   },...
    {'FEM Conductor Inductance'     },...
    {'Iron Loss'                    },...
    {'Torque'                       },...
    {'Joule Loss'                   },...
    {'Hysteresis Loss'              }]';
    % {'Total Rotational Displacement'},...
    % {'FEM Conductor Resistance'     },...
    % {'Rotational Velocity'          },...

%% 
if nargin>2
    if contains(DataSetName,'Joule','IgnoreCase',true)
        DataSetName='Joule Loss';
    elseif contains(DataSetName,'current','IgnoreCase',true)
        DataSetName='Circuit Current';
    elseif contains(DataSetName,'voltage','IgnoreCase',true)
        DataSetName='Circuit Voltage';
    elseif contains(DataSetName,'flux','IgnoreCase',true)
        DataSetName='FEM Conductor Flux-Linkage';
    elseif contains(DataSetName,'torque','IgnoreCase',true)
        DataSetName='Torque';
    elseif contains(DataSetName,'iron','IgnoreCase',true)
        DataSetName='Iron Loss';
    end
else 
    for DataSetIndex=1:len(AllDataSet)
    DataSetName{DataSetIndex}=['[Cases] ',AllDataSet{DataSetIndex}]';
    end
end

if nargin<6
   PartName= "Total";
   DataSetName=['[Cases] ',DataSetName];
end

if nargin<5&&nargin>2
    BoolAllCases=1;
    DataSetName=['[Cases] ',DataSetName];
end    
%% get PropTable
[jpropTable,StepTable]=getJMagStudyProperties(curStudyObj);
EndTime=StepTable(contains(StepTable.PropertiesName,'EndPoint'),'PropertiesValue').Variables;
StepDivision=StepTable(contains(StepTable.PropertiesName,'StepDivision'),'PropertiesValue').Variables;
Step=StepTable(contains(StepTable.PropertiesName,'Step'),'PropertiesValue').Variables;
TotalSteps=Step{:};
StepDivision=StepDivision{:};
EndTime=EndTime{:};
%% def Duration
if TotalSteps>=2*StepDivision+1
StartValue=EndTime/TotalSteps*(StepDivision+1);
else
StartValue=0;
end
%% def ResponseParameter OBj
if ~iscell(DataSetName)
        mkJMAGResponseParameter(app,curStudyObj,DataSetName,StartValue,EndTime,PartName)
else
    for DataSetIndex=1:len(DataSetName)
        mkJMAGResponseParameter(app,curStudyObj,DataSetName{DataSetIndex},StartValue,EndTime,PartName)
    end
end

[DataSetAllNames,DataManager]=getJMAGDataSetByStudy(app);

if ~iscell(DataSetName)
    BoolDataSet=contains(DataSetAllNames,DataSetName,'IgnoreCase',true);
    DataSetName=DataSetAllNames{BoolDataSet};
else
    disp('TBC');
end

DataSet=DataManager.GetDataSet(DataSetName);
if DataSet.IsValid
    DataSetCSV=replaceSpacesWithUnderscores(DataSetName);
    DataSetCSV=strrep(DataSetCSV,'[','');
    DataSetCSV=strrep(DataSetCSV,']','');
    csvPath=[parentPath,'\',StudyName,DataSetCSV,'.csv'];
    DataSet.WriteTable(csvPath);
end
%% 
end