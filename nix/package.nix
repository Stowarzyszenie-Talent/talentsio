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
, watchdog
, supervisor

, pytz
, sqlalchemy
, django
, beautifulsoup4
, pyyaml
, python-dateutil
, django-two-factor-auth
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
, pytest-html
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
, fontawesomefree
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

  python-monkey-business = simplePackage {
    name = "python-monkey-business";
    version = "1.0.0";
    hash = "sha256-mXZSKYl2bwCyqqJOyW6suRpt57cAHRRSB5MjsHGYjg4=";

    propagatedBuildInputs = [
      six
    ];
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
    sed -i 's/"django-supervisor.*$/"django-supervisor",/' setup.py
  '';

  doCheck = false;
  dontStrip = true;

  # An env var for running tests. It isn't needed in module.nix,
  # as there we don't use the local sioworkers backend.
  SIOWORKERS_SANDBOXES_URL = "https://otsrv.net/sandboxes/";

  passthru = {
    o-texlive = (
      pkgs.texlive.combine { inherit (pkgs.texlive)
        scheme-small collection-langpolish collection-fontsrecommended
        collection-latexrecommended collection-latexextra
        pst-barcode tex-gyre pstricks auto-pst-pdf pst-pdf
        pslatex luatex85 epsf;
    });
    inherit celery;
  };

  # This just for running tests in `nix develop`.
  nativeBuildInputs = [ poetry-core pytest pkgs.sox pkgs.flite passthru.o-texlive ];
  buildInputs = with pkgs; [ gcc glibc.static fpc ];

  propagatedBuildInputs = [
    django
    pytz
    sqlalchemy
    beautifulsoup4
    pyyaml
    python-dateutil
    django-two-factor-auth
    o-django-registration-redux
    celery
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
    pytest-html
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
    fontawesomefree
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
