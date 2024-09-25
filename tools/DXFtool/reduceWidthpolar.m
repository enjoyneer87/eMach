function [reducedMinTheta,reducedMaxTheta]=reduceWidthpolar(minTheta,maxTheta,ScaleFactor)
        centerTheta = (maxTheta - minTheta) / 2 + minTheta;  % 각도의 중앙값       
        % 각도 범위를 1.001배만큼 줄이기
        reducedMinTheta = centerTheta - (centerTheta - minTheta) / ScaleFactor;
        reducedMaxTheta = centerTheta + (maxTheta - centerTheta) /ScaleFactor;

end