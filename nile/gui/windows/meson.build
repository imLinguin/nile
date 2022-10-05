pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
windowspath = join_paths(pkgdatadir, 'nile/gui/windows')



nile_sources = [
    '__init__.py',
    'main_window.py',
    'about_window.py',
    'onboard.py',
    'install_game.py',
    'filepicker.py',
    'webview.py',
    'wine_management.py'
]


install_data(nile_sources, install_dir: windowspath)