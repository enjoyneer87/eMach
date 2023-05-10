function  measuredWeights= calculateRotorWeights(measuredWeights)

% 입력된 변수로부터 값 추출
rotorAssy = measuredWeights.rotorAssy;
rotorCore = measuredWeights.rotorCore;
shaft = measuredWeights.shaft;
Bearing = measuredWeights.Bearing;

% rotorAssy값이 0인 경우 계산

if measuredWeights.rotorAssy == 0
    measuredWeights.rotorAssy = measuredWeights.rotorCore + measuredWeights.shaft + measuredWeights.Bearing;
elseif measuredWeights.rotorAssy > 0 && (measuredWeights.rotorCore == 0 || measuredWeights.shaft == 0 || measuredWeights.Bearing == 0)
    missingValueCount = 0;
    missingValueFields = {};
    if measuredWeights.rotorCore == 0
        missingValueCount = missingValueCount + 1;
        missingValueFields{missingValueCount} = 'rotorCore';
    end
    if measuredWeights.shaft == 0
        missingValueCount = missingValueCount + 1;
        missingValueFields{missingValueCount} = 'shaft';
    end
    if measuredWeights.Bearing == 0
        missingValueCount = missingValueCount + 1;
        missingValueFields{missingValueCount} = 'Bearing';
    end
    if missingValueCount > 1
        error('두 개 이상의 값이 없습니다. 값을 입력하세요.');
    else
        missingValueField = missingValueFields{1};
        measuredWeights.(missingValueField) = measuredWeights.rotorAssy - measuredWeights.rotorCore - measuredWeights.shaft - measuredWeights.Bearing;
    end
end

end
