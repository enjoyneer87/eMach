function [file_list,file_length]=file_list_get(path)
formatSpec='%.2f';
o_path=pwd
cd(path)
file_list_c1= dir('*C1*.dat') ; 
file_list_c2= dir('*C2*.dat') ; 
file_list_c3= dir('*C3*.dat') ; 
file_list_c4= dir('*C4*.dat') ; 

file_list.c1=file_list_c1;
file_list.c2=file_list_c2;
file_list.c3=file_list_c3;
file_list.c4=file_list_c4;
file_length=length(file_list.c1);
cd(o_path)
end