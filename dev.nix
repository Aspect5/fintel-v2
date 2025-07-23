# dev.nix

{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python311
    # (FIX) The package is called 'nodejs_20' not 'nodejs-20_x'
    pkgs.nodejs_20
    pkgs.gcc
  ];

  shellHook = ''
    export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
  '';
}