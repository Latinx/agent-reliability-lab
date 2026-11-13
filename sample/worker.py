#!/usr/bin/env python3
"""One local order workflow with a SQLite idempotency sink and synthetic billing.

Independent command implementation of contract 1.0, not a production integration.
"""
import json
from pathlib import Path
import sqlite3
import sys
import time

connection = sqlite3.connect(Path(sys.argv[1]) / 'workflow.sqlite')
connection.executescript('''
CREATE TABLE IF NOT EXISTS effects (task TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS charges (run TEXT, cost INTEGER);
CREATE TABLE IF NOT EXISTS completion (task TEXT PRIMARY KEY);
''')
progress = 0
last_progress = time.monotonic()
stalled = False
capabilities = ['reset', 'work', 'stall', 'observe', 'attempt', 'deliver']

for line in sys.stdin:
    request = json.loads(line)
    response = {'contract': '1.0'}
    op = request['op']
    if request.get('contract') != '1.0':
        response['unsupported'] = True
    elif op == 'hello':
        response['capabilities'] = capabilities
    elif op == 'reset':
        with connection:
            for table in ('effects', 'charges', 'completion'):
                connection.execute('DELETE FROM ' + table)
        progress = 0
        last_progress = time.monotonic()
        stalled = False
    elif op == 'work':
        progress += 1
        last_progress = time.monotonic()
    elif op == 'stall':
        stalled = True
    elif op == 'observe':
        response.update(
            progress=progress,
            healthy=not stalled or time.monotonic() - last_progress < 0.1,
            charges=[{'run': run, 'cost': cost} for run, cost in connection.execute('SELECT run,cost FROM charges ORDER BY rowid')],
            effects=[row[0] for row in connection.execute('SELECT task FROM effects ORDER BY rowid')],
            checkpointed=bool(connection.execute('SELECT COUNT(*) FROM completion').fetchone()[0]))
    elif op == 'attempt':
        with connection:
            run_spent = connection.execute('SELECT COALESCE(SUM(cost),0) FROM charges WHERE run=?', (request['run'],)).fetchone()[0]
            day_spent = connection.execute('SELECT COALESCE(SUM(cost),0) FROM charges').fetchone()[0]
            allowed = (run_spent + request['cost'] <= request['run_cap'] and
                       day_spent + request['cost'] <= request['day_cap'])
            if allowed:
                connection.execute('INSERT INTO charges VALUES (?,?)', (request['run'], request['cost']))
        response['accepted'] = allowed
        # A billed attempt fails transiently; the checker requests its next retry.
        response['transient_failure'] = allowed
    elif op == 'deliver':
        with connection:
            connection.execute('INSERT OR IGNORE INTO effects VALUES (?)', (request['task'],))
        # Persist the external effect before the completion checkpoint.
        if not request['before_checkpoint']:
            with connection:
                connection.execute('INSERT OR IGNORE INTO completion VALUES (?)', (request['task'],))
    else:
        response['unsupported'] = True
    print(json.dumps(response), flush=True)
