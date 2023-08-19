{ pkgs
, lib
, buildPythonPackage
, fetchPypi
, pythonAtLeast
, python

, poetry-core
, six
, libsass
, setuptools
, setuptools_scm
, vine
, billiard
, kombu
, watchdog
, supervisor

, pytz
, sqlalchemy
, django
, beautifulsoup4
, pyyaml
, python-dateutil
, django-two-factor-auth
, django-formtools
, celery
, coreapi
, django-compressor
, django-statici18n
, pygments
, django-libsass
, django-debug-toolbar
, django-extensions
, djangorestframework
, werkzeug
, pytest
, pytest-metadata
, pytest-django
#, pytest-html
, pytest-xdist
, pytest-cov
, requests
, fpdf
, unicodecsv
, dnslib
, bleach
, chardet
, django-gravatar2
, django-mptt
, mistune
, pika
, raven
, unidecode
, sentry-sdk
, filetracker
, django-simple-captcha
, phonenumbers
, pdfminer-six

, sioworkers
, psycopg2

, ...
}:

let
  fetchPypi2 =
    { pname
    , version
    , hash ? null
    , sha256 ? null
    , extension ? null
    }: fetchPypi ({
      inherit pname;
      inherit version;
      extension = if extension != null then extension else "tar.gz";
    } // (if hash != null then { inherit hash; } else { }) // (if sha256 != null then { inherit sha256; } else { }));

  simplePackage =
    { name
    , version
    , ...
    }@rest: buildPythonPackage ({
      pname = name;

      src = rest.src or (fetchPypi2 {
        inherit version;
        pname = rest.pypiName or name;
        hash = rest.hash or null;
        sha256 = rest.sha256  or null;
        extension = rest.extension or null;
      });
    } // (builtins.removeAttrs rest [
      "src"
      "name"
      "pypiName"
      "hash"
      "sha256"
      "extension"
    ]));

  overridePackage = package: { extraPropagatedBuildInputs ? [ ], propagatedBuildInputsFilter ? x: true, ... }@rest: package.overridePythonAttrs (old: {
    propagatedBuildInputs = rest.propagatedBuildInputs or (builtins.filter propagatedBuildInputsFilter (old.propagatedBuildInputs or [ ])) ++ extraPropagatedBuildInputs;

    src =
      if builtins.hasAttr "version" rest then
        fetchPypi2
          {
            pname = rest.pypiName or old.pname;
            inherit (rest) version;
            hash = rest.hash or null;
            sha256 = rest.sha256 or null;
            extension = rest.extension or old.src.extension or null;
          } else old.src;
  } // (if builtins.hasAttr "version" rest then { name = "${old.pname}-${rest.version}"; } else { })
  // (builtins.removeAttrs rest [
    "extraPropagatedBuildInputs"
    "propagatedBuildInputs"
    "propagatedBuildInputsFilter"
    "pypiName"
    "hash"
    "sha256"
    "extension"
  ]));

  o-sqlalchemy = overridePackage sqlalchemy {
    version = "1.4.48";
    hash = "sha256-tHvChwltmJoIOM6W99jpZpFKJNqHftQadTHUS1XNuN8=";
  };
  python-monkey-business = simplePackage {
    name = "python-monkey-business";
    version = "1.0.0";
    hash = "sha256-mXZSKYl2bwCyqqJOyW6suRpt57cAHRRSB5MjsHGYjg4=";

    propagatedBuildInputs = [
      six
    ];
  };
  o-vine = overridePackage vine {
    version = "1.3.0";
    hash = "sha256-Ez7m16kBbxd93q8ZHB9YQhodzG7ppCxYs0vtQOHSzYc=";

    pythonImportsCheck = [ "vine" "vine.five" ];
  };
  o-billiard = overridePackage billiard {
    version = "3.6.4.0";
    hash = "sha256-KZ3lqNoop4PVGxl9SWvvTxWV3QI6k6T1nd4Yhq6QVUc=";
  };
  amqp = simplePackage {
    name = "amqp";
    version = "2.6.1";
    hash = "sha256-cM2xBihGj/FOV+wvdRx6qeSOfjZRz9YtQxITwMTljyE=";

    checkPhase = "";
    doCheck = false;
    postPatch = ''
      rm requirements/test.txt
      sed -i "s/reqs('test.txt')/[]/" setup.py
    '';

    propagatedBuildInputs = [ o-vine ];
  };
  o-kombu = overridePackage kombu {
    version = "4.6.11";
    hash = "sha256-yhtF+qyMCxhJPQKoVxeS88QCkc8rzx9Vr+09jzqnunQ=";

    disabledTestPaths = [
      "t/unit/transport/test_SQS.py"
      "t/unit/transport/test_azureservicebus.py"
      "t/unit/transport/test_azureservicebus.py"
      "t/unit/transport/test_azureservicebus.py"
      "t/unit/transport/test_azureservicebus.py"
      "t/unit/transport/test_azureservicebus.py"
      "t/unit/transport/test_azureservicebus.py"
      "t/unit/transport/test_azureservicebus.py"
      "t/unit/transport/test_filesystem.py"
      "t/unit/transport/test_filesystem.py"
    ];

    propagatedBuildInputs = [ amqp ];
  };
  o-django-registration-redux = simplePackage {
    name = "django-registration-redux";
    version = "2.12";
    hash = "sha256-IhO76HMr5yckA09BRvAlWnvWZutaXhstjYqmM/6K+JQ=";

    doCheck = false;

    nativeCheckInputs = [
      pytest
      pytest-django
    ];
  };
  o-celery = overridePackage celery {
    version = "4.4.7";
    hash = "sha256-0iCxOo7VfHgUms+CwAZ4U1YHGESv4LJwEqSZHUQCb58=";

    patches = [ ];
    doCheck = false;
    postPatch = ''
      sed -i "s/pytz>dev/pytz/" requirements/default.txt
    '';

    disabledTestPaths = [
      "t/unit/backends/test_mongodb.py"
      "t/unit/concurrency/test_pool.py"
      "t/unit/events/test_cursesmon.py"
      "t/unit/security/test_security.py"
      "t/unit/tasks/test_tasks.py"
      "t/unit/backends/test_filesystem.py"
      "t/unit/backends/test_dynamodb.py"
      "t/unit/backends/test_cassandra.py"
    ];

    propagatedBuildInputs = [ pytz o-vine o-billiard o-kombu ];
  };
  o-dj-pagination = simplePackage {
    name = "dj-pagination";
    version = "2.5.0";
    hash = "sha256-hgMBzcee3AcSAIkhA3sjQScdOlVYa8NPrQcudMjoAMQ=";

    doCheck = false;

    propagatedBuildInputs = [ django ];
  };
  o-mistune = overridePackage mistune {
    version = "0.8.4";
    hash = "sha256-WaNCnbU8ULXGvMigf4hIywDX3IvbQxpKtBkg0gHUdW4=";
  };
  o-fontawesomefree = simplePackage rec {
    name = "fontawesomefree";
    version = "6.4.0";
    format = "wheel";

    dontStrip = true;

    src = fetchPypi {
      pname = name;
      inherit version format;
      dist = "py3";
      python = "py3";
      hash = "sha256-4S7a1xts9pk/x8aupjZ+Ex8vJHtkNfrKmbEjKbrNKyc=";
    };
  };
  o-django-nested-admin = simplePackage {
    name = "django-nested-admin";
    version = "4.0.2";
    hash = "sha256-eaXOgLgcQaD0j3ePtVajchAp30hYC/zmClli/6LvLUc=";

    doCheck = false;

    propagatedBuildInputs = [
      python-monkey-business
    ];
  };
  django-supervisor = simplePackage rec {
    name = "django-supervisor";
    version = "0.4.0";

    src = builtins.fetchTree {
      type = "github";
      owner = "sio2project";
      repo = "django-supervisor";
      rev = "0c2df945454bbfedd1efae968a549b78dde9c37a";
    };

    postPatch = ''
      sed -i 's/setup_kwds\["use_2to3"\] = True//' setup.py
    '';

    propagatedBuildInputs = [ supervisor watchdog ];
  };
in
buildPythonPackage rec {
  name = "oioioi";
  version = "unstable-2023-03-12";

  src = builtins.path {
    path = ./..;
    filter = path: type: builtins.match "(.*/nix|.*/flake\\..*)" path == null;
  };

  postPatch = ''
    sed -i 's/"pytest-html/#"pytest-html/;
            s/"django-supervisor.*$/"django-supervisor",/' setup.py
  '';

  doCheck = false;
  dontStrip = true;

  # An env var for running tests. It isn't needed in module.nix,
  # as there we don't use the local sioworkers backend.
  SIOWORKERS_SANDBOXES_URL = "https://otsrv.net/sandboxes/";

  # This is just so pytest is available in nix shell and can be manually run.
  nativeBuildInputs = [ poetry-core pytest (
    pkgs.texlive.combine { inherit (pkgs.texlive)
      scheme-small collection-langpolish collection-fontsrecommended
      pst-barcode tex-gyre marginnote pstricks auto-pst-pdf catchfile pst-pdf
      pslatex a4wide fancyhdr luatex85 preview environ;
    }) pkgs.sox pkgs.flite ];

  # This is only required so that tests can be run from a devshell.
  # TODO: Add texlive to oioioi services in module.nix
  buildInputs = with pkgs; [ gcc glibc.static fpc ];

  propagatedBuildInputs = [
    django
    pytz
    o-sqlalchemy
    beautifulsoup4
    pyyaml
    python-dateutil
    django-two-factor-auth
    django-formtools
    o-django-registration-redux
    o-celery
    coreapi
    o-dj-pagination
    django-compressor
    django-statici18n
    pygments
    django-libsass
    django-debug-toolbar
    django-extensions
    djangorestframework
    werkzeug
    pytest
    pytest-metadata
    pytest-django
#    pytest-html
    pytest-xdist
    pytest-cov
    requests
    fpdf
    unicodecsv
    dnslib
    bleach
    chardet
    django-gravatar2
    django-mptt
    o-mistune
    pika
    raven
    unidecode
    sentry-sdk
    o-fontawesomefree
    o-django-nested-admin
    filetracker
    django-simple-captcha
    phonenumbers
    pdfminer-six
    supervisor
    django-supervisor

    sioworkers
    psycopg2 # postgresql support
  ];

  meta = with pkgs.lib; {
    description = "The main component of the SIO2 project";
    homepage = "https://github.com/sio2project/oioioi";
    # license = licenses.gpl3;
  };
}
