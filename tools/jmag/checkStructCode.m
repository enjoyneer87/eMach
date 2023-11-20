
% getVertexTable
    % getPositionTableFromPostionObj
        % getPositionStructFromPostionObj
    % getRefVertexTableFromItemObj
        % mkRefObjTableFromItemObj


% devDesignerPartDataTable
% getJMAGDesignerPartStruct
 %% getDesignerVertexTable
    
    % a.Value
    % a.Getx
    % a.x
% 
% curSel=appView.GetCurrentSelection
% curSel.IsValid
% curSel.EdgeID(0)
% curSel.



% getEdgeVertexIdwithXYZCheck

    % PartStruct(validSortedIndices).Name이 "Rotor"인 경우에 이름 변경

    %% 
    % 2layer 중앙센터포스트와 바타입자석 지원x 워스트케이스 - 모따기해서 자석은 사각이 아닌데 중앙 센터포스트는 사각.
        % - 중앙센터포스트면 한개임
            %  사각 Center Post 와 Bar 타입 자석이 투레이어이면?
                % -> 이건안되지 다만 자석이 Center Post보다 많겠지 그래도 이건 안될듯

    % 크기가 같은게 2개이상 체크 what if  bar Type or Spoke or SPMSM
            % core나 Band,Shaft 는 두개이상인거 잘없음,      
            % 크기가 같은게 두개이상이고 사각형이면 자석임
            % 크기가 두개이상이지만 사각형이 아니면? 모따기와 Barrier 구분...
                 % 가장 바깥쪽이면 Barrier 아니면 자석

    % [TC] 중앙에서의 가상선과의 각도 체크는 bar도 만족 (대칭조건), Spoke도 대칭조건, SPMSM도 대칭임      
                %  Center Post는 중앙에 배치되는데 같은 사이즈가 잘없음 있을수도 있긴하겠다
            %  Spoke 타입은 중앙에 배치됨 
            %  SPMSM도 중앙에 배치되야됨 
    % CenterPost와  자석구분 ???
    % 사각형인 Spoke나 Bar타입이면 개수가 한개임, 그리고 중앙임 - CenterPost 와 구분안됨

    % [TB] Vertex 가 네개인거 체크할필요 모따기한거는?
     