#---------------------------------------------------------------------
#Name: winding_aa.py
#Menu-en: 
#Type: Python
#Create: November 22, 2023 JSOL Corporation
#Comment-en: 
#---------------------------------------------------------------------
# -*- coding: utf-8 -*-
import numpy as np
import sys

from win32com import client
app=client.dynamic.Dispatch('designer.Application.231')
#sys.path.append(r"C:\\Program Files\\JMAG-Designer22.2\\")

#from jmag.designer import *

#app = designer.GetApplication()


# 텍스트 문서를 읽어서 라인별로 리스트에 저장
def winding_table(fname):
	target_word = 'Table'
	with open(fname, 'r',encoding='utf-8') as file:
	    lines = file.readlines()
	
	newlines=[]
	for i in range(len(lines)):
	    newlines.append(lines[i].strip().replace('" "','0').replace('"',''))
	                    
	# 특정 단어가 포함된 라인의 다음 행부터 4번째 행까지 묶어서 리스트로 생성
	result = []
	for i in range(len(newlines)):
	    # 특정 단어 포함 여부 체크
	    if target_word in newlines[i]:
	        # 해당 라인의 다음 행부터 4번째 행까지를 리스트로 생성
	        sub_list = []
	        for j in range(i+1, i+5):
	            # 라인의 값을 정수로 변환하고, 값이 없으면 0으로 지정
	 
	            value = newlines[j].strip().replace('"','').split(',')
	            #print(np.array(value))
	            sub_list.append(np.array(value))
	        result.append(sub_list)
	ncoil=[]
	for i in range(len(result)):
	    ncoil.append(np.squeeze(result[i]).T.astype('int'))
	return ncoil

        

def main(fname):
	#fname ='d:/aaa.csv'  #  csv 파일 
	study=app.GetCurrentStudy()
	if study.GetWinding(0).IsValid():
		study.GetWinding(0).RemoveAllCoils()
		ncoil=winding_table(fname)
		for i in range(len(ncoil)):
			study.GetWinding(0).CreateCoil('Coil_%s'%(i+1))
			coil_1=study.GetWinding(0).GetCoil(i)
			coil_1.SetPhaseIndex(i)
			coil_1.SetSerialGroupIndex(0)
			coil_1.SetTable(ncoil[i])
# 
# if __name__ == "__main__":
#     if len(sys.argv) > 1:
#         fname = sys.argv[1]
#     else:
#         print("파일 이름 인자가 제공되지 않았습니다.")
#         sys.exit(1)

# fname ='Z:\01_Codes_Projects\git_fork_emach\tools\jmag\testout2.csv'  #  csv 파일 

main(fname)
