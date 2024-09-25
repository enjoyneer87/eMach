Irms             =460;
% Irms             =interpList{4,3}.REFDataSet.originDqTable.Is./sqrt(2)
% PhaseAdvance     =interpList{4,3}.REFDataSet.originDqTable.("Current Angle")
PhaseAdvance=43.3
load("Rdcactive.mat")
% [SCIdrms,SCIqrms]=pkgamma2dq(Irms,PhaseAdvance)
ScaleList    =[1,2]
juhaspeedList=0.01:2000:20000;
freqE=rpm2freqE(juhaspeedList,4)
REFdimensions=[3.7,1.6,5]
NtCoil=4


JuhaMatFileList=findMatFiles(pwd)
JuhaMatFileList=JuhaMatFileList(contains(JuhaMatFileList,'LossList'))'
LineList ={'--','-'}

for ScaleIndex=1:len(ScaleList)
    if ScaleIndex==2
    figure(1)
    linesty=LineList{2}
    DispName='SCL'
    else
    figure(1)
    linesty=LineList{1}
    DispName='REF'
    end
    dimension2Calc=REFdimensions*ScaleList(ScaleIndex)
    IrmsList             =Irms*ScaleList(ScaleIndex);
    DCLoss = 3 * RdcREF/(ScaleList(ScaleIndex).^2) * (IrmsList).^2
    [kr,varphiXi,ksi,psiXi]=calcHybridJouleLossJuHa(dimension2Calc,NtCoil,freqE)
    bc = mm2m(dimension2Calc(1)); % 폭 [m]
    hc = mm2m(dimension2Calc(2)); % 높이 [m]
    bm = mm2m(dimension2Calc(3));  % slot widht
    coeffixi=calckXi4EddyLoss(hc,bc,bm,freqE);
    % skinLoss=DCLoss*(varphiXi-1)/1000;
    % proxLoss{ScaleIndex}=DCLoss *(psiXi)*(NtCoil^2 - 0.2) / 9/1000;
    proxLoss{ScaleIndex}=DCLoss *(psiXi)*(NtCoil^2 - 1) / 3/1000;
    
    Pjoule{ScaleIndex}= DCLoss/1000*(1+(coeffixi.^4*(NtCoil^2 - 0.2)/9));
    % Pjoule = DCLoss*(varphiXi)/1000 +proxLoss{ScaleIndex};

    % plot(juhaspeedList,skinLoss,linesty,'DisplayName',[DispName,'Skin Effect'])
    hold on
    plot(juhaspeedList,Pjoule{ScaleIndex},linesty,'DisplayName',[DispName,'Joule Juha'])
    plot(juhaspeedList,proxLoss{ScaleIndex},linesty,'DisplayName',[DispName,'Prox. Effect'])
    
    
    title(DispName)
    legend
end

plot(juhaspeedList,proxLoss{2}./proxLoss{1})

plot(juhaspeedList,Pjoule{2}./Pjoule{1})