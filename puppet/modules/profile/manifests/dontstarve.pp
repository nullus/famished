# Class: profile::steamcmd
#
#
class profile::dontstarve {
  class { "steamcmd": }
  class { "steamcmd::dontstarve": }

  # Stage save data
  exec { "aws s3 cp s3://dst.aws.disasterarea.ninja/save.tar.xz .":
    cwd => "/home/steam",
    creates => "/home/steam/save.tar.xz",
  } -> exec { "tar xJf save.tar.xz":
    cwd => "/home/steam/",
    creates => "/home/steam/.klei",
    before => Class['steamcmd::dontstarve'],
  }

  package { "tmux":
    ensure => present,
  }
}
