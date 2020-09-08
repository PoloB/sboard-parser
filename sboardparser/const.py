"""
Defines all the constants that are used to properly parse StoryBoard Pro files.
"""

# Defines which xml elements are to be considered as list where building the
# Python object hierarchy. The values gives the name of the list in which to
# append those elements.
LIST_ATTRIBUTES = {"warpSeq": "warp_sequences",
                   "transitionSeq": "transition_sequences",
                   "soundSequence": "sound_sequences",
                   "envelope": "envelopes"}

