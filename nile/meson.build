pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'nile')
gnome = import('gnome')

gnome.compile_resources('nile',
  'nile.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'nile.in',
  output: 'nile',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)


subdir('api')
subdir('downloading')
subdir('gui')
subdir('proto')
subdir('models')
subdir('utils')

nile_sources = [
  '__init__.py',
  'main.py',
  'constants.py'
]


install_data(nile_sources, install_dir: moduledir)
