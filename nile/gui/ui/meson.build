pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
uipath = join_paths(pkgdatadir, 'nile/gui/ui')


nile_sources = [
    'library.ui',
    'onboard.ui',
    'game_details.ui',
    'game_card.ui',
    'loading.ui',
    'about_window.ui',
    'style.css'
]


install_data(nile_sources, install_dir: uipath)