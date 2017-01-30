# Class: steamcmd::dontstarve
#
#
class steamcmd::dontstarve {
  exec { "/home/steam/steamcmd.sh +login anonymous +app_update 343050 validate +quit":
    creates => "/home/steam/Steam/steamapps/common/Don't Starve Together Dedicated Server/bin/dontstarve_dedicated_server_nullrenderer",
    timeout => 1800,
    user => "steam",
    cwd => "/home/steam",
    environment => [
      "HOME=/home/steam",
      "USER=steam",
    ],
    require => Class["steamcmd"],
  }

  file { "/usr/lib/libcurl-gnutls.so.4":
    ensure => link,
    target => "libcurl.so.4",
  }
}
