"""Check reviewed local note bytes, not remote service state or acceptance."""
from hashlib import sha256

LIMIT = 65536
SCHEMA = 'dit-admin-operation-sources-v1'
# Fixed, reviewed paths relative to the local home; never supplied by a request.
SOURCES = (
    dict(id='wake-8450', title='8450 wake service',
         path='dev/dit-ffxi-bridge-integration-20261029/docs/evidence/ax41-retirement-20261029/READBACK-20261030-0055.md',
         sha256='4f2acaf75bf2271249a43b1c97c4ecedca6f3abad96b7c9d51bb7240fa60f3ac',
         reference='DIT fa843e8 / READBACK-20261030-0055.md',
         reported='2026-10-30 00:55–00:56 UTC: AX41 controller retained; Banshee controller absent. Public transport returned 401.',
         missing='Completed cutover and authenticated per-game readbacks. Current route unknown; 401 is not acceptance.'),
    dict(id='ashes', title='Ashes of Creation',
         path='dev/sandalcore/docs/experimental/BANSHEE_SIGN_IN.md',
         sha256='1b3f3f472d5fe8becaae52f075acfd68b9d8ab6f52d9ce781331fc44b6d48124',
         reference='SandalCore BANSHEE_SIGN_IN.md / reviewed October 30',
         reported='October 29: auth deployment reported at 19:30 UTC; auto-provisioning update at 23:01 UTC. Staging sign-in checks are separate.',
         missing='Owner PLAY/client acceptance not recorded. Outside the twelve-game controller manifest; no 8450 binding established.'),
    dict(id='lotro', title='LOTRO',
         path='dev/lotro-rust/docs/evidence/owner-tailnet-instance-20261029.md',
         sha256='adca1885e96dfd8d742af34adbfef9bf0a2c4aa7ceaef641f520f18f8310fc9a',
         reference='LOTRO owner-tailnet-instance-20261029.md / untracked owning-lead note',
         reported='October 29: owner-only public instance and Banshee dry-run reported; hostname advertisement updated at 14:48 UTC. Access rule is runtime-only.',
         missing='Alienware/public-instance client acceptance not recorded. Outside the twelve-game controller manifest; no 8450 binding established.'),
)


def read(home=None):
    """home=None packages dated context without claiming a source check."""
    rows = []
    for source in SOURCES:
        state = 'Not checked in standalone preview'
        if home is not None:
            try:
                with (home / source['path']).open('rb') as stream:
                    raw = stream.read(LIMIT + 1)
                state = ('Reviewed bytes match' if len(raw) <= LIMIT and
                         sha256(raw).hexdigest() == source['sha256'] else
                         'Source changed — review required')
            except OSError:
                state = 'Source unavailable'
        rows.append({key: source[key] for key in
                     ('id', 'title', 'sha256', 'reference', 'reported', 'missing')} | {'state': state})
    return {'schema': SCHEMA, 'rows': rows}
