#!/bin/bash

cd "$(dirname "$0")"

for run in {1..12}; do
	if [ "$(cat stats_lock)" == "1" ]; then
		stats=`docker stats --no-stream --format "table {{.Name}},{{.CPUPerc}},{{.MemUsage}}" | tail -n +2 | sort --field-separator=',' -k 2 -h -r | head -5`
		echo "$stats" > stats
	fi
	sleep 5
done

echo 0 > stats_lock
