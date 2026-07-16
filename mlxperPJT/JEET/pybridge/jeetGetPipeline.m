function pl = jeetGetPipeline(reset)
%JEETGETPIPELINE  Returns the session-persistent AcLossPipeline handle.
%
%   pl = jeetGetPipeline()       reuse (or create) the cached pipeline
%   pl = jeetGetPipeline(true)   force a fresh pipeline (reload datasets)
%
%   The returned object is a py.jeet_acloss_rbf.pipeline.AcLossPipeline;
%   pass it to the other jeet* helpers.

persistent cached
if nargin >= 1 && reset
    cached = [];
end
if isempty(cached)
    mod = py.importlib.import_module('jeet_acloss_rbf');
    py.importlib.reload(mod);           % pick up on-disk edits
    cached = py.jeet_acloss_rbf.AcLossPipeline();
end
pl = cached;
end
