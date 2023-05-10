%Iabc((length(Iabc)-Period_step):(length(Iabc)), 1:3);
function C2=one_period_Sampling(Raw_data, rpm,Np)
% file_path='I:\99_Cloud\00_Onedrive\00_dhkang87\성균관대학교\EMLAB - 문서\23407\02_2020_한국산업기술평가관리원(KEIT)_수소트럭 [한국자동차연구원-(1세부)푸름케이디]\02_접수자료\21_시험데이터\무부하시험\20210602_1차년도_한자연\오실로 역기전력 데이터\'
% file_path='Z:\HDEV\Test_Measured_Data\EMF\get_data\오실로 역기전력 데이터\'
% file_name='C1--test_EMF_1000rrpm--00001';
% Raw_data=CSV_to_table(file_path,file_name);
% Raw_data=C2testEMF1000rrpm00000;

%%테이블 변수명 - Raw_Data 

fre=rpm/60*Np/2;
Single_elec_period_Time=1/fre;
Time_of_step=Raw_data{2,1}- Raw_data{1,1};
Period_Steps=Single_elec_period_Time/Time_of_step;
len_data=height(Raw_data);
start_steps=len_data-Period_Steps;
C2=Raw_data{int32(start_steps):int32(len_data),2};
y=C2;
return 