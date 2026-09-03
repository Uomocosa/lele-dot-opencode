{ pkgs, lib, config, inputs, ... }: {
  languages.rust = {
    enable = true;
    channel = "nightly";
    components = [ "rustc" "cargo" "clippy" "rustfmt" ];
  };

  packages = with pkgs; [
    cargo-nextest
  ];

  env.CARGO_TARGET_DIR = "/tmp/frt-build";

  tasks = {
    "lele:build" = { exec = "cargo build --all-targets"; showOutput = true; };
    "lele:clippy" = { exec = "cargo clippy --all-targets -- -D warnings"; showOutput = true; };
    "lele:fmt" = { exec = "cargo fmt -- --check"; showOutput = true; };
    "lele:nextest" = { exec = "cargo nextest run --all-targets"; showOutput = true; };
    "lele:lint" = { exec = "cargo run --manifest-path ../lele_lint/Cargo.toml"; showOutput = true; };
    "lele:taxonomy_check" = { exec = "cargo run --manifest-path ../lele_function_taxonomy/Cargo.toml --features rustc-private -- --manifest-path ./Cargo.toml"; showOutput = true; };
  };

  git-hooks.hooks = {
    lele-clippy = {
      enable = true;
      name = "clippy (<crate>)";
      entry = "bash -c 'cd <crate> && devenv tasks run lele:clippy 2>&1'";
      pass_filenames = false;
      always_run = true;
    };
    lele-fmt = {
      enable = true;
      name = "fmt (<crate>)";
      entry = "bash -c 'cd <crate> && devenv tasks run lele:fmt 2>&1'";
      pass_filenames = false;
      always_run = true;
    };
    lele-lint = {
      enable = true;
      name = "lele_lint (<crate>)";
      entry = "bash -c 'cd <crate> && devenv tasks run lele:lint 2>&1'";
      pass_filenames = false;
      always_run = true;
    };
    lele-taxonomy = {
      enable = true;
      name = "taxonomy_check (<crate>)";
      entry = "bash -c 'cd <crate> && devenv tasks run lele:taxonomy_check 2>&1'";
      pass_filenames = false;
      always_run = true;
    };
  };
}
