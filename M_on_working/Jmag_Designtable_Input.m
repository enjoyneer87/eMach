function Jmag_Designtable_Input(Input_)


current = sqrt(i_d(k)^2+i_q(k)^2);
phase = atan2(i_q(k),i_d(k))*180/pi+360*(i_q(k)<0)+90;
Case_Input