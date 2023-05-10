a = {'A', 'A', 'A', 'B'};
a_expected = {'A', 'A_1', 'A_2', 'B'};

a = addIndexToDuplicateCells(a);
assert(isequal(a, a_expected), 'Test case failed.');