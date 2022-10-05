pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
widgetspath = join_paths(pkgdatadir, 'nile/gui/widgets')



nile_sources = [
    '__init__.py',
    'game_card.py',
    'component_entry.py'
]


install_data(nile_sources, install_dir: widgetspath)