pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
viewspath = join_paths(pkgdatadir, 'nile/gui/views')



nile_sources = [
    '__init__.py',
    'library.py'
]


install_data(nile_sources, install_dir: viewspath)