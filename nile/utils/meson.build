pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
utilspath = join_paths(pkgdatadir, 'nile/utils')

nile_sources = [
    'config.py',
    'download.py',
    'launch.py',
    'search.py',
    'uninstall.py'
]


install_data(nile_sources, install_dir: utilspath)
