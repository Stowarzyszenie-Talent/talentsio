{
  description = "The main component of the SIO2 project";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/release-24.05";
  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.filetracker = {
    url = "github:Stowarzyszenie-Talent/filetracker";
    inputs.nixpkgs.follows = "nixpkgs";
  };
  inputs.sioworkers = {
    url = "github:Stowarzyszenie-Talent/sioworkers/io-interactive-trial";
    inputs.nixpkgs.follows = "nixpkgs";
    inputs.filetracker.follows = "filetracker";
  };
  inputs.extra-container = {
    url = "github:erikarvstedt/extra-container";
    inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, flake-utils, filetracker, sioworkers, extra-container }:
    let
      overlays = [
        sioworkers.overlays.default
        filetracker.overlays.default
      ];

      module = { pkgs, lib, config, ... }: import ./nix/module.nix {
        # Use pinned nixpkgs from our input for epic reproducibility.
        pkgs = import nixpkgs {
          inherit (pkgs) system; inherit overlays;
        };
        inherit lib config;
      };
    in
    {
      lib = import ./nix/lib { inherit (nixpkgs) lib; };
      nixosModules.default = {
        nixpkgs.overlays = overlays;

        imports = [
          filetracker.nixosModules.default
          sioworkers.nixosModules.self
          module
        ];
      };
    } // (flake-utils.lib.eachSystem [ "x86_64-linux" ] (system:
      let
        pkgs = import nixpkgs {
          inherit system overlays;
        };
      in
      {
        packages.default = pkgs.python311Packages.callPackage ./nix/package.nix { };
        packages.extra-container = extra-container.lib.buildContainers {
          inherit nixpkgs system;

          # Only set this if the `system.stateVersion` of your container
          # host is < 22.05
          # legacyInstallDirs = true;

          config.containers.oioioi = {
            extra = {
              # Sets
              # privateNetwork = true
              # hostAddress = "${addressPrefix}.1"
              # localAddress = "${addressPrefix}.2"
              # addressPrefix = "10.221.0";
              addressPrefix = "10.250.0";
              # Enable internet access for the container
              enableWAN = true;
              # Always allow connections from hostAddress
              firewallAllowHost = true;
              # Make the container's localhost reachable via localAddress
              exposeLocalhost = true;
            };

            # sio2jail requires this capability
            additionalCapabilities = [ "CAP_PERFMON" ];

            extraFlags = [ "--system-call-filter=perf_event_open" ];

            config = { system, ... }: {
              imports = [
                self.nixosModules.default
                ./nix/container.nix
              ];
            };
          };
        };
      }));
}
