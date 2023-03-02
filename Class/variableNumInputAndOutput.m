function varargout = variableNumInputAndOutput(varargin)
    disp(['Number of provided inputs: ' num2str(length(varargin))])
    disp(['Number of requested outputs: ' num2str(nargout)])
    
    for k = 1:nargout
        varargout{k} = k;
    end
end

