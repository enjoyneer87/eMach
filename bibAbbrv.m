path = 'Z:\01_Codes_Projects\Thesis_skku\Thesis_SKKU\backmatter';
bib_files = dir(fullfile(path, '*.bib'));
bib_files = {bib_files.name};

for i = 1:length(bib_files)
    bib_file_name = bib_files{i};
    bib_file_path = fullfile(path, bib_file_name);
    bib_file = fopen(bib_file_path, 'r');
    bib_entries = textscan(bib_file, '%s', 'Delimiter', '@');
    bib_entries = bib_entries{1}(2:end);
    fclose(bib_file);

    unique_entries = {};
    unique_callables = {};
    for j = 1:length(bib_entries)
        entry = bib_entries{j};
        callable_start = strfind(entry, '{') + 1;
        callable_end = strfind(entry, ',') - 1;
        callable = entry(callable_start:callable_end);
        if ~ismember(callable, unique_callables)
            unique_callables{end+1} = callable;
            unique_entries{end+1} = ['@', entry];
        end
    end

    modified_entries = {};
    for j = 1:length(unique_entries)
        entry = unique_entries{j};
        % energy and power
        modified_entry = regexprep(entry, 'journal\s*=\s*{ieee transactions on energy conversion}', 'journal=IEEE_J_EC', 'ignorecase');
        modified_entry = regexprep(modified_entry, 'journal\s*=\s*{ieee transactions on power electronics}', 'journal=IEEE_J_PWRE', 'ignorecase');
        % industrial, commercial and consumer
        modified_entry = regexprep(modified_entry, 'journal\s*=\s*{ieee transactions on industry applications}', 'journal=IEEE_J_IA', 'ignorecase');
        modified_entry = regexprep(modified_entry, 'journal\s*=\s*{ieee transactions on industrial electronics}', 'journal=IEEE_J_IE', 'ignorecase');
        % autos, transportation and vehicles (non-aerospace)
        modified_entry = regexprep(modified_entry, 'journal\s*=\s*{ieee transactions on vehicular technology}', 'journal=IEEE_J_VT', 'ignorecase');
        modified_entry = regexprep(modified_entry, 'journal\s*=\s*{ieee transactions on transportation electrification}', 'journal=IEEE_J_TTE', 'ignorecase');
        modified_entry = regexprep(modified_entry, 'journal\s*=\s*{ieee transactions on intelligent transportation systems}','journal=IEEE_J_ITS', 'ignorecase');
        %
        modified_entry = regexprep(modified_entry, 'journal\s*=\s*{ieee transactions on magnetics}', 'journal=IEEE_J_MAG', 'ignorecase');
        modified_entries{end+1} = modified_entry;
    end

    bib_file = fopen(bib_file_path, 'w');
    fprintf(bib_file, '%s\n', modified_entries{:});
    fclose(bib_file);
end
