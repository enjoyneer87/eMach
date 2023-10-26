function [alpha, beta] = computeMCADMagTempCoefficients(Table1,Table2)
% · α: RTC of induction (also referred to as α(Br) in the literature). Measured between the Minimum valid temperature and the Maximum valid temperature. 
% · β: RTC of coercivity (also referred to as α(HcJ) in the literature). Measured between the Minimum valid temperature and the Maximum valid temperature.  

Temp1str=Table1.Properties.Description;
Temp2str=Table2.Properties.Description;
T1=str2double(strrep(Temp1str,'Temp=',''));
T2=str2double(strrep(Temp2str,'Temp=',''));
Br1     =Table1.Bvalue(Table1.Hvalue == 0);
Hcj1    =Table1.Hvalue(Table1.Bvalue == 0);
Br2     =Table2.Bvalue(Table2.Hvalue == 0);
Hcj2    =Table2.Hvalue(Table2.Bvalue == 0);
[alpha, beta] = computeMagTempCoefficients(Br1, Hcj1, Br2, Hcj2, T1, T2);

 

end