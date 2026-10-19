#!/usr/bin/env python3
"""
Decode and compare two JWTs (no signature verification - just claims).

Handy for comparing tokens in this lab: compare the access_token from the PKCE user flow
against the access_token from the client_credentials flow, to see how
a user-bound token differs from a machine-to-machine token.

Usage:
    python3 compare-tokens.py

You'll be prompted to paste each token. Or pass them as args:
    python3 compare-tokens.py <token1> <token2>
"""

import sys
import json
import base64


def decode_jwt(token):
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise ValueError("Not a valid JWT (expected 3 dot-separated parts)")

    def b64decode(segment):
        # JWT base64url is unpadded; pad it back out before decoding
        padded = segment + "=" * (-len(segment) % 4)
        return json.loads(base64.urlsafe_b64decode(padded))

    header = b64decode(parts[0])
    payload = b64decode(parts[1])
    return header, payload


def get_token(prompt):
    print(prompt)
    return input("> ").strip()


def print_section(title, data):
    print(f"\n--- {title} ---")
    print(json.dumps(data, indent=2))


def diff_claims(payload_a, payload_b, label_a, label_b):
    keys = sorted(set(payload_a.keys()) | set(payload_b.keys()))
    print(f"\n--- Claim comparison ({label_a} vs {label_b}) ---")
    print(f"{'claim':<20} {label_a:<35} {label_b:<35}")
    print("-" * 90)
    for key in keys:
        val_a = payload_a.get(key, "<absent>")
        val_b = payload_b.get(key, "<absent>")
        marker = "  " if val_a == val_b else "≠ "
        print(f"{marker}{key:<18} {str(val_a):<35} {str(val_b):<35}")


def main():
    if len(sys.argv) == 3:
        token_a, token_b = sys.argv[1], sys.argv[2]
    else:
        token_a = get_token("Paste access_token #1 (e.g. from PKCE user flow):")
        token_b = get_token("Paste access_token #2 (e.g. from client_credentials flow):")

    header_a, payload_a = decode_jwt(token_a)
    header_b, payload_b = decode_jwt(token_b)

    print_section("Token #1 header", header_a)
    print_section("Token #1 payload", payload_a)
    print_section("Token #2 header", header_b)
    print_section("Token #2 payload", payload_b)

    diff_claims(payload_a, payload_b, "Token #1", "Token #2")

    print("\nNote: this only decodes the tokens, it does NOT verify signatures.")
    print("Use the JWKS endpoint + jwt.io (or a real JWT library) for signature verification.")


if __name__ == "__main__":
    main()
