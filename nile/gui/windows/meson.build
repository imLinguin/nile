pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
windowspath = join_paths(pkgdatadir, 'nile/gui/windows')



nile_sources = [
    '__init__.py',
    'main_window.py',
    'onboard.py',
    'webview.py'
]


install_data(nile_sources, install_dir: windowspath)