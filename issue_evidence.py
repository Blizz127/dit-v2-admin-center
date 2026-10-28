"""Project bounded historical evidence and pending-decision metadata to issue cards."""


def bridge_fault_issue():
    return {
        'title': 'FFXI bridge delayed-delivery fault (historical)', 'scope': 'FFXI',
        'status': 'Reported historically; current status unknown',
        'detail': 'The project evidence reports a delayed-delivery fault and failed bridge at 09:41 CDT on October 28, 2026. The exact exception was not observed and the reply outcome is uncertain.',
        'suggestedFix': 'The coordinator reported approval of fix ef097b2; ask the owning lead for the deployed revision and readiness. Preserve the fault marker and uncertain reply; do not replay or restart based on this card.',
        'bridgeObservation': True,
        'source': 'DIT platform evidence: ffxi-relative-inbox-20261028/README.md',
        'updatedAt': '2026-10-28T14:41:24Z', 'timeLabel': 'Reported',
    }


def pending_decision_issues(owner_attention):
    result = []
    for item in owner_attention.get('items', []):
        result.append({'title': 'Pending owner decision: ' + item['title'],
                       'detail': 'Coordinator approval record for ' + item['project'] + '; expires ' + item['expiresAt'] + '. Other decisions may be tracked elsewhere.',
                       'scope': 'Decisions', 'status': 'Pending record', 'source': 'Coordinator approval records',
                       'updatedAt': item['createdAt'], 'timeLabel': 'Created', 'ownerAttention': True})
    return result
