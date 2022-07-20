pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
modelspath = join_paths(pkgdatadir, 'nile/models')

nile_sources = [
    '__init__.py',
    'hash_pairs.py',
    'manifest.py',
    'patch_manifest.py',
    'patcher.py'
]


install_data(nile_sources, install_dir: modelspath)
