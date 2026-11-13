#!/usr/bin/env python3
"""Interpret explicit synthetic workflow steps; not an integration with a real agent."""
import json
from pathlib import Path
import sys
import time

config = json.loads(Path(sys.argv[1]).read_text())
statefile = Path(sys.argv[2]) / 'model-state.json'
state = json.loads(statefile.read_text()) if statefile.exists() else {}

for line in sys.stdin:
    request = json.loads(line)
    op = request['op']
    result = {'contract': '1.0'}
    if op == 'hello':
        result['capabilities'] = list(config['steps'])
    elif op not in config['steps']:
        result['unsupported'] = True
    else:
        for step in config['steps'][op]:
            action = step['action']
            if action == 'reset':
                state = {'progress': 0, 'healthy': True, 'charges': [], 'effects': [], 'checkpointed': False}
            elif action == 'progress':
                state['progress'] += 1
            elif action == 'stall':
                # The process remains alive, but the model makes no task progress.
                pass
            elif action == 'charge':
                state['charges'].append({'run': request['run'], 'cost': request['cost']})
            elif action == 'effect':
                state['effects'].append(request['task'])
            elif action == 'checkpoint':
                state['checkpointed'] = not request['before_checkpoint']
            elif action == 'snapshot':
                result.update(state)
            else:
                raise ValueError('unknown model action: ' + action)
        statefile.write_text(json.dumps(state))
    print(json.dumps(result), flush=True)
