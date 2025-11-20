function [Babs, B, B_node] = calcFluxDensity(X, msh)
% calculate_B calculates flux density.
% 추가적으로 각 노드에서의 B값도 계산
%
% X: 자기 벡터 포텐셜 값 (curMVP)
% msh: 메쉬 구조체 (msh.p: 노드 좌표, msh.t: 삼각형 요소 연결, etc.)

if size(msh.t, 1) == 3
    % first-order elements (1차 삼각형 요소)
    A = X(1:size(msh.p,2));

    Ne = size(msh.t, 2);  % 요소의 개수
    Nn = size(msh.p, 2);  % 노드의 개수
    phiGrad = [-1 -1; 1 0; 0 1]';  % 참조 형태 함수의 그라디언트

    F = mappingTerms(msh);  % 요소 맵핑
    detF = mappingDeterminant(F);  % 요소의 결정자 계산

    dPhi = @(ind_n)( mappingTimesVector(phiGrad(:,ind_n), 1, 1, F, [], detF) );

    B = zeros(2, Ne);  % 각 요소에서의 자속 밀도 벡터
    B_node = zeros(2, Nn);  % 각 노드에서의 자속 밀도 벡터
    nodeCount = zeros(1, Nn);  % 각 노드가 몇 개의 요소에 속하는지 카운트

    % 요소별로 B 계산 및 노드에 분배
    for kn = 1:3
        B = B + bsxfun(@times, dPhi(kn), transpose(A(msh.t(kn,:))));        
    end

    % 각 노드로 분배 (노드들이 속한 요소에서 B 값을 분배)
    for elem = 1:Ne
        elem_nodes = msh.t(:, elem);  % 요소에 속한 노드들
        for kn = 1:3
            B_node(:, elem_nodes(kn)) = B_node(:, elem_nodes(kn)) + B(:, elem) / 3;  % 노드에 B 값을 분배
            nodeCount(elem_nodes(kn)) = nodeCount(elem_nodes(kn)) + 1;  % 노드 카운트 증가
        end
    end

    % 노드에서의 자속 밀도를 요소의 평균값으로 계산
    B_node = B_node ./ nodeCount;  % 각 노드에서의 자속 밀도 평균화

    B = [0 1; -1 0] * B;  % B 벡터 회전
    Babs = sqrt( dotProduct(B, B) );  % 요소에서의 B 크기 계산

elseif size(msh.t, 1) == 6
    % Higher-order elements (2차 삼각형 요소)
    xref = [0 0;1 0;0 1;0.5 0;0.5 0.5;0 0.5]';
    B = cell(6, 1); Babs = zeros(6, size(msh.t, 2));
    [B{:}] = deal(zeros(2, size(msh.t, 2)));
    N = Nodal2D(Operators.curl);
    Ne = size(msh.t, 2);
    
    % 각 노드에서 B 값을 저장
    B_node = zeros(2, size(msh.p, 2));
    nodeCount = zeros(1, size(msh.p, 2));

    % 요소별로 처리
    for kp = 1:6
        for kf = 1:6
            B{kp} = B{kp} + bsxfun(@times, N.eval(kf, xref(:,kp), msh, 1:Ne), ...
                transpose(X(msh.t(kf,:))) );
        end
        Babs(kp, :) = sum(B{kp}.^2, 1).^0.5;
        
        % 각 요소에서의 B 값을 해당 노드에 분배
        for elem = 1:Ne
            elem_nodes = msh.t(kf, elem);  % 요소의 노드들
            for kn = 1:6
                B_node(:, elem_nodes(kn)) = B_node(:, elem_nodes(kn)) + B{kp}(:, elem) / 6;  % 분배
                nodeCount(elem_nodes(kn)) = nodeCount(elem_nodes(kn)) + 1;
            end
        end
    end

    % 노드에서의 자속 밀도 평균화
    B_node = B_node ./ nodeCount;
end
end