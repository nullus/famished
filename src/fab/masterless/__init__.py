
import os
from pipes import quote as shellquote
import yaml

from fabric.api import env, local, parallel, put, run, sudo, task

def relative_path(*path):
    '''Absolute path relative to fabfile'''

    return os.path.join(os.path.dirname(env.real_fabfile), *path)

def puppet_get_var(name):
    '''Get a puppet config variable'''

    return puppet('config', 'print', '--', name)

def puppet(command, *args):
    '''Execute puppet command locally'''

    confdir = relative_path('puppet')
    vardir = relative_path('puppet', 'var')

    command = ' '.join(
        ['puppet', shellquote(command),
         '--confdir=' + shellquote(confdir),
         '--vardir=' + shellquote(vardir)] +
        [shellquote(arg) for arg in args]
    )

    return local(command, capture=True)

class PuppetNodeFacts(yaml.YAMLObject):
    yaml_tag = u'!ruby/object:Puppet::Node::Facts'
    yaml_flow_style = False

    def __init__(self, values):
        self.values = values

@task
@parallel
def get_facts():
    '''Get facts from host'''

    output = run('facter --yaml 2>/dev/null')

    local_path = os.path.join(puppet_get_var('yamldir'), "facts", env.host + ".yaml")

    with open(local_path, 'wb') as facts:
        yaml.dump(PuppetNodeFacts(yaml.load(output)), stream=facts, explicit_start=True)

@task
@parallel
def compile_catalog():
    '''Compile catalog for host'''

    catalog_file = relative_path('catalog', shellquote(env.host + ".json"))

    with open(catalog_file, 'wb') as catalog:
        catalog.write(puppet('master', '--compile', env.host).split("\n", 1)[1])

@task
def apply_catalog():
    '''Apply catalog on host'''

    catalog_file = relative_path('catalog', env.host + ".json")

    put(local_path=catalog_file, remote_path="catalog.json")
    sudo("puppet apply --debug --catalog catalog.json", pty=True)

@task
def check(var):
    print "{0}={1}".format(var, puppet_get_var(var))

@task
def bootstrap():
    '''Build directory structure for our puppet sandbox'''

    yamldir = puppet_get_var('yamldir')

    for path in [yamldir, os.path.join(yamldir, 'facts'), relative_path('catalog')]:
        try:
            os.mkdir(path)
        except OSError as expt:
            if expt.errno != 17:
                raise

    # FIXME: find out the binary location in a slightly less shit way
    try:
        os.symlink('/Volumes/home/null/Library/Python/2.7/bin/masterless-enc', os.path.join(puppet_get_var('confdir'), 'masterless-enc'))
    except OSError as expt:
        if expt.errno != 17:
            raise

__all__ = ['bootstrap', 'compile_catalog', 'apply_catalog', 'get_facts', 'check']
