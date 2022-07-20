pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
protopath = join_paths(pkgdatadir, 'nile/proto')

nile_sources = [
    'sds_proto2_pb2.py'
]


install_data(nile_sources, install_dir: protopath)
