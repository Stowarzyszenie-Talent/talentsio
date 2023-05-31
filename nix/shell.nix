{ pkgs ? import <nixpkgs> { } }:
with pkgs;
mkShell {
  buildInputs = [
    :q
    gcc glibc.static fpc texlive.combined.scheme-full
  ];

  shellHook = ''
    
  '';
}
