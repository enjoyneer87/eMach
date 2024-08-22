function lastwriteDate=getLastWriteDateList(MessageLogsList)
    for MsgLogIndex=1:length(MessageLogsList)
    filePath=    MessageLogsList{MsgLogIndex};
    lastwriteDate(MsgLogIndex).LastDate=getFileLastWriteDate(filePath);
    end
end