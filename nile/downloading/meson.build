pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
dlpath = join_paths(pkgdatadir, 'nile/downloading')

nile_sources = [
    'manager.py',
    'worker.py'
]


install_data(nile_sources, install_dir: dlpath)
