#!/bin/sh
# Generates the runtime configuration of the frontend as window.__RUNTIME_CONFIG__.
#
# The keys are read from the env file. If an environment variable with the same name is set
# (even if it is empty), its value is used, otherwise the default value from the env file.
#
# Usage: runtime-env.sh [env file, default ./.env] [output file, default ./runtime-env.js]
#
# In the production image this script is executed from /docker-entrypoint.d with
# /usr/share/nginx/html as working directory.

set -eu

env_file="${1:-./.env}"
output_file="${2:-./runtime-env.js}"

if [ ! -f "$env_file" ]; then
    echo "runtime-env: $env_file does not exist" >&2
    exit 1
fi

tmp_file="$output_file.tmp.$$"
trap 'rm -f "$tmp_file"' EXIT

awk '
    function json_escape(s) {
        gsub(/\\/, "\\\\", s)
        gsub(/"/, "\\\"", s)
        gsub(/\n/, "\\n", s)
        gsub(/\r/, "\\r", s)
        gsub(/\t/, "\\t", s)
        return s
    }
    {
        line = $0
        sub(/#.*/, "", line)
        gsub(/^[ \t\r]+|[ \t\r]+$/, "", line)
        separator = index(line, "=")
        if (separator == 0) {
            next
        }
        key = substr(line, 1, separator - 1)
        value = (key in ENVIRON) ? ENVIRON[key] : substr(line, separator + 1)
        config = config (count++ ? "," : "") "\"" json_escape(key) "\":\"" json_escape(value) "\""
    }
    END {
        if (count == 0) {
            print "runtime-env: could not generate runtime config, check the format of the env file" > "/dev/stderr"
            exit 1
        }
        print "window.__RUNTIME_CONFIG__ = {" config "};"
    }
' "$env_file" > "$tmp_file"

mv -f "$tmp_file" "$output_file"
echo "runtime-env: generated $output_file from $env_file"
