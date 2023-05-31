{ pkgs
, lib
, buildPythonPackage
, fetchPypi
, pythonAtLeast
, python

, six
, libsass
, django-otp
, setuptools
, setuptools_scm
, urllib3
, selenium
, vine
, atomicwrites
, django-appconf
, django-statici18n
, rcssmin
, rjsmin
, billiard
, wcwidth
, pluggy
, py
, attrs
, more-itertools
, kombu
, pytest-rerunfailures
, pytest-sugar
, case
, watchdog
, supervisor

, pytz
, sqlalchemy
, django
, beautifulsoup4
, pyyaml
, python-dateutil
, django-formtools
, celery
, coreapi
, django-compressor
, pygments
, django-debug-toolbar
, django-extensions
, djangorestframework
, pytest
, pytest-metadata
, pytest-django
, pytest-html
, pytest-xdist
, pytest-cov
, requests
, fpdf
, unicodecsv
, shortuuid
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
, importlib-metadata
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

  python-monkey-business = simplePackage {
    name = "python-monkey-business";
    version = "1.0.0";
    hash = "sha256-mXZSKYl2bwCyqqJOyW6suRpt57cAHRRSB5MjsHGYjg4=";

    propagatedBuildInputs = [
      six
    ];
  };
  django-phonenumber-field = simplePackage {
    name = "django-phonenumber-field";
    version = "6.4.0";
    hash = "sha256-cqPno+dJO/KhLAejvHfOiYE6zBZZK/BNDu47WkUgl+0=";

    format = "pyproject";

    nativeBuildInputs = [
      setuptools
      setuptools_scm
    ];

    propagatedBuildInputs = [
      django
    ];
  };
  django-selenosis = simplePackage {
    name = "django-selenosis";
    version = "2.0.0";
    hash = "sha256-/MSC5/yAv+dN7JwrY0LY2R45gI0ub48Ldg05TKqmubE=";

    doCheck = false;

    propagatedBuildInputs = [
      django
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
  o-pluggy = overridePackage pluggy {
    version = "0.13.1";
    hash = "sha256-FbKs3mZlYeEpjXG1IwB+1zZN4HApIZtgTPgIv6HHZbA=";
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
  o-watchdog = overridePackage watchdog {
    propagatedBuildInputsFilter = x: (lib.getName x) == "PyYAML";
    extraPropagatedBuildInputs = [ o-pyyaml ];
  };

  # o-pytz = overridePackage pytz {
  #   version = "2021.1";
  #   hash = "sha256-g6SpCJS/OOJDzwUsi1jzgb/pp6SD9qnKsUC8f3AqxNo=";
  # };
  o-pyyaml = overridePackage pyyaml {
    pypiName = "PyYAML";
    version = "5.4.1";
    hash = "sha256-YHd0y7oocyv6gCtUuqdIQhX1MJkQVbtWLvvtWy8gpF4=";

    postPatch = "rm -r tests/lib{,3}";
    checkPhase = "";
    installCheckPhase = "";
    doCheck = false;
    doInstallCheck = false;
    patches = [ ./pyyaml-disable-tests.patch ];
  };
  o-django-two-factor-auth = simplePackage {
    name = "django-two-factor-auth";
    version = "1.13.2";
    hash = "sha256-P6wmbRJHKsZkdd1ze7GPKZJIQxO/Vqz1ou6l6CQpHuY=";

    doCheck = false;

    propagatedBuildInputs = [
      django-otp
      django-phonenumber-field
      o-django-formtools
    ];
  };
  o-django-formtools = overridePackage django-formtools {
    name = "django-formtools";
    version = "2.3";
    hash = "sha256-lmO27KZHd7aNbUFC762Fl/6aaFkkZzslqoodz/TbAMM=";
  };
  o-django-registration-redux = simplePackage {
    name = "django-registration-redux";
    version = "2.9";
    hash = "sha256-49EjNUobjL+gBdYPHruJroVB8+r/1hdNnyr/UptX5DA=";

    doCheck = false;

    nativeCheckInputs = [
      pytest
      pytest-django
    ];
  };
  o-celery = overridePackage celery {
    version = "4.4.7";
    hash = "sha256-0iCxOo7VfHgUms+CwAZ4U1YHGESv4LJwEqSZHUQCb58=";

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

    propagatedBuildInputs = [ o-vine o-billiard o-kombu ];
  };
  o-dj-pagination = simplePackage {
    name = "dj-pagination";
    version = "2.5.0";
    hash = "sha256-hgMBzcee3AcSAIkhA3sjQScdOlVYa8NPrQcudMjoAMQ=";

    propagatedBuildInputs = [ django ];
  };
  o-django-compressor = overridePackage django-compressor {
    pypiName = "django_compressor";
    version = "2.4.1";
    hash = "sha256-M1gHdgXBRv3Mpfnq/7UKpdvhXyOPiFRnkRXr8xwEFeA=";

    postPatch = ''
      sed -i 's/rcssmin\s*==/rcssmin >=/' setup.py
      sed -i 's/rjsmin\s*==/rjsmin >=/' setup.py
    '';

    propagatedBuildInputs = [ six django-appconf rcssmin rjsmin ];
  };
  o-django-libsass = simplePackage {
    name = "django-libsass";
    version = "0.8";
    hash = "sha256-OPq0zhJFVC86/XJI3Ej4oLJh9fbGHnzEOWmpyQebX/0=";

    propagatedBuildInputs = [
      o-django-compressor
      libsass
    ];
  };
  o-django-debug-toolbar = simplePackage {
    name = "django-debug-toolbar";
    version = "3.3.0";

    # oh yes 
    doCheck = false;

    src = pkgs.fetchurl {
      # why does nothing else work??
      url = "https://files.pythonhosted.org/packages/db/2b/901d969678caf037fa95ccb3fac2b6944b03235e6423c211fe966e6a8168/django-debug-toolbar-3.3.0.tar.gz";
      hash = "sha256-dBUcKS25RV+lEn1kpEFPrujuOxzd+xfw6Tzz8TzYS8E=";
    };

    propagatedBuildInputs = [
      django
    ];
  };
  o-django-extensions = overridePackage django-extensions {
    version = "3.2.0";
    hash = "sha256-fcfNHaUNg7dkR6WPXX5cjmzYPyHpt+X5fmtkT01OIaY=";

    disabledTestPaths = [
      "tests/management/commands/test_set_fake_emails.py"
      "tests/management/commands/test_syncdata.py"
      "tests/management/commands/test_validate_templates.py"
      "tests/management/commands/test_export_emails.py"
      "tests/management/commands/test_export_emails.py"
      "tests/management/commands/test_export_emails.py"
      "tests/management/commands/test_export_emails.py"
      "tests/management/commands/test_export_emails.py"
      "tests/management/commands/test_set_fake_passwords.py"
      "tests/management/commands/test_set_fake_passwords.py"
      "tests/management/commands/test_set_fake_passwords.py"
      "tests/management/commands/test_set_fake_passwords.py"
      "tests/management/commands/test_pipchecker.py"
      "tests/management/commands/test_pipchecker.py"
      "tests/management/commands/test_pipchecker.py"
      "tests/management/commands/test_pipchecker.py"
      "tests/management/commands/test_pipchecker.py"
      "tests/management/commands/test_pipchecker.py"
    ];
  };
  # o-djangorestframework = overridePackage djangorestframework {
  #   version = "3.12.4";
  #   hash = "sha256-90eUmo3ayHboeRkN8ZS5JcF3zetyWgmdsUYIcvfAp/I=";
  #
  #   propagatedBuildInputs = [
  #     pytz
  #   ];
  #
  #   disabledTestPaths = [
  #     "tests/authentication/test_authentication.py"
  #     "tests/browsable_api/test_browsable_api.py"
  #     "tests/browsable_api/test_browsable_nested_api.py"
  #     "tests/browsable_api/test_form_rendering.py"
  #     "tests/generic_relations/test_generic_relations.py"
  #     "tests/schemas/test_coreapi.py"
  #     "tests/schemas/test_get_schema_view.py"
  #     "tests/schemas/test_managementcommand.py"
  #     "tests/schemas/test_openapi.py"
  #     "tests/importable/test_installed.py"
  #   ];
  # };
  o-pytest = overridePackage pytest {
    version = "4.6.11";
    hash = "sha256-UPqCOS8hIMw+wsoKde5hW+TEeeZmaXiXcfF1gzK+Q1M=";

    propagatedBuildInputs = [
      py
      atomicwrites
      wcwidth
      o-pluggy
      six
      attrs
      more-itertools
    ];
  };
  o-pytest-metadata = overridePackage pytest-metadata {
    version = "1.11.0";
    hash = "sha256-cbUG1J005TnMPP23zixfByvqXJUzIAAslZaOAjj47PE=";
  };
  o-pytest-django = overridePackage pytest-django {
    version = "3.10.0";
    hash = "sha256-Tebb0HfthgZhaVj3dlX+0NXj7kUVlHVnHH+mdZbG26Y=";
  };
  o-pytest-html = overridePackage pytest-html {
    version = "1.22.1";
    hash = "sha256-8Prm3nHwL2L5Rg9ijQxfcLDNyGuzkyOYYMfexw/Slz0=";

    propagatedBuildInputsFilter = x: (lib.getName x) != "pytest-metadata";
    extraPropagatedBuildInputs = [ o-pytest-metadata ];
  };
  o-pytest-xdist = overridePackage pytest-xdist {
    version = "1.34.0";
    hash = "sha256-NA6Og+KkwNhhvdjQXF17cUP27qCrqQKZfbFcKoa+BO4=";

    disabledTestPaths = [ "testing/acceptance_test.py" ];

    extraPropagatedBuildInputs = [ six ];
  };
  o-pytest-cov = overridePackage pytest-cov {
    version = "2.11.1";
    hash = "sha256-NZlS2dObn4ItnSkyRIPnugSjoX3X0FqmvrfqAeNZ5fc=";
  };
  o-mistune = overridePackage mistune {
    version = "0.8.4";
    hash = "sha256-WaNCnbU8ULXGvMigf4hIywDX3IvbQxpKtBkg0gHUdW4=";
  };
  o-fontawesomefree = simplePackage rec {
    name = "fontawesomefree";
    version = "6.3.0";
    format = "wheel";

    src = fetchPypi {
      pname = name;
      inherit version format;
      dist = "py3";
      python = "py3";
      hash = "sha256-kmJ+dYXh19ET4UeohVvazZ/CimuDpwypvrEfr+DadbY=";
    };
  };
  o-django-nested-admin = simplePackage {
    name = "django-nested-admin";
    version = "4.0.2";
    hash = "sha256-eaXOgLgcQaD0j3ePtVajchAp30hYC/zmClli/6LvLUc=";

    doCheck = false;

    propagatedBuildInputs = [
      python-monkey-business
      selenium
      django-selenosis
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

    propagatedBuildInputs = [ supervisor o-watchdog ];
  };
in
buildPythonPackage rec {
  name = "oioioi";
  version = "unstable-2023-03-12";
  disabled = pythonAtLeast "3.9";

  src = builtins.path {
    path = ./..;
    filter = path: type: builtins.match "(.*/nix|.*/flake\\..*)" path == null;
  };

  doCheck = false;
  dontStrip = true;

  # An env var for running tests. It isn't needed in module.nix,
  # as there we don't use the local sioworkers backend.
  SIOWORKERS_SANDBOXES_URL = "https://otsrv.net/sandboxes/";

  # This is just so pytest is available in nix shell and can be manually run.
  nativeBuildInputs = [ o-pytest pkgs.texlive.combined.scheme-full ];

  # This is only required so that tests can be run from a devshell.
  # TODO: Add texlive to oioioi services in module.nix
  buildInputs = with pkgs; [ gcc glibc.static fpc texlive.combined.scheme-full ];

  propagatedBuildInputs = [
    django
    pytz
    sqlalchemy
    beautifulsoup4
    o-pyyaml
    python-dateutil
    o-django-two-factor-auth
    o-django-formtools
    o-django-registration-redux
    o-celery
    coreapi
    o-dj-pagination
    o-django-compressor
    django-statici18n
    pygments
    o-django-libsass
    o-django-debug-toolbar
    o-django-extensions
    djangorestframework
    o-pytest
    o-pytest-metadata
    o-pytest-django
    o-pytest-html
    o-pytest-xdist
    o-pytest-cov
    requests
    fpdf
    unicodecsv
    shortuuid
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
    importlib-metadata
    supervisor
    django-supervisor
    sioworkers

    # postgresql support
    psycopg2
  ];

  meta = with pkgs.lib; {
    description = "The main component of the SIO2 project";
    homepage = "https://github.com/sio2project/oioioi";
    # license = licenses.gpl3;
  };
}
