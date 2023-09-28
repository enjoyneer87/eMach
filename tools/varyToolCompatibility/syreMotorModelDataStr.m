function data=syreMotorModelDataStr()

data=struct();
data.('motorName'   )=[]
data.('i0'          )=[]  %Ratedcurrent
data.('Imax'        )=[]  %Maximumcurrent
data.('Vdc'         )=[]
data.('nmax'        )=[]
data.('n0'          )=[]
data.('T0'          )=[]
data.('P0'          )=[]
data.('p'           )=[] 
data.('n3phase'     )=[]
data.('Rs'          )=[]
data.('tempCu'      )=[]  %  Windingtemperature Build
data.('tempPM'      )=[]  %  PMtemperature Build
data.('Ns'          )=[]  % Turnsinseriesperphase
data.('l'           )=[]
data.('lend'        )=[]
data.('R'           )=[]
data.('J'           )=[]
data.('axisType'    )=[]
data.('motorType'   )=[]
data.('pathname'    )=[]
data.('Lld'         )=[]
data.('Llq'         )=[]
data.('nCurr'       )=[]   % NumCurrLevelTgammaE
data.('tempVectPM'  )=[]
data.('targetPMtemp')=[]   % TargetPMTemp
data.('l0'          )=[]

%%
% dataSet.TurnsInSeries
% dataSet.SlotConductorNumber=dataSet.TurnsInSeries/dataSet.NumOfPolePairs/(dataSet.NumOfSlots);


end






