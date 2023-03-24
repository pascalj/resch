{
  inputs = {
    nixpkgs = {
      url = "github:nixos/nixpkgs/22.11";
    };
    flake-utils = {
      url = "github:numtide/flake-utils";
    };
  };
  outputs = { nixpkgs, flake-utils, ... }: flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = import nixpkgs {
        inherit system;
      };
    in rec {
      devShell = pkgs.mkShell {
        buildInputs = with pkgs; [
          (pkgs.python3.withPackages(ps: with ps; [
            graph-tool
            ortools

            (buildPythonPackage rec {
              pname = "portion";
              version = "2.4.0";
              src = fetchPypi {
                inherit pname version;
                sha256 = "sha256-3rFjiehE2/mutlQmH85f69cg5HhsZpDvu53BFggiaEA=";
              };
              doCheck = false;
              propagatedBuildInputs = [
                (buildPythonPackage rec {
                  pname = "sortedcontainers";
                  version = "2.4.0";
                  src = fetchPypi {
                    inherit pname version;
                    sha256 = "sha256-JcqloGzDC2uD0RQjQz9l0fnXbExqDJDjN56qQ7m/24g=";
                  };
                  doCheck = false;
                })
              ];
            })
          ]))
        ];
        shellHook = ''
          export PIP_PREFIX=$(pwd)/_build/pip_packages #Dir where built packages are stored
          export PYTHONPATH="$PIP_PREFIX/${pkgs.python3.sitePackages}:$PYTHONPATH"
          export PATH="$PIP_PREFIX/bin:$PATH"
          unset SOURCE_DATE_EPOCH
        '';
      };
    }
  );
}

