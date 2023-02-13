function obj=jmagFcnGraphExport(obj,Noutputdata)
global jmag_version
global ModelName
global StudyName
jv=jmag_version;


datatype=1;
if datatype==1
Nsourcename=1;

%Dataname & CSVname
singleDataName=obj.outputName{Noutputdata};
csv_name=strcat(singleDataName,num2str(Nsourcename));
obj.res{Noutputdata}=strcat(pwd,'\',csv_name,'.csv')

% csv_name=strrep(csv_name,' ','');
jmag = actxserver(strcat('designer.Application.',jv));
% sp=split(selec_from_list);

% typename=sp{1};
% typename1=outputdataname;
% typename='LineCurrent'
% sourcename=join(sp(2:end))
% sourcename=extractAfter(selec_from_list,typename1)

    jmag.GetModel(ModelName).GetStudy(StudyName).GetResultTable().GetData(singleDataName).WriteTable(obj.res{Noutputdata},"Time");
else
    jmag.GetModel(ModelName).GetStudy(StudyName).GetResultTable().GetDataFromName(typename,sourcename).WriteTable(obj.res{Noutputdata},"Time");
end

end 