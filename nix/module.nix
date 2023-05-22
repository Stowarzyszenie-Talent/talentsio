{ pkgs, lib, config, ... }:

with (import ./lib { inherit lib; });
let
  cfg = config.services.oioioi;
  baseSettings = {
    # TODO: How do we handle updating this?
    CONFIG_VERSION = 49;
    DEBUG = false;

    SITE_NAME = "OIOIOI";
    SITE_ID = 1;
    PUBLIC_ROOT_URL = "https://${cfg.domain}";

    DISABLE_QUIZZES = false;
    PROBLEM_STATISTICS_AVAILABLE = true;

    # SERVER is managed by a more high level module below, same with DATABASES

    TIME_ZONE = config.time.timeZone;
    LANGUAGE_CODE = "en";

    COMPRESS_OFFLINE = true;

    CAPTCHA_FLITE_PATH = "${pkgs.flite}/bin/flite";
    CAPTCHA_SOX_PATH = "${pkgs.sox}/bin/sox";

    # This shouldn't be written to, if it is then we've encountered a bug.
    MEDIA_ROOT = "/var/empty";

    # Managed by systemd
    STATIC_ROOT = "/var/lib/sio2/static";
    FILETRACKER_CACHE_ROOT = "/var/cache/sio2-filetracker-cache";

    NOTIFICATIONS_SERVER_ENABLED = false;

    INSTALLED_APPS = pythonExpression ''${toPythonValue { } [
      "oioioi.participants"
      "oioioi.testrun"
      "oioioi.scoresreveal"
      "oioioi.confirmations"
      "oioioi.ctimes"
      "oioioi.suspendjudge"
      "oioioi.submitservice"
      "oioioi.timeline"
      "oioioi.statistics"
      "oioioi.notifications"
      "oioioi.globalmessage"
      "oioioi.phase"
      "oioioi.supervision"
      "oioioi.talent"
    ]} + INSTALLED_APPS'';

    MIDDLEWARE = overrideAssignment "+=" [
      "oioioi.supervision.middleware.supervision_middleware" # needed for supervision
      "oioioi.contests.middleware.CurrentContestMiddleware"
    ];

    SUBMITTABLE_LANGUAGES = pythonStatements ''
      SUBMITTABLE_LANGUAGES.pop('Java');
      SUBMITTABLE_LANGUAGES.pop('Python');
      SUBMITTABLE_EXTENSIONS.pop('Java');
      SUBMITTABLE_EXTENSIONS.pop('Python');
    '';

    SECRET_KEY = pythonStatements ''
      import uuid
      from pathlib import Path

      SECRET_KEY_PATH = Path("/var/lib/sio2/secret_key")
      if SECRET_KEY_PATH.exists():
        SECRET_KEY = SECRET_KEY_PATH.read_text().strip()
      else:
        SECRET_KEY = str(uuid.uuid4())
        SECRET_KEY_PATH.touch(0o600)
        SECRET_KEY_PATH.write_text(SECRET_KEY)
    '';

    ADMINS = [ ];
    MANAGERS = pythonExpression "ADMINS";

    EMAIL_USE_TLS = false;
    EMAIL_HOST = "localhost";
    EMAIL_PORT = 25;
    EMAIL_HOST_USER = "";
    EMAIL_HOST_PASSWORD = "";
    EMAIL_SUBJECT_PREFIX = "[OIOIOI] ";

    DEFAULT_FROM_EMAIL = "oioioi@${cfg.domain}";
    SERVER_EMAIL = pythonExpression "DEFAULT_FROM_EMAIL";

    SEND_USER_ACTIVATION_EMAIL = false;

    AVAILABLE_COMPILERS = {
      "C" = {
        "gcc10_2_1_c99" = { "display_name" = "gcc=10.2.1 std=gnu99 -O3"; };
      };
      "C++" = {
        "g++10_2_1_cpp17" = { "display_name" = "g++=10.2.1 std=c++17 -O3"; };
      };
      "Pascal" = {
        "fpc2_6_2" = { "display_name" = "fpc=2.6.2"; };
      };
      "Output-only" = {
        "output-only" = { "display_name" = "output-only"; };
      };
    };

    DEFAULT_COMPILERS = {
      "C" = "gcc10_2_1_c99";
      "C++" = "g++10_2_1_cpp17";
      "Pascal" = "fpc2_6_2";
      "Output-only" = "output-only";
    };

    USE_SINOLPACK_MAKEFILES = false;

    ALLOWED_HOSTS = [ "*" ];
  };
in
{
  options.services.oioioi = {
    enable = lib.mkEnableOption "OIOIOI, the main component of the SIO2 contesting system";

    domain = lib.mkOption {
      default = config.networking.fqdn;
      defaultText = lib.literalExpression "config.networking.fqdn";
      type = lib.types.str;
      description = lib.mkDoc ''
        Domain name of the oioioi instance.

        Used for the default value of PUBLIC_ROOT_URL in settings and for nginx vhost configuration.
      '';
    };

    nginx = lib.mkOption {
      default = null;
      description = lib.mdDoc ''
        Options for customising the oioioi nginx virtual host.
      '';
      # FIXME: Typecheck this
      type = lib.types.nullOr lib.types.attrs;
    };

    rabbitmqUrl = lib.mkOption {
      default = "amqp://oioioi:oioioi@localhost:${builtins.toString config.services.rabbitmq.port}//";
      description = "The RabbitMQ URL in amqp format SIO2 processes should connect to";
      type = lib.types.str;
    };

    filetrackerUrl = lib.mkOption {
      default = "http://127.0.0.1:${config.services.filetracker.port}/";
      description = "The Filetracker URL SIO2 processes should connect to";
      type = lib.types.str;
    };

    unpackmgr = lib.mkOption {
      default = { };
      description = "unpackmgr settings";
      type = mkOptionSubmodule {
        concurrency = lib.mkOption {
          default = 1;
          description = "unpackmgr concurrency";
          type = lib.types.ints.positive;
        };
      };
    };

    evalmgr = lib.mkOption {
      default = { };
      description = "evalmgr settings";
      type = mkOptionSubmodule {
        concurrency = lib.mkOption {
          default = 1;
          description = "evalmgr concurrency";
          type = lib.types.ints.positive;
        };
      };
    };

    extraSettings = lib.mkOption {
      default = [ ];
      description = "Extra settings written to settings.py";
      # TODO: This could be a DAG.
      type = with lib.types; let element = oneOf [ lines attrs ]; in coercedTo element (x: [ x ]) (listOf element);
    };
  };

  config =
    let
      python = pkgs.python38;
      package = python.pkgs.callPackage ./package.nix { };
      uwsgi = pkgs.uwsgi.override { plugins = [ "python3" ]; python3 = python; };
      # FIXME: This could probably be acomplished without this hackery
      celery = builtins.head (builtins.filter (x: lib.getName x == "celery") package.propagatedBuildInputs);

      writePython38 = pkgs.writers.makePythonWriter python pkgs.python38Packages /* FIXME: build packages? */ pkgs.python38Packages;
      writePython38Bin = name: writePython38 "/bin/${name}";

      finalSimpleSettings = baseSettings // (builtins.foldl' (a: b: a // b) { } (builtins.filter builtins.isAttrs cfg.extraSettings)) // {
        SERVER = "uwsgi";
        BROKER_URL = cfg.rabbitmqUrl;

        DATABASES.default = {
          ENGINE = "django.db.backends.postgresql";
          ATOMIC_REQUESTS = true;
          NAME = "sio2";
          USER = "sio2";
          PASSWORD = "";
          HOST = "";
        };
      };
      finalSettingsText = lib.concatMapStrings (x: if lib.hasSuffix "\n" x then x else x + "\n") ([
        "# Settings header\n"
        (builtins.readFile ./settings-header.py)
        "\n# Simple settings\n"
        (toPythonVars { } finalSimpleSettings)
        "\n# String values from extraSettings\n"
      ] ++ (builtins.filter builtins.isString cfg.extraSettings) ++ [
        "\n# Settings footer\n"
        (builtins.readFile ./settings-footer.py)
      ]);
      settingsDir = pkgs.runCommandLocal "settings-py-dir" { } ''
        mkdir -p $out
        ln -s ${pkgs.writeText "settings.py" finalSettingsText} $out/settings.py
      '';

      PYTHONPATH = "${settingsDir}:${python.pkgs.makePythonPath [ package ]}:/etc/sio2/";
      DJANGO_SETTINGS_MODULE = "settings";
      writePythonSio = name: script: writePython38 name { } ''
        # flake8: noqa
        import sys
        import os
        sys.path += ${toPythonValue {} (lib.splitString ":" PYTHONPATH)}
        os.environ["DJANGO_SETTINGS_MODULE"] = ${toPythonValue {} DJANGO_SETTINGS_MODULE}

        ${script}
      '';
      writePythonSioBin = name: writePythonSio "/bin/${name}";

      managePy = writePythonSioBin "sio-manage" ''
        import sys
        from django.core.management import execute_from_command_line

        execute_from_command_line(sys.argv)
      '';
      wsgiPy = writePythonSio "wsgi.py" ''
        from django.core.wsgi import get_wsgi_application
        application = get_wsgi_application()
      '';
    in
    lib.mkIf cfg.enable {
      users.extraUsers.sio2 = {
        isSystemUser = true;
        group = "sio2";
      };
      users.extraGroups.sio2 = { };

      environment.systemPackages = [ managePy ];

      services.nginx =
        if cfg.nginx != null then {
          enable = lib.mkDefault true;
          virtualHosts."oioioi" = {
            forceSSL = true;
          } // cfg.nginx // {
            serverName = cfg.domain;

            locations."/static/" = {
              alias = "/var/lib/sio2/static/";
              extraConfig = ''
                gzip on;
                gzip_vary on;
                gzip_min_length 1024;
                gzip_proxied expired no-cache no-store private auth;
                gzip_types text/plain text/css application/javascript text/javascript;
                expires 1d;
              '';
            };

            locations."/socket.io/".extraConfig = ''
              proxy_pass http://127.0.0.1:7887;
              proxy_http_version 1.1;
              proxy_set_header Upgrade $http_upgrade;
              proxy_set_header Connection "Upgrade";
            '';

            locations."/".extraConfig = ''
              uwsgi_pass unix:///var/run/sio2/uwsgi.sock;
              include ${pkgs.nginx}/conf/uwsgi_params;
              uwsgi_read_timeout 1800;
            '';

            locations."~ ^/(jsi18n/|c/[a-z0-9_-]+/(status/|admin/|p/[a-z0-9_-]+/$))".extraConfig = ''
              uwsgi_pass unix:///var/run/sio2/uwsgi.sock;
              include ${pkgs.nginx}/conf/uwsgi_params;
              uwsgi_read_timeout 1800;
            '';

            extraConfig = ''
              charset utf-8;

              client_max_body_size 1g;

              limit_req_status 429;
              keepalive_requests 1000;
              keepalive_timeout 360s 360s;
            '';
          };
        } else { };

      services.postgresql = {
        enable = true;
        ensureDatabases = [ "sio2" ];
        ensureUsers = [
          {
            name = "sio2";
            ensurePermissions = {
              "DATABASE sio2" = "ALL PRIVILEGES";
            };
          }
        ];
      };

      services.rabbitmq = {
        enable = true;
      };

      system.activationScripts.copy-sio2-etc-defaults = ''
        if [[ ! -e /etc/sio2 ]]; then
          mkdir -m=775 -p /etc/sio2
          cp --no-preserve=all ${../oioioi/deployment/basic_settings.py.template} /etc/sio2/basic_settings.py
        fi
      '';

      services.sioworkersd.enable = true;

      users.extraGroups.sio2-filetracker = { };
      services.filetracker-cache-cleaner.paths = [ "/var/cache/sio2-filetracker-cache" ];
      services.sioworker.filetrackerCache = "/var/cache/sio2-filetracker-cache";

      systemd.tmpfiles.rules = [
        "d /var/cache/sio2-filetracker-cache 2770 root sio2-filetracker - -"
        "A /var/cache/sio2-filetracker-cache - - - - u::rwx,d:g::rwx,o::---"
      ];

      systemd.services =
        let
          mkSioProcess = { name, requiresDatabase, requiresFiletracker, requiresRabbitmq ? requiresFiletracker, ... }@x:
            let extraRequires = (lib.optionals requiresDatabase [ "postgresql.service" "sio2-migrate.service" ]) ++ (lib.optional requiresFiletracker "filetracker.service") ++ (lib.optional requiresRabbitmq "sio2-rabbitmq.service");
            in
            {
              enable = true;
              description = "${name}, a part of SIO2";
              requires = (x.requires or [ ]) ++ extraRequires;
              after = (x.wants or [ ]) ++ (x.requires or [ ]) ++ (x.after or [ ]) ++ extraRequires;

              environment = {
                # This is required for services that don't go through manage.py
                inherit DJANGO_SETTINGS_MODULE;
                inherit PYTHONPATH;
                FILETRACKER_FILE_MODE = "770";
              } // (x.environment or { });

              serviceConfig = {
                Type = "simple";

                ReadWritePaths = (lib.optional requiresFiletracker "/var/cache/sio2-filetracker-cache") ++ (x.ReadWritePaths or [ ]);
                SupplementaryGroups = (lib.optional requiresFiletracker "sio2-filetracker") ++ (x.SupplementaryGroups or [ ]);

                User = "sio2";
                Group = "sio2";
              } // {
                PrivateTmp = true;
                ProtectSystem = "strict";
                RemoveIPC = true;
                NoNewPrivileges = true;
                RestrictSUIDSGID = true;
                ProtectKernelTunables = true;
                ProtectControlGroups = true;
                ProtectKernelModules = true;
                ProtectKernelLogs = true;
                PrivateDevices = true;
              } // (builtins.removeAttrs (x.serviceConfig or { }) [ "ReadWritePaths" "SupplementaryGroups" ]);
            } // (builtins.removeAttrs x [ "name" "requiresDatabase" "requiresFiletracker" "requiresRabbitmq" "requires" "after" "serviceConfig" "environment" ]);
        in
        {
          # The sioworker service has to be modified this way so it has access to the shared filetracker cache.
          sioworker = {
            serviceConfig = {
              ReadWritePaths = [ "/var/cache/sio2-filetracker-cache" ];
              SupplementaryGroups = [ "sio2-filetracker" ];
            };
            # This is required so that filetracker creates files with the 770 mode instead of 700 and the sio2-filetracker group has access to the files, this is also replicated in other sio2 services.
            environment.FILETRACKER_FILE_MODE = "770";
          };

          sio2-migrate = {
            enable = true;
            description = "SIO2 database migrator";
            after = [ "postgresql.service" ];
            requires = [ "postgresql.service" ];

            script =
              let
                hash = collectUniqueString [
                  (builtins.toString package)
                  (collectUniqueString finalSimpleSettings.DATABASES)
                ];
              in
              ''
                hashfile=/var/lib/sio2/last-migrate-hash
                if [[ ! -e "$hashfile" || $(cat "$hashfile") != "$hash" ]]; then
                  ${managePy}/bin/sio-manage migrate
                  echo -n "${hash}" >"$hashfile"
                fi
              '';

            serviceConfig = {
              Type = "simple";
              ReadOnlyPaths = "/";
              ReadWritePaths = [ "/tmp" ];
              StateDirectory = "sio2";
              User = "sio2";
              Group = "sio2";
            };
          };

          sio2-rabbitmq = {
            enable = true;
            description = "SIO2 rabbitmq setup";
            after = [ "rabbitmq.service" ];
            requires = [ "rabbitmq.service" ];

            path = [ pkgs.rabbitmq-server ];

            script = ''
              function rmqctl() {
                HOME=/tmp rabbitmqctl --erlang-cookie $(cat /var/lib/rabbitmq/.erlang.cookie) "$@"
              }

              if ! rmqctl list_users | grep oioioi; then
                rmqctl add_user oioioi oioioi
                rmqctl set_permissions oioioi '.*' '.*' '.*'
              fi
            '';

            serviceConfig = {
              Type = "simple";
              ReadOnlyPaths = "/";
              PrivateTmp = true;
            };
          };

          sio2-uwsgi = mkSioProcess {
            name = "uwsgi";

            requiresFiletracker = true;
            requiresDatabase = true;

            wantedBy = [ "multi-user.target" ];
            wants = [
              "rankingsd.service"
              "mailnotifyd.service"
              "unpackmgr.service"
              "evalmgr.service"
              "sioworkersd.service"
              "receive_from_workers.service"
            ];

            # These units all have to be in the same namespace due to celery requiring a shared /tmp.
            unitConfig.JoinsNamespaceOf = [ "evalmgr.service" "unpackmgr.service" "receive_from_workers.service" ];

            serviceConfig = {
              ReadWritePaths = [ "/dev/shm" ];
              ExecStartPre = [
                "${managePy}/bin/sio-manage collectstatic --no-input"
                "${managePy}/bin/sio-manage compress --force"
              ];
              ExecStart = ''
                ${uwsgi}/bin/uwsgi --plugin ${uwsgi}/lib/uwsgi/python3_plugin.so -s /var/run/sio2/uwsgi.sock --umask=000 --processes=10 -M --max-requests=5000 --disable-logging --need-app --enable-threads --socket-timeout=30 --ignore-sigpipe --ignore-write-errors --disable-write-exception --wsgi-file=${wsgiPy}
              '';

              KillSignal = "SIGINT";

              RuntimeDirectory = "sio2";
              StateDirectory = "sio2";
            };
          };


          rankingsd = mkSioProcess {
            name = "rankingsd";

            requiresFiletracker = false;
            requiresDatabase = false;

            serviceConfig = {
              ExecStart = ''
                ${managePy}/bin/sio-manage rankingsd
              '';

              StateDirectory = "sio2";
            };
          };

          mailnotifyd = mkSioProcess {
            name = "mailnotifyd";

            requiresFiletracker = false;
            requiresDatabase = false;

            serviceConfig = {
              ExecStart = ''
                ${managePy}/bin/sio-manage mailnotifyd
              '';

              StateDirectory = "sio2";
            };
          };

          unpackmgr = mkSioProcess {
            name = "unpackmgr";

            requiresFiletracker = true;
            requiresDatabase = true;

            unitConfig.JoinsNamespaceOf = [ "sio2-uwsgi.service" "evalmgr.service" "receive_from_workers.service" ];

            serviceConfig = {
              ExecStart = ''
                ${celery}/bin/celery -A oioioi.celery worker -E -l info -Q unpackmgr -c ${builtins.toString cfg.unpackmgr.concurrency}
              '';

              StateDirectory = "sio2";
            };
          };

          evalmgr = mkSioProcess {
            name = "evalmgr";

            requiresFiletracker = true;
            requiresDatabase = true;

            unitConfig.JoinsNamespaceOf = [ "sio2-uwsgi.service" "unpackmgr.service" "receive_from_workers.service" ];

            serviceConfig = {
              ExecStart = ''
                ${celery}/bin/celery -A oioioi.celery worker -E -l info -Q evalmgr -c ${builtins.toString cfg.evalmgr.concurrency}
              '';

              StateDirectory = "sio2";
            };
          };

          receive_from_workers = mkSioProcess {
            name = "receive_from_workers";

            requiresFiletracker = false;
            requiresDatabase = false;

            unitConfig.JoinsNamespaceOf = [ "sio2-uwsgi.service" "unpackmgr.service" "evalmgr.service" ];

            serviceConfig = {
              ExecStart = ''
                ${managePy}/bin/sio-manage start_receive_from_workers
              '';

              StateDirectory = "sio2";
            };
          };
        };
    };
}
