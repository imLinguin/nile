pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
guipath = join_paths(pkgdatadir, 'nile/gui')

nile_sources = [
    'main_window.py',
    'webview.py',
    'ui/main.ui',
    'ui/help-overlay.ui'
]


install_data(nile_sources, install_dir: guipath)
