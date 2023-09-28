function devgetMCADData4syreMotorModelDataStr
syreMotorModelDataStr()
data.('motorName'   )=
data.('i0'          )=
data.('Imax'        )=MotorCADGeo.Imaxpk                    %  : 최대 전류 (maximum current)
data.('Vdc'         )=MotorCADGeo.DCBusVoltage              %  : 직류 전압 (DC voltage)
data.('nmax'        )=MotorCADGeo.SpeedMax_MotorLAB
data.('n0'          )=
data.('T0'          )= 
data.('P0'          )=double(MotorCADGeo.Pole_Number)       %  : 폴 수 (number of poles)
data.('p'           )=double(MotorCADGeo.Pole_Number)
data.('n3phase'     )=1
data.('Rs'          )=MotorCADGeo.Resistance_MotorLAB       %  : 스테이터 저항 (stator resistance)
data.('tempCu'      )=MotorCADGeo.Twdg_MotorLAB;
data.('tempPM'      )=MotorCADGeo.Tmag_MotorLAB;
data.('Ns'          )=double(MotorCADGeo.MagTurnsConductor) / double(MotorCADGeo.ParallelPaths)%  : 턴 
data.('l'           )=MotorCADGeo.Stator_Lam_Length   %  : 축 길이 (axial length)
data.('lend'        )=                                %  : End Part 길이
data.('R'           )=MotorCADGeo.Stator_Lam_Dia  %  
data.('J'           )=0
data.('axisType'    )='PM'
data.('motorType'   )='PM'
data.('pathname'    )=
data.('Lld'         )=0
data.('Llq'         )=0
data.('nCurr'       )=1
data.('tempVectPM'  )=65
data.('targetPMtemp')=65
data.('l0'          )=motorModel.data.l %  : active Part 길이
end