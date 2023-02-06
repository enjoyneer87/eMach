function res=jmag_fcn_graph_export(o_data_name)
global jmag_version
global ModelName
global StudyName
jv=jmag_version
jmag = actxserver(strcat('designer.Application.',jv));
res=strcat(pwd,'/',o_data_name,'.csv')
jmag.GetModel(ModelName).GetStudy(StudyName).GetResultTable().GetData(o_data_name).WriteTable(res,"Time")

end 
