#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/../fonts" || exit 1
B=https://raw.githubusercontent.com/google/fonts/main/ofl
dl(){ curl -sfL "$1" -o "$2" && echo "OK $(du -h "$2" | cut -f1)  $2" || echo "FAIL $2"; }
dl "$B/spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf" SpaceGrotesk-var.ttf
dl "$B/ibmplexsans/IBMPlexSans%5Bwdth,wght%5D.ttf" IBMPlexSans-var.ttf
for w in Regular Medium SemiBold Bold; do
  dl "$B/ibmplexsansarabic/IBMPlexSansArabic-$w.ttf" "IBMPlexSansArabic-$w.ttf"
done
for w in Regular Medium Bold; do
  dl "$B/ibmplexmono/IBMPlexMono-$w.ttf" "IBMPlexMono-$w.ttf"
done
for d in spacegrotesk ibmplexsans ibmplexsansarabic ibmplexmono; do
  dl "$B/$d/OFL.txt" "OFL-$d.txt"
done
echo "=== ls ==="
ls -la
