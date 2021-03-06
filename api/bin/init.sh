#!/bin/sh
make --file=./bin/Makefile all
sqlite-utils insert ./var/users.db users --csv ./share/users.csv --pk=id
sqlite-utils insert ./var/users.db followers --csv ./share/followers.csv --pk=id
sqlite-utils insert ./var/timelines.db posts --csv ./share/posts.csv --pk=id
python3 ./polls/polls_create_table.py
python3 ./polls/polls_load_data.py
