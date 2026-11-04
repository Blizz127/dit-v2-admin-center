"""Optional single synthetic integration capture; no hub, token or model access."""
import os

from local_evidence import read_json
from tools.build_integrated_context_preview import timestamp, validate

ENV = 'DIT_CONTEXT_CAPTURE_FILE'
LIMIT = 262144


def selected(mapping, keys):
    return {key: mapping[key] for key in keys.split()}


def from_env():
    path = os.environ.get(ENV)
    if not path:
        return {'status': 'Not configured', 'capture': None}
    try:
        data = validate(read_json(path, LIMIT))
        binding = data['statusBinding']
        view = binding['View']
        for field in view['Fields'] if view is not None else []:
            for key in ('ObservedAtUtc', 'ValidUntilUtc'):
                if field[key] is not None:
                    timestamp(field[key])
        # Whitelist the response; arbitrary extra file content is never exported.
        capture = selected(data, 'schema synthetic game path modelCall delivery systemMessage userMessage suppliedHistory')
        capture['contextReceipt'] = selected(data['contextReceipt'], 'RequestId SuppliedHistoryTurns IncludedHistoryTurns OmittedHistoryTurns SerializedCharacters MaximumSerializedCharacters PromptSha256')
        capture['statusBinding'] = selected(binding, 'RequestId State')
        capture['statusBinding']['Lookup'] = selected(binding['Lookup'], 'Game ServerInstance ActorKey')
        if view is None:
            capture['statusBinding']['View'] = None
            return {'status': 'Loaded', 'capture': capture}
        capture['statusBinding']['View'] = selected(view, 'Epoch Sequence Source RevisionSha256 FreshnessPolicyVersion ReadAtUtc')
        output = capture['statusBinding']['View']
        output['Body'] = selected(view['Body'], 'Game Realm Instance NativeActorId')
        output['Fields'] = [selected(field, 'Field State Value Reason ObservedAtUtc ValidUntilUtc') for field in view['Fields']]
        output['ApprovedFacts'] = [selected(fact, 'Key Value') for fact in view['ApprovedFacts']]
        return {'status': 'Loaded', 'capture': capture}
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
        return {'status': 'Unavailable', 'capture': None}
