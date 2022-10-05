pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
apipath = join_paths(pkgdatadir, 'nile/api')

nile_sources = [
    'authorization.py',
    'graphql.py',
    'library.py',
    'session.py',
    'wine.py'
]


install_data(nile_sources, install_dir: apipath)
