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
    user => "steam",
  } -> exec { "tar xJf save.tar.xz":
    cwd => "/home/steam/",
    creates => "/home/steam/.klei",
    user => "steam",
    before => Class['steamcmd::dontstarve'],
  }

  package { "tmux":
    ensure => present,
  }
}
