%% 
% From VeriCalcHybridACLossMOdelwithSlotB  Line 170
%% 
% 
% 
% A Table B테이블로부터
% 
% Element와 Node Matching
% 
% 
%% Export 

app=callJmag
app.Show
parameter = app.GetCurrentStudy().CreateTableDefinition()
parameter.IsValid
parameter.GetResultTypeNames

% parameter.SetResultType
parameter.SetResultType('VectorPotential',0)

parameter.SetCoordinate("Global Rectangular")
% parameter.SetComponent()
parameter.SetStepsByString("541-721")
parameter.SetIsShownMinMaxInfo(false)
parameter.SetIsShownPositionInfo(true)
app.GetCurrentStudy().ExportTable(parameter, "Z:/Thesis/00_Theory_Prof/02_System/JFT047FeedbackControl/Az.csv", 0)

% [TB]2/26 B Export /



%% Import  (In Field Data CV, contain Element(B), Node(A) data)
% B & Element

% 가져오기 옵션을 설정하고 데이터 가져오기
opts = delimitedTextImportOptions("NumVariables", 185);

% 범위 및 구분 기호 지정
opts.DataLines = [3, Inf];
opts.Delimiter = ",";

% 열 이름과 유형 지정
opts.VariableNames = ["ElementID", "Step541_X", "Step542_X", "Step543_X", "Step544_X", "Step545_X", "Step546_X", "Step547_X", "Step548_X", "Step549_X", "Step550_X", "Step551_X", "Step552_X", "Step553_X", "Step554_X", "Step555_X", "Step556_X", "Step557_X", "Step558_X", "Step559_X", "Step560_X", "Step561_X", "Step562_X", "Step563_X", "Step564_X", "Step565_X", "Step566_X", "Step567_X", "Step568_X", "Step569_X", "Step570_X", "Step571_X", "Step572_X", "Step573_X", "Step574_X", "Step575_X", "Step576_X", "Step577_X", "Step578_X", "Step579_X", "Step580_X", "Step581_X", "Step582_X", "Step583_X", "Step584_X", "Step585_X", "Step586_X", "Step587_X", "Step588_X", "Step589_X", "Step590_X", "Step591_X", "Step592_X", "Step593_X", "Step594_X", "Step595_X", "Step596_X", "Step597_X", "Step598_X", "Step599_X", "Step600_X", "Step601_X", "Step602_X", "Step603_X", "Step604_X", "Step605_X", "Step606_X", "Step607_X", "Step608_X", "Step609_X", "Step610_X", "Step611_X", "Step612_X", "Step613_X", "Step614_X", "Step615_X", "Step616_X", "Step617_X", "Step618_X", "Step619_X", "Step620_X", "Step621_X", "Step622_X", "Step623_X", "Step624_X", "Step625_X", "Step626_X", "Step627_X", "Step628_X", "Step629_X", "Step630_X", "Step631_X", "Step632_X", "Step633_X", "Step634_X", "Step635_X", "Step636_X", "Step637_X", "Step638_X", "Step639_X", "Step640_X", "Step641_X", "Step642_X", "Step643_X", "Step644_X", "Step645_X", "Step646_X", "Step647_X", "Step648_X", "Step649_X", "Step650_X", "Step651_X", "Step652_X", "Step653_X", "Step654_X", "Step655_X", "Step656_X", "Step657_X", "Step658_X", "Step659_X", "Step660_X", "Step661_X", "Step662_X", "Step663_X", "Step664_X", "Step665_X", "Step666_X", "Step667_X", "Step668_X", "Step669_X", "Step670_X", "Step671_X", "Step672_X", "Step673_X", "Step674_X", "Step675_X", "Step676_X", "Step677_X", "Step678_X", "Step679_X", "Step680_X", "Step681_X", "Step682_X", "Step683_X", "Step684_X", "Step685_X", "Step686_X", "Step687_X", "Step688_X", "Step689_X", "Step690_X", "Step691_X", "Step692_X", "Step693_X", "Step694_X", "Step695_X", "Step696_X", "Step697_X", "Step698_X", "Step699_X", "Step700_X", "Step701_X", "Step702_X", "Step703_X", "Step704_X", "Step705_X", "Step706_X", "Step707_X", "Step708_X", "Step709_X", "Step710_X", "Step711_X", "Step712_X", "Step713_X", "Step714_X", "Step715_X", "Step716_X", "Step717_X", "Step718_X", "Step719_X", "Step720_X", "Step721_X", "PositionX", "PositionY", "PositionZ"];
opts.VariableTypes = ["double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double"];

% 파일 수준 속성 지정
opts.ExtraColumnsRule = "ignore";
opts.EmptyLineRule = "read";

% 데이터 가져오기
Bx2 = readtable("Z:\Thesis\00_Theory_Prof\02_System\JFT047FeedbackControl\Bx.csv", opts);

% 가져오기 옵션을 설정하고 데이터 가져오기
opts2 = delimitedTextImportOptions("NumVariables", 185);

% 범위 및 구분 기호 지정
opts2.DataLines = [3, Inf];
opts2.Delimiter = ",";

% 열 이름과 유형 지정
opts2.VariableNames = ["ElementID", "Step541_X", "Step542_X", "Step543_X", "Step544_X", "Step545_X", "Step546_X", "Step547_X", "Step548_X", "Step549_X", "Step550_X", "Step551_X", "Step552_X", "Step553_X", "Step554_X", "Step555_X", "Step556_X", "Step557_X", "Step558_X", "Step559_X", "Step560_X", "Step561_X", "Step562_X", "Step563_X", "Step564_X", "Step565_X", "Step566_X", "Step567_X", "Step568_X", "Step569_X", "Step570_X", "Step571_X", "Step572_X", "Step573_X", "Step574_X", "Step575_X", "Step576_X", "Step577_X", "Step578_X", "Step579_X", "Step580_X", "Step581_X", "Step582_X", "Step583_X", "Step584_X", "Step585_X", "Step586_X", "Step587_X", "Step588_X", "Step589_X", "Step590_X", "Step591_X", "Step592_X", "Step593_X", "Step594_X", "Step595_X", "Step596_X", "Step597_X", "Step598_X", "Step599_X", "Step600_X", "Step601_X", "Step602_X", "Step603_X", "Step604_X", "Step605_X", "Step606_X", "Step607_X", "Step608_X", "Step609_X", "Step610_X", "Step611_X", "Step612_X", "Step613_X", "Step614_X", "Step615_X", "Step616_X", "Step617_X", "Step618_X", "Step619_X", "Step620_X", "Step621_X", "Step622_X", "Step623_X", "Step624_X", "Step625_X", "Step626_X", "Step627_X", "Step628_X", "Step629_X", "Step630_X", "Step631_X", "Step632_X", "Step633_X", "Step634_X", "Step635_X", "Step636_X", "Step637_X", "Step638_X", "Step639_X", "Step640_X", "Step641_X", "Step642_X", "Step643_X", "Step644_X", "Step645_X", "Step646_X", "Step647_X", "Step648_X", "Step649_X", "Step650_X", "Step651_X", "Step652_X", "Step653_X", "Step654_X", "Step655_X", "Step656_X", "Step657_X", "Step658_X", "Step659_X", "Step660_X", "Step661_X", "Step662_X", "Step663_X", "Step664_X", "Step665_X", "Step666_X", "Step667_X", "Step668_X", "Step669_X", "Step670_X", "Step671_X", "Step672_X", "Step673_X", "Step674_X", "Step675_X", "Step676_X", "Step677_X", "Step678_X", "Step679_X", "Step680_X", "Step681_X", "Step682_X", "Step683_X", "Step684_X", "Step685_X", "Step686_X", "Step687_X", "Step688_X", "Step689_X", "Step690_X", "Step691_X", "Step692_X", "Step693_X", "Step694_X", "Step695_X", "Step696_X", "Step697_X", "Step698_X", "Step699_X", "Step700_X", "Step701_X", "Step702_X", "Step703_X", "Step704_X", "Step705_X", "Step706_X", "Step707_X", "Step708_X", "Step709_X", "Step710_X", "Step711_X", "Step712_X", "Step713_X", "Step714_X", "Step715_X", "Step716_X", "Step717_X", "Step718_X", "Step719_X", "Step720_X", "Step721_X", "PositionX", "PositionY", "PositionZ"];
opts2.VariableTypes = ["double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double"];

% 파일 수준 속성 지정
opts2.ExtraColumnsRule = "ignore";
opts2.EmptyLineRule = "read";

% 데이터 가져오기
By2 = readtable("Z:\Thesis\00_Theory_Prof\02_System\JFT047FeedbackControl\By.csv", opts2);

% 임시 변수 지우기
clear opts2

% 결과 표시
By2

% 변수(열) 이름에서 'position' 문자열이 포함된 열 찾기
idx = contains(Bx2.Properties.VariableNames, 'position','IgnoreCase',true);

Bx2 = setVarAsRowNames(Bx2, 'ElementID');
Bx2=removevars(Bx2,'ElementID')


By2 = setVarAsRowNames(By2, 'ElementID');
By2=removevars(By2,'ElementID')



% 해당하는 열만으로 구성된 새로운 테이블 생성
positionTable = Bx2(:, idx);

Bx=Bx2(:,~idx)

% 변수(열) 이름에서 'position' 문자열이 포함된 열 찾기
idx = contains(By2.Properties.VariableNames, 'position','IgnoreCase',true);

% 해당하는 열만으로 구성된 새로운 테이블 생성
% positionTable = By2(:, idx);

By=By2(:,~idx)

Babs=sqrt(Bx.^2+By.^2)

figure(2)
hold on
quiver(positionTable.PositionX,positionTable.PositionY,Bx(:,2).Variables,By(:,2).Variables)

%%Loci Plot
idx = contains(By.Properties.VariableNames, 'Element','IgnoreCase',true);
ByOnly=By(:,~idx)

idx = contains(Bx.Properties.VariableNames, 'Element','IgnoreCase',true);
BxOnly=Bx(:,~idx)

% A & Node

% 가져오기 옵션을 설정하고 데이터 가져오기
opts3 = delimitedTextImportOptions("NumVariables", 185);

% 범위 및 구분 기호 지정
opts3.DataLines = [3, Inf];
opts3.Delimiter = ",";

% 열 이름과 유형 지정
opts3.VariableNames = ["NodeID", "Step541_Z", "Step542_Z", "Step543_Z", "Step544_Z", "Step545_Z", "Step546_Z", "Step547_Z", "Step548_Z", "Step549_Z", "Step550_Z", "Step551_Z", "Step552_Z", "Step553_Z", "Step554_Z", "Step555_Z", "Step556_Z", "Step557_Z", "Step558_Z", "Step559_Z", "Step560_Z", "Step561_Z", "Step562_Z", "Step563_Z", "Step564_Z", "Step565_Z", "Step566_Z", "Step567_Z", "Step568_Z", "Step569_Z", "Step570_Z", "Step571_Z", "Step572_Z", "Step573_Z", "Step574_Z", "Step575_Z", "Step576_Z", "Step577_Z", "Step578_Z", "Step579_Z", "Step580_Z", "Step581_Z", "Step582_Z", "Step583_Z", "Step584_Z", "Step585_Z", "Step586_Z", "Step587_Z", "Step588_Z", "Step589_Z", "Step590_Z", "Step591_Z", "Step592_Z", "Step593_Z", "Step594_Z", "Step595_Z", "Step596_Z", "Step597_Z", "Step598_Z", "Step599_Z", "Step600_Z", "Step601_Z", "Step602_Z", "Step603_Z", "Step604_Z", "Step605_Z", "Step606_Z", "Step607_Z", "Step608_Z", "Step609_Z", "Step610_Z", "Step611_Z", "Step612_Z", "Step613_Z", "Step614_Z", "Step615_Z", "Step616_Z", "Step617_Z", "Step618_Z", "Step619_Z", "Step620_Z", "Step621_Z", "Step622_Z", "Step623_Z", "Step624_Z", "Step625_Z", "Step626_Z", "Step627_Z", "Step628_Z", "Step629_Z", "Step630_Z", "Step631_Z", "Step632_Z", "Step633_Z", "Step634_Z", "Step635_Z", "Step636_Z", "Step637_Z", "Step638_Z", "Step639_Z", "Step640_Z", "Step641_Z", "Step642_Z", "Step643_Z", "Step644_Z", "Step645_Z", "Step646_Z", "Step647_Z", "Step648_Z", "Step649_Z", "Step650_Z", "Step651_Z", "Step652_Z", "Step653_Z", "Step654_Z", "Step655_Z", "Step656_Z", "Step657_Z", "Step658_Z", "Step659_Z", "Step660_Z", "Step661_Z", "Step662_Z", "Step663_Z", "Step664_Z", "Step665_Z", "Step666_Z", "Step667_Z", "Step668_Z", "Step669_Z", "Step670_Z", "Step671_Z", "Step672_Z", "Step673_Z", "Step674_Z", "Step675_Z", "Step676_Z", "Step677_Z", "Step678_Z", "Step679_Z", "Step680_Z", "Step681_Z", "Step682_Z", "Step683_Z", "Step684_Z", "Step685_Z", "Step686_Z", "Step687_Z", "Step688_Z", "Step689_Z", "Step690_Z", "Step691_Z", "Step692_Z", "Step693_Z", "Step694_Z", "Step695_Z", "Step696_Z", "Step697_Z", "Step698_Z", "Step699_Z", "Step700_Z", "Step701_Z", "Step702_Z", "Step703_Z", "Step704_Z", "Step705_Z", "Step706_Z", "Step707_Z", "Step708_Z", "Step709_Z", "Step710_Z", "Step711_Z", "Step712_Z", "Step713_Z", "Step714_Z", "Step715_Z", "Step716_Z", "Step717_Z", "Step718_Z", "Step719_Z", "Step720_Z", "Step721_Z", "PositionX", "PositionY", "PositionZ"];
opts3.VariableTypes = ["double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double"];

% 파일 수준 속성 지정
opts3.ExtraColumnsRule = "ignore";
opts3.EmptyLineRule = "read";

% 데이터 가져오기
Az = readtable("Z:\Thesis\00_Theory_Prof\02_System\JFT047FeedbackControl\Az.csv", opts3);

% 임시 변수 지우기
clear opts3

% 결과 표시
Az
% 


% 변수(열) 이름에서 'position' 문자열이 포함된 열 찾기
idx = contains(Az.Properties.VariableNames, 'Position','IgnoreCase',true);

% 해당하는 열만으로 구성된 새로운 테이블 생성
NodepositionTable = Az(:, idx);
NodepositionTable.NodeID=Az.NodeID
Az=Az(:,~idx);

NodeID=Az.NodeID;
NodePosX=NodepositionTable.PositionX;
NodePosY=NodepositionTable.PositionY;
NodePosZ=NodepositionTable.PositionZ;
strCellArray = arrayfun(@(x) num2str(x), NodeID, 'UniformOutput', false);

Az.Properties.RowNames=strCellArray
Az.Properties.VariableUnits(1:end)={'Wb/m'}
Az = removevars(Az, ["NodeID"]);

%% Allocate Structed Data Format Field and Mesh data
% B By Part with Element ID

PartStruct=getJMAGDesignerPartStruct(JMAG)

%% WireStruct
idx=findMatchingIndexInStruct(PartStruct,'Name','Wire')
WireStruct=PartStruct(idx)

%% Get Wire Element and Node ID
for Index=1:length(WireStruct)
    WireIndex=WireStruct(Index).partIndex;
    [WireStruct(Index).ElementId, WireStruct(Index).NodeID]=devgetMeshData(app,WireIndex)
end

% [TC]Field Data 할당

PostionDatainRow=rows2vars(positionTable)
PostionDatainRow.Properties.RowNames={'xPosition','yPosition','zPosition'}
% %% Ex
% targetValue=8218
% 
% % 일치하는 구조체 인덱스
% matchingIndicesOfStruct=findMatchingIndexInStruct(WireStruct,'ElementId',targetValue)
% 
% % arrayfun을 이용해서 matchingIndicesOfStruct에 해당하는 배열에서 해당 열 찾기
% matchingRows = arrayfun(@(x) find(WireStruct(x).ElementId == targetValue, 1, 'first'), matchingIndicesOfStruct);


WireStruct = updatePartStructWithFieldTable(WireStruct, PostionDatainRow, 'ElementPosition')

WireStruct = updatePartStructWithFieldTable(WireStruct, BabsfftMagTable, 'BabsfftMagTable')
WireStruct = updatePartStructWithFieldTable(WireStruct, BabsTimeinRow, 'BabsTimeinRow')
WireStruct = updatePartStructWithFieldTable(WireStruct, BxfftMagTable, 'BxfftMagTable')
WireStruct = updatePartStructWithFieldTable(WireStruct, ByfftMagTable, 'ByfftMagTable')
WireStruct = updatePartStructWithFieldTable(WireStruct, BxTimeinRow, 'BxTimeinRow')
WireStruct = updatePartStructWithFieldTable(WireStruct, ByTimeinRow, 'ByTimeinRow')
% [WIP]element 위치로부터 Node 할당

nodePositions=[NodePosX NodePosY]
elementPositions=[positionTable.PositionX positionTable.PositionY]
elementIndex=positionTable.Properties.RowNames
% elementNodeIndices = findNodesFromElementPositions(nodePositions, elementPositions)
elementNodeIndices = assignNodesToElements(nodePositions, elementPositions, NodepositionTable.NodeID, positionTable.Properties.RowNames)

%% Calc