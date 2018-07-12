#!/bin/bash
echo ${REDIS_URL:=redis://wexam-redis}
rq worker --url $REDIS_URL -q json2latex-task