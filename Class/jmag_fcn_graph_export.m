function res=jmag_fcn_graph_export(selec_from_list)
global jmag_version
global ModelName
global StudyName
jv=jmag_version;

datatype=1;
if datatype==1
Nsourcename=1;
csv_name=strcat(selec_from_list,num2str(Nsourcename));
% csv_name=strrep(csv_name,' ','');
jmag = actxserver(strcat('designer.Application.',jv));
res=strcat(pwd,'\',csv_name,'.csv')
% sp=split(selec_from_list);

% typename=sp{1};
% typename1=outputdataname;
% typename='LineCurrent'
% sourcename=join(sp(2:end))
% sourcename=extractAfter(selec_from_list,typename1)

    jmag.GetModel(ModelName).GetStudy(StudyName).GetResultTable().GetData(selec_from_list).WriteTable(res,"Time");
else
    jmag.GetModel(ModelName).GetStudy(StudyName).GetResultTable().GetDataFromName(typename,sourcename).WriteTable(res,"Time");
end
end 

