%Iabc((length(Iabc)-Period_step):(length(Iabc)), 1:3);
function data=fcn_One_period_Sampling(data)
% file_path='I:\99_Cloud\00_Onedrive\00_dhkang87\성균관대학교\EMLAB - 문서\23407\02_2020_한국산업기술평가관리원(KEIT)_수소트럭 [한국자동차연구원-(1세부)푸름케이디]\02_접수자료\21_시험데이터\무부하시험\20210602_1차년도_한자연\오실로 역기전력 데이터\'
% file_path='Z:\HDEV\Test_Measured_Data\EMF\get_data\오실로 역기전력 데이터\'
% file_name='C1--test_EMF_1000rrpm--00001';
% Raw_data=CSV_to_table(file_path,file_name);
% Raw_data=C2testEMF1000rrpm00000;

%%테이블 변수명 - Raw_Data 

fre=data.test_rpm/60*data.p/2;
Single_elec_period_Time=1/fre;
Time_of_1step=data.I1.time(end,1).time-data.I1.time(end-1,1).time;
Steps_of_1period=Single_elec_period_Time/Time_of_1step;

len_data=height(data.I1.time);
start_steps=len_data-(Steps_of_1period-1);
% C2=Raw_data{int32(start_steps):int32(len_data),2};
data.Iabc=table(data.I1.value.data(int32(start_steps):end),data.I2.value.data(int32(start_steps):end),data.I3.value.data(int32(start_steps):end));
INames={'Ia','Ib','Ic'}
data.Iabc.Properties.VariableNames=INames;
data.Iabc.time=data.I1.time.time(int32(start_steps):end);


% return 
end