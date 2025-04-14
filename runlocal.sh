#!/bin/sh
trap 'jobs %% 2>/dev/null && kill $(jobs -p)' EXIT

n=${1-2}
[ "$n" -lt 1 ] && { python pydames.py -s; exit; }

processus=
while [ "$n" -gt 0 ]
do
	python pydames.py &
	processus="$! ${processus}"
	n=$((n - 1))
done

python pydames.py -s

for id in $processus
do
	wait $id
done

