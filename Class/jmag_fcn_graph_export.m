function res=jmag_fcn_graph_export(o_data_name,i,csv_name)
global jmag_version
global ModelName
global StudyName
jv=jmag_version;

csv_name=strcat(csv_name,num2str(i));
jmag = actxserver(strcat('designer.Application.',jv));
res=strcat(pwd,'\',csv_name,'.csv')
sp=split(o_data_name);
typename=sp{1}
% sourcename=join(sp(2:end))
sourcename=extractAfter(o_data_name,typename)

datatype=0;

if datatype==1
    jmag.GetModel(ModelName).GetStudy(StudyName).GetResultTable().GetData(o_data_name).WriteTable(res,"Time")
else
    jmag.GetModel(ModelName).GetStudy(StudyName).GetResultTable().GetDataFromName(typename,sourcename).WriteTable(res,"Time")
end
end 

