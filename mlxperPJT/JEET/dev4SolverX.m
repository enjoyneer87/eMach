% motorcad
% 5 geometry
% 48*5
% ref dev4Thesis

refFilePath="E:\KDH\SolverX\e10SingleFEA.mot";
refDir=dir(refFilePath)
DOEDir=fullfile(refDir.folder,'DOE')
if ~exist(DOEDir,"dir")
    mkdir(DOEDir)
end
addpath(DOEDir)


mcad=callMCAD


%%
%[text] ## get MachineData
Obj_SLLAWLabList_8p48sVV                               =MCADBuildList(refFilePath);
getLabBuildDateFromMotFile(refFilePath)

MotFileList = findMOTFiles(refDir.folder)';
scaleList2Build = repmat(struct('MotFilePath', [], 'SatDate', [], 'BuildingData', [], 'refTable', []), numel(MotFileList), 1);
[Data2Scaling4Building, filteredLabTable4Scaling]=getMCADData4ScalingFromMotFile(refFilePath)

% filteredTable           =getMCADLabDataFromMotFile(refFilePath);

%%


MachineData=defMCADMachineData4Scaling(mcad)
[~,RMSCurrent]=mcad.GetVariable('RMSCurrent');
[~,MCADPhaseAdvance]=mcad.GetVariable('PhaseAdvance');
FreqE=rpm2freqE(rpm,MachineData.Pole_Number/2)


% copy File 
if ~exist(curDOEFilePath,"file")
    copyfile(refFilePath,curDOEFilePath)
end

% 병렬 해석
mpiprofile on
SLLAWmotorCADManager = MCADLabManager(8, ListTable4Scaling);


%% set geometry 

% 48 (id,iq) set
% Define motor parameters
id = 0; % Direct axis current
iq = 0; % Quadrature axis current


mcad(8) = callMCAD
mcad.loadfromfile(refFilePath)




%% set id,iq

%% set rpm

% calculation

% get fea field and extract 2 txt file




%[appendix]{"version":"1.0"}
%---
%[metadata:view]
%   data: {"layout":"inline"}
%---
