function tempCsvPath=exportJMAGProbeValueTable(app,ProbeName,ProjName)
%%dev
% ProbeType   ="MagneticFluxDensity" ;                 
% ProbeName   ='ProbeB'              ;   
    %%  Get Grph In PJT
    GraphDMObj      =app.GetDataManager();
    NumGraphs       =GraphDMObj.NumGraphs;
    if NumGraphs>0
        GrphName        =cell(1,NumGraphs);
        % GraphDMObj.NumSets
        for GraphIndex=1:NumGraphs
            GrphName{GraphIndex}=GraphDMObj.GetGraphName(GraphIndex-1);      
        end
        CurrentFilePath =mfilename("fullpath");
        CurrentFilePath='D:\KangDH\Emlab_emach\tools\jmag\Designer\Result\test.m';
        % CurrentFilePath='D:\KangDH\Emlab_emach\mlxperPJT\JEET\e10MQS_WireTemplate_38100.m';
        [MfileDir,~,~]        =fileparts(CurrentFilePath);
        for DirIndex=1:4 % Result, Designer,jmag,tools
            [MfileDir,~,~]        =fileparts(MfileDir);
        end
        MfileDir=fullfile(MfileDir,'mlxperPJT');
        if nargin>2
            MfileDir=fullfile(MfileDir,ProjName);
        end
        TargetProbeGraphList  =GrphName(contains(GrphName,ProbeName)); %% Check Wanted Graph
        % PJTName         =app.GetProjectName;
        %% Export CSV
        for ProbeGrhIndex=1:length(TargetProbeGraphList)
            gotPrbobeGrhName                =TargetProbeGraphList{ProbeGrhIndex};
            CSVFileNameByPJT                =mkCSVFileNameByPJT(app,gotPrbobeGrhName);
            portNumber=getPCRDPPortNumber;
            filePathPerPort =fullfile(MfileDir,['From',num2str(portNumber)]);
            if ~exist(filePathPerPort,"dir")
                mkdir(filePathPerPort)
            end
            MfileDirperPort=fullfile(filePathPerPort);
            tempCsvPath{ProbeGrhIndex}      =fullfile(MfileDirperPort,CSVFileNameByPJT);
            GraphDMObj.GetGraphModel(gotPrbobeGrhName).WriteAllCaseTable(tempCsvPath{ProbeGrhIndex});
        end
    end
end