load('SCLTableMapPerSpeed.mat');
load('REFTableMapPerSpeed.mat');
load('SCLFPFQTableMapPerSpeed.mat');
% CSVList=[REFTable;SCLTable;SCLFqTable]
CSVList=[REFTable;SCLTable;SCLFqTable]

CSVList=table2cell(CSVList)
close all
Kr=2
load('Rdcactive.mat')
RdcSCL=RdcREF./Kr.^2
RdcSCLM=RdcSCL;
for csvindex=1:height(REFTable)
    REFTable.dqTable{csvindex}.TotalDCLoss   =3*(REFTable.dqTable{csvindex}.Is./sqrt(2)).^2*RdcREF/1000;
    REFTable.dqTable{csvindex}.TotalOnlyLoss =REFTable.dqTable{csvindex}.TotalACLoss -REFTable.dqTable{csvindex}.TotalDCLoss;
end

for csvindex=1:height(SCLTable)
    SCLTable.dqTable{csvindex}.TotalDCLoss   =3*(SCLTable.dqTable{csvindex}.Is./sqrt(2)).^2*RdcSCL/1000;
    SCLTable.dqTable{csvindex}.TotalOnlyLoss =SCLTable.dqTable{csvindex}.TotalACLoss -SCLTable.dqTable{csvindex}.TotalDCLoss;
end

for csvindex=1:height(SCLFqTable)
    SCLFqTable.dqTable{csvindex}.TotalDCLoss   =3*(SCLFqTable.dqTable{csvindex}.Is./sqrt(2)).^2*RdcSCL/1000;
    SCLFqTable.dqTable{csvindex}.TotalOnlyLoss =SCLFqTable.dqTable{csvindex}.TotalACLoss ;
end

LossTableNames={'TotalACLoss','TotalDCLoss','TotalOnlyLoss'};

speed=REFTable.speedK;
speedList=sort(speed,'ascend');

% REFTable=SCLFqTable;

for LossIndex=1:3
    close all
    devSurfVaryLoss_v1
    %%Temporal Save 2 Fig File
    % gcf=figure(len(CSVList)+1)
    % markerObjects = findobj(gcf, 'Type', 'Axes');
    % curZlim=markerObjects.ZLim
    % markerObjects.ZLim=[curZlim(1) 30];
    % 
    % %% Export Fig
    % for figIndex=len(CSVList)+1:len(CSVList)+2
    %     if figIndex==len(CSVList)+1
    %         ModelName='REF'
    %     elseif figIndex==len(CSVList)+2
    %         ModelName='SCL';
    %     end
    %     grid on
    %     savefig(figure(figIndex),[LossTableNames{LossIndex},ModelName,'TSFEA_','FitSurfPerSpeed'])
    % end
    % 
    % 
    % for speedIndex=1:len(CSVList)/2
    %     curRPM=speedList(speedIndex);
    %     speedFigureIndex=len(CSVList)+speedIndex+2;
    %     savefig(figure(speedFigureIndex),[LossTableNames{LossIndex},'TSFEA_','FitSurf_',num2str(curRPM),'rpm'])
    % end
   
    % %% Export
    % % 렌더러를 painters로 설정 후 export_fig로 EPS 저장
    % % set(gcf, 'Renderer', 'painters');
    % % export_fig('my_plot.eps', '-depsc');
    % for figIndex=len(CSVList)+1:len(CSVList)+len(CSVList)/2
    %     speedNum=figIndex-len(CSVList);
    %     curRPM=speedList(speedNum)
    %     % legend hide
    %     % % image
    %     pdfPath=['TSFEA_ACFitSurf_',num2str(curRPM),'rpm.pdf'];
    %     exportgraphics(figure(figIndex),pdfPath,'ContentType','image')
    %     % vector
    %     objline=findall(figure(figIndex),'Type','line');
    %     obj3d=findall(figure(figIndex),'Type','Surface');
    %     for chIndex=1:len(obj3d)
    %     set(obj3d(chIndex), 'XData', [], 'YData', [],'ZData',[]);
    %     end
    %     for chIndex=1:len(objline)
    %     set(objline(chIndex), 'XData', [], 'YData', [],'ZData',[]);
    %     end
    %     legend Show
    %     setlegendBoxShape(2)
    %     pdfPath=['TSFEA_ACFitSurf_',num2str(curRPM),'rpmLenged.pdf'];
    %     exportgraphics(figure(figIndex),pdfPath,'ContentType','vector')
    % end
    % %% Per Model
    % % for figIndex=len(CSVList)+len(CSVList)/2+1:len(CSVList)+len(CSVList)/2+2
    % for figIndex=len(CSVList)+len(CSVList)/2+1:len(CSVList)+len(CSVList)/2+2
    %     speedNum=figIndex-len(CSVList)-1
    %     if speedNum>len(CSVList)/2
    %         ModelName='SCL'
    %     else
    %         ModelName='REF'
    %     end
    %     % image
    %     % legend hide
    %     PDFdName=[ModelName,'_TSFEA_TotalACFitSurfPerSpeed.pdf']
    %     exportgraphics(figure(figIndex),PDFdName,'ContentType','image')
    %     % Vector
    %     objline=findall(figure(figIndex),'Type','line');
    %     obj3d=findall(figure(figIndex),'Type','Surface');
    %     for chIndex=1:len(obj3d)
    %     set(obj3d(chIndex), 'XData', [], 'YData', [],'ZData',[]);
    %     end
    %     for chIndex=1:len(objline)
    %     set(objline(chIndex), 'XData', [], 'YData', [],'ZData',[]);
    %     end
    %     legend Show
    %     setlegendBoxShape(4)
    %     PDFlegendName=[ModelName,'_TSFEA_TotalACFitSurfPerSpeedLegend.pdf']
    %     exportgraphics(figure(figIndex),PDFlegendName,'ContentType','vector')
    % end

end