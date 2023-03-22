import os

ignores = ['node_modules']
def walk(path):
    for fn in os.listdir(path):
        if fn in ignores:
            continue
        sub = os.path.join(path, fn)
        if os.path.isdir(sub):
            for p in walk(sub):
                yield p
        elif os.path.isfile(sub):
            yield sub

def table_should_be_aligned(fn, lines):
    in_code = False
    bar_count = 0
    line_length = 0
    for idx, line in enumerate(lines):

        if line.count('```'):
            in_code = not in_code
            continue
        if in_code:
            continue

        lineno = idx + 1
        if not line.startswith('|'):
            bar_count = 0
            continue
        if not bar_count:
            line_length = len(line)
            bar_count = line.count('|')
        else:
            assert len(line) == line_length, \
                f'Table lines should be aligned, ' \
                f'expect exact line length {fn}:{lineno}'
            assert line.count('|') == bar_count, \
                f'Vertical bar count error in {fn}:{lineno}'

def check_title_syntax(path, lines):
    in_code = False
    got_one = False
    for line in lines:
        line = line.strip(' \n')
        if line.count('```'):
            in_code = not in_code
            continue
        if in_code:
            continue
        if line.startswith('#'):
            assert got_one or line.count('#') == 1, \
                f'First title should be top level with single # in {path}'
            assert line.count('#') < 3, \
                f'Please don\'t have ### level title in {path}'
            assert not got_one or line.count('#') > 1, \
                f'Should have ONLY one title with single # in {path}'
            got_one = True
    assert got_one, \
        f'Should have a title with single # in {path}'

must_include_titles = set([
    'Description',
    'Model',
    'References',
    'License'])
allowed_titles = set([
    'Description',
    'Model',
    'Preprocessing',
    'Postprocessing',
    'Dataset',
    'References',
    'Contributors',
    'License'])
def check_title_content(path, lines):
    includes = set()
    for idx, line in enumerate(lines):
        lineno = idx + 1
        line = line.strip(' \n')
        if not line.startswith('#'):
            continue
        if line.count('#') == 1:
            # Model name
            continue
        title = line.replace('#', '').strip()
        assert title in allowed_titles, \
            f'Please don\'t use "{title}" title in markdown, {path}:{lineno}'
        if title in must_include_titles:
            includes.add(title)
    if len(includes) != len(must_include_titles):
        lack = ', '.join(t for t in must_include_titles if t not in includes)
        print(f'Please add {lack} in {path}')
        raise Exception('Lack certain title')

def should_have_one_table_in_model_chapter(path, lines):
    table_count = 0
    in_table = False
    in_chapter = False
    for idx, line in enumerate(lines):
        lineno = idx + 1
        line = line.strip(' \n')
        if line.startswith('#'):
            title = line.replace('#', '').strip()
            if title == 'Model':
                in_chapter = True
            elif in_chapter:
                break
        if not in_chapter:
            continue
        if line.startswith('|'):
            if not in_table:
                in_table = True
                table_count += 1
        else:
            in_table = False

    assert table_count == 1, \
        f'Should have ONE-AND-ONLY-ONE table in Model chapter in {path}. ' \
        f'Got {table_count}.'

def no_chapter_should_be_empty(path, lines):
    invalid = None
    for idx, line in enumerate(lines):
        lineno = idx + 1
        line = line.strip(' \n')
        if not line.startswith('#'):
            if line:
                invalid = False
            continue
        if line.count('#') == 1:
            # Model name
            continue
        assert not invalid, \
            f'Please fill in chapter in {lineno}'
        invalid = line.replace('#', '').strip()
    assert not invalid, \
        f'Please fill in chapter "{invalid}" in {path}:{lineno}'

def link_markdown(path):
    with open(path) as f:
        lines = f.readlines()

    check_title_syntax(path, lines)
    check_title_content(path, lines)
    no_chapter_should_be_empty(path, lines)
    should_have_one_table_in_model_chapter(path, lines)
    table_should_be_aligned(path, lines)

def leaf_dir_should_have_readme(path):
    has_readme = False
    has_child = False
    has_config = False
    for fn in os.listdir(path):
        sub = os.path.join(path, fn)
        if os.path.isdir(sub):
            has_child = True
            leaf_dir_should_have_readme(sub)
        elif os.path.isfile(sub) and fn.endswith('.md'):
            has_readme = True
        elif os.path.isfile(sub) and fn.endswith('config.yaml'):
            has_config = True
    assert has_child or not has_config or has_readme, \
        f'Please provide a README.md in {path}'

def all_model_should_be_in_cases_list(path):
    with open('full_cases.txt') as f:
        full = [line.strip(' \n') for line in f.readlines() if line]
        full_set = set(full)
        assert len(full) == len(full_set)
    for case in full_set:
        assert os.path.isdir(case), f'Case {case} does not exist'
    for fn in walk(path):
        if not fn.endswith('config.yaml'):
            continue
        model = os.path.dirname(fn)
        assert model in full_set, f'Please add {model} to full_cases.txt'

def config_filenames_should_be_standard(path):
    mlir_fields = ['mlir_transform', 'deploy', 'mlir_calibration']
    nntc_fields = ['fp_compile_options', 'time_only_cali', 'cali', 'bmnetu_options']
    for fn in walk(path):
        if not fn.endswith('config.yaml'):
            continue
        with open(fn) as f:
            config = yaml.load(f, yaml.Loader)
        has_mlir = any(f in config for f in mlir_fields)
        has_nntc = any(f in config for f in nntc_fields)
        assert not (has_mlir and has_nntc), \
            f'Please don\'t place both mlir and nntc in same config file, {fn}'
        if has_mlir:
            assert fn.endswith('mlir.config.yaml'), \
                f'MLIR config should be named <optionalname.>mlir.config.yaml, {fn}'
        if has_nntc:
            assert fn.endswith('nntc.config.yaml'), \
                f'NNTC config should be named <optionalname.>nntc.config.yaml, {fn}'

import yaml
import re
def target_should_be_valid_in_config(fn):
    targets = ['BM1684', 'BM1684X']
    patterns = [
        '(BM|bm)1684([^a-zA-Z]|$)',
        '(BM|bm)1684(x|X)']
    state = None
    def check_target(data):
        nonlocal state
        ok = True
        if type(data) == dict:
            for k, v in data.items():
                if k in targets:
                    assert state is None, 'Nested target field'
                    state = k
                ok = ok and check_target(v)
                if not ok:
                    print(v)
                    return ok
                if k in targets:
                    state = None
        elif type(data) == list:
            for v in data:
                ok = ok and check_target(v)
        elif type(data) == str:
            ok = ok and all(
                not re.search(patterns[i], data)
                for i, t in enumerate(targets)
                if (state is None or t != state))
        return ok
    with open(fn) as f:
        assert check_target(yaml.load(f, yaml.Loader)), f'Invalid target in {fn}'

def target_should_be_valid(path):
    for fn in walk(path):
        if not fn.endswith('config.yaml'):
            continue
        target_should_be_valid_in_config(fn)

def lint_markdowns(path):
    leaf_dir_should_have_readme(path)
    for fn in walk(path):
        if not fn.endswith('.md'):
            continue
        link_markdown(fn)

def main():
    path = os.path.dirname(os.path.realpath(__file__))
    path = os.path.abspath(os.path.join(path, '../..'))

    os.chdir(path)
    for path in ['vision', 'language']:
        config_filenames_should_be_standard(path)
        target_should_be_valid(path)
        lint_markdowns(path)
        all_model_should_be_in_cases_list(path)

if __name__ == '__main__':
    main()
