function ApplyJMAGAnalysisTemplate(TemplateName,app)
%%dev
% jtmpl

fullpath='Z:\01_Codes_Projects\git_fork_emach\tools\jmag\Template\';
%% path or name
    fileExtension='.jtmpl';
if ~contains(TemplateName,fileExtension)
    %% 경로와 파일명을 분리
    fullpath = mfilename("fullpath");
    [currentFolder, MfileName, b] = fileparts(fullpath);
    %% TemplatePath
    TemplateName='IPMSM_HairPinWireSinCond';
    TemplateDir=currentFolder;
    TemplatePath= fullfile(TemplateDir,[TemplateName,fileExtension]);
else
    TemplatePath=TemplateName;
end
%%
% void Model::ApplyAnalysisTemplate  ( String &  path,  
%   StringList &  partnames,                > partnames
%   StringList &  setnames,                 > setnames
%   bool  renameParts = false,              > renameParts       =false
%   bool  renameSets = false,               > renameSets        =false
%   bool  onlyAddExistedSets = false,       > onlyAddExistedSets=false
%   StringList &  refnames = StringList(),  > refnames
%   bool  renameRefs = false,               > renameRefs        =false
%   bool  onlyAddExistedRefs = false,       > onlyAddExistedRefs=false
%   StringList &  equationnames = StringList()  >equationnames
%  ) 

%%
% Parameters
% path Path of Analysis Template in Toolbox  
% partnames Name or index of the table defined with a link between parts in a template and CAD model  
% setnames Name or index of the table defined with a link between sets in a template and CAD model  
% renameParts 
% True=1 : Rename part name to match part name of template
% False=0 : Do not rename part name to match template
% 
% renameSets 
% True=1 : Rename set name to match template
% False=0 : Do not rename set name to match template
% 
% onlyAddExistedSets 
% True=1 : only add sets existed in model
% False=0 : add empty sets if they are not existed in model
% 
% refnames Name or index of the table defined with a link between refrence targets in a template and CAD model  
% renameRefs 
% True=1 : Rename reference target name to match template
% False=0 : Do not rename reference target name to match template
% 
% onlyAddExistedRefs 
% True=1 : only add reference targets existed in model
% False=0 : add empty reference targets if they are not existed in model
% 
% equationnames Name or index of the table defined with a link between equations in a template and CAD model 
%%
Model=app.GetCurrentModel;
% partnamesList         ={}
% setnamesList          ={}
% renameParts       =false
% renameSets        =false
% onlyAddExistedSets=false
% refnames          ={}
% renameRefs        =false
% onlyAddExistedRefs=false
% equationnames     ={}
% 
% equationnames{1} = "POLES"
% equationnames{end+1} = "0"
% equationnames{end+1}= "POLES"
% equationnames{end+1}= "0"
% equationnames{end+1}= "SLOTS"
% equationnames{end+1}= "0"
% equationnames{end+1}= "SLOTS"
% equationnames{end+1}= "0"
% equationnames{end+1}= "stack_length"
% equationnames{end+1}= "0"
% equationnames{end+1} = "stack_length"
% equationnames{end+1} = "0"
%% 
%%
%% CreateAnalysisTemplateParameter error
% TemplateObj=app.CreateAnalysisTemplateParameter()
% TemplateObj.SetFilepath(TemplatePath)
% TemplateObj.IsValid
% TemplateObj=app.GetModel(0).CreateAnalysisTemplateControl(TemplatePath)
% TemplateObj.GetSetsFromTemplate
% TemplateObj.IsValid
% app.ApplyAnalysisTemplate(TemplateObj)  % error
% app.ImportAnalysisTemplate(TemplateObj)   % error
%% ModelImport?
% Model.ImportAnalysisTemplate(TemplatePath,{});   % work
Model.ImportAnalysisTemplateAuto(TemplatePath,{},{});

%% ApplyAnalysisTemplate
% Model.ApplyAnalysisTemplate(TemplateName, partnamesList, setnamesList, renameParts, renameSets, onlyAddExistedSets, refnames, renameRefs, onlyAddExistedRefs, equationnames)


end