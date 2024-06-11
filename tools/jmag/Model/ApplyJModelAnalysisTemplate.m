function ApplyJModelAnalysisTemplate()

% void Model::ApplyAnalysisTemplate  ( String &  path,  
%   StringList &  partnames,  
%   StringList &  setnames,  
%   bool  renameParts = false,  
%   bool  renameSets = false,  
%   bool  onlyAddExistedSets = false,  
%   StringList &  refnames = StringList(),  
%   bool  renameRefs = false,  
%   bool  onlyAddExistedRefs = false,  
%   StringList &  equationnames = StringList()  
%  )   

% Parameters
% path      Path of Analysis Template in Toolbox  
% partnames Name or index of the table defined with a link between parts in a template and CAD model  
% setnames  Name or index of the table defined with a link between sets in a template and CAD model  

% renameParts 
% True=1 : Rename part name to match part name of template
% False=0 : Do not rename part name to match template
 
% renameSets 
% True=1 : Rename set name to match template
% False=0 : Do not rename set name to match template
% onlyAddExistedSets 
% True=1 : only add sets existed in model
% False=0 : add empty sets if they are not existed in model

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

% partnames
% 도구 상자의 분석 템플릿을 지정하고 템플릿을 CAD 모델과 연결합니다. (세트 포함). 
% 1: Set name of a template (or group part name)
% 2: Part index of a template (or part group index)
% 3: Part type of a template (0: Part, 1: Part group)
% 4: Part name (or part group name)     of a CAD model that a template is applied
% 5: Part index (or part group index)   of a CAD model that a template is applied
% 6: Part type (0: part, 1: part group) of a CAD model that a template is applied


% setnames
% 위의 설정 이름으로 테이블을 설정할 때 다음 형식을 지정합니다.
% 1: Set name of a template
% 2: Set index of a template
% 3: Set type of a template ("part","face","edge","vertex")
% 4: Set name of a CAD model that a template is applied
% 5: Set index of a CAD model that a template is applied.
% 6: Set type of a CAD model that a template is applied ("part","face","edge","vertex")
% The following repeats the number of sets 


% equationnames 위의 방정식 이름으로 테이블을 설정할 때 다음 형식을 지정합니다.
% 
% 1: Equation name of a template
% 2: Equation index of a template
% 3: Equation name of a CAD model that a template is applied
% 4: Equation index of a CAD model that a template is applied.
% The following repeats the number of equations
