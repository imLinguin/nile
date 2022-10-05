pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
uipath = join_paths(pkgdatadir, 'nile/gui/ui')

gnome = import('gnome')

blueprints = custom_target('blueprints',
  input: files(
    'about_window.blp',
    'game_card.blp',
    'game_details.blp',
    'install_game.blp',
    'library.blp',
    'main.blp',
    'onboard.blp',
    'loading.blp',
    'wine_management.blp',
    'component_entry.blp'
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)


gnome.compile_resources('nile',
  'nile.gresource.xml',
  gresource_bundle: true,
  dependencies: blueprints,
  install: true,
  install_dir: pkgdatadir,
)

