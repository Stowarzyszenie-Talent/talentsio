{ pkgs, config, ... }:

{
  time.timeZone = "Europe/Warsaw";
  networking.useDHCP = false;
  networking.hostName = "oioioi";
  networking.domain = "local";

  services.filetracker = {
    enable = true;

    ensureFiles = {
      "/sandboxes/compiler-gcc.10_2_1.tar.gz" = pkgs.fetchurl {
        url = "https://downloads.sio2project.mimuw.edu.pl/sandboxes/compiler-gcc.10_2_1.tar.gz";
        hash = "sha256-+QO7/ZqLWRvFCF9KdVqrZ6ZsBB96bkRgYVUUezvAf8A=";
      };
      "/sandboxes/proot-sandbox_amd64.tar.gz" = pkgs.fetchurl {
        url = "https://downloads.sio2project.mimuw.edu.pl/sandboxes/proot-sandbox_amd64.tar.gz";
        hash = "sha256-u6CSak326pAa7amYqYuHIqFu1VppItOXjFyFZgpf39w=";
      };
      "/sandboxes/sio2jail_exec-sandbox-1.4.2.tar.gz" = pkgs.fetchurl {
        url = "https://downloads.sio2project.mimuw.edu.pl/sandboxes/sio2jail_exec-sandbox-1.4.2.tar.gz";
        hash = "sha256-B3gtNatgcl+sx2ok3uXfWDt1gnSQptWrGEZdwmOUn20=";
      };
    };

    workers = 2;
  };

  services.filetracker-cache-cleaner = {
    enable = true;
    dates = "daily";
    sizeLimit = "10G500M";
    cleaningLevel = 75;
  };

  networking.firewall.allowedTCPPorts = [ 8000 ];

  # Allow local users to access the database.
  services.postgresql.authentication = ''
    # TYPE  DATABASE    USER        CIDR-ADDRESS          METHOD
    local   all         all                               trust
  '';

  services.sioworker = {
    enable = true;
    concurrency = 6;
    memoryLimit = 2048;
  };

  services.oioioi = {
    enable = true;

    nginx = {
      forceSSL = false;
      enableACME = false;
    };
  };

  environment.systemPackages = with pkgs; [
    htop
    # For the `filetracker` CLI
    filetracker
    python3
  ];
}
