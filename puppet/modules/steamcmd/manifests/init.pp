# Class: steam
#
#
class steamcmd {
  $file = "steamcmd_linux.tar.gz"

  Exec {
    cwd => "/home/steam",
    user => "steam",
    require => User["steam"],
  }

  user { 'steam':
    comment => 'Steam &',
    home => '/home/steam',
    ensure => present,
    uid => '2001',
    managehome => true,
  }

  exec { "curl -O https://steamcdn-a.akamaihd.net/client/installer/${file}":
    creates => "/home/steam/${file}",
  } ->
  exec { "tar xzf ${file}":
    creates => "/home/steam/steamcmd.sh",
  }

  # For compatibility
  package { ["glibc.i686", "libcurl.i686"]:
    ensure => installed,
  }
}
