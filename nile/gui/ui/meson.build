pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
uipath = join_paths(pkgdatadir, 'nile/gui/ui')


nile_sources = [
    'library.ui',
    'onboard.ui',
    'help-overlay.ui'
]


install_data(nile_sources, install_dir: uipath)