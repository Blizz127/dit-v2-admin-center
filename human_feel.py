"""Human-feel signals: plain measurements of how machine-regular a bot's logged actions are.

Why: the owner wants bots that feel like players. These functions surface repeated timing patterns from
logged timestamps so QA can compare runs. Labels are heuristics, not proof of human or non-human behavior.

- cadence: the share of a repeated action's in-fight gaps in the most common rounded bucket.
- sync: the share of a bot's group actions that another bot did within SYNC_WINDOW_S.
- schedule: the share of the gaps between trip starts in the most common rounded bucket.

Each result is a measurement plus one boolean label. The label never hides the numbers, and a result with
too few samples is None (unknown), never a pass. Thresholds and action selection use unrounded ratios;
only the reported shares are rounded. Pure functions: no I/O or clock.
"""
from bisect import bisect_left

MIN_GAPS = 10            # Fewer in-fight gaps than this is too little to call a cadence.
FIGHT_GAP_S = 60.0       # A longer gap separates two fights; it is not part of a cadence.
CADENCE_STEP_S = 0.1     # Gaps are compared after rounding to this step.
METRONOMIC_SHARE = 0.6   # At or over this share in one rounded bucket is labelled metronomic.
MIN_SYNC = 5             # Fewer group actions than this is too little to call synchrony.
SYNC_WINDOW_S = 1.0
SYNC_SHARE = 0.6
MIN_INTERVALS = 3        # Fewer gaps between trip starts than this is too little to call a schedule.
SCHEDULE_STEP_S = 2.0
SCHEDULE_SHARE = 0.6


def _gaps(moments):
    ordered = sorted(moments)
    return [(later - earlier).total_seconds() for earlier, later in zip(ordered, ordered[1:])]


def _modal(gaps, step):
    """(most common gap rounded to step, how many gaps equal it). Ties go to the shorter gap."""
    counts = {}
    for gap in gaps:
        bucket = round(gap / step)
        counts[bucket] = counts.get(bucket, 0) + 1
    bucket, count = min(counts.items(), key=lambda item: (-item[1], item[0]))
    return round(bucket * step, 3), count


def cadence(moments_by_action):
    """The most regular repeated action: {action, gaps, modalGapS, modalCount, modalShare, metronomic}, or None.

    moments_by_action maps an action name to the datetimes it happened. Only gaps under FIGHT_GAP_S count."""
    best = best_score = None
    for action in sorted(moments_by_action):
        gaps = [gap for gap in _gaps(moments_by_action[action]) if 0 < gap < FIGHT_GAP_S]
        if len(gaps) < MIN_GAPS:
            continue
        gap, count = _modal(gaps, CADENCE_STEP_S)
        share = count / len(gaps)
        score = (share, len(gaps))
        if best_score is None or score > best_score:
            best = {'action': action, 'gaps': len(gaps), 'modalGapS': gap, 'modalCount': count,
                    'modalShare': round(share, 3), 'metronomic': share >= METRONOMIC_SHARE}
            best_score = score
    return best


def sync(own, others):
    """Group actions done within SYNC_WINDOW_S of another bot: {actions, together, share, synchronized}, or None.

    own and others map a kind of group action (mount, dismount, trip end) to datetimes; a bot is only compared
    with other bots doing the same kind."""
    actions = together = 0
    for kind, moments in own.items():
        theirs = sorted(others.get(kind, ()))
        for moment in moments:
            actions += 1
            index = bisect_left(theirs, moment)
            near = [theirs[i] for i in (index - 1, index) if 0 <= i < len(theirs)]
            together += any(abs((other - moment).total_seconds()) <= SYNC_WINDOW_S for other in near)
    if actions < MIN_SYNC:
        return None
    share = together / actions
    return {'actions': actions, 'together': together, 'share': round(share, 3), 'synchronized': share >= SYNC_SHARE}


def schedule(starts):
    """Trip starts on a fixed clock: {intervals, modalIntervalS, modalCount, modalShare, fixed}, or None."""
    gaps = [gap for gap in _gaps(starts) if gap > 0]
    if len(gaps) < MIN_INTERVALS:
        return None
    gap, count = _modal(gaps, SCHEDULE_STEP_S)
    share = count / len(gaps)
    return {'intervals': len(gaps), 'modalIntervalS': gap, 'modalCount': count, 'modalShare': round(share, 3),
            'fixed': share >= SCHEDULE_SHARE}
