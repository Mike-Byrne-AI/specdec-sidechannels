"""Public exception hierarchy for Lockstep.

The hierarchy keeps untrusted-container failures typed and lets callers
separate malformed input, unsupported profiles, integrity damage, decoder
desynchronisation, and local resource-policy failures without matching text.
"""

from __future__ import annotations


class LockstepError(Exception):
    """Base class for all expected Lockstep failures."""


class CoderError(LockstepError):
    """Invalid coder/model input or an impossible coder state."""


class ContainerError(LockstepError):
    """Base class for malformed, unsupported, or undecodable containers."""


class ManifestError(ContainerError):
    """The manifest or its schema is malformed."""


class UnsupportedProfileError(ManifestError):
    """The container pins a profile/model this runtime cannot reproduce."""


class IntegrityError(ContainerError):
    """The stored payload is truncated, padded, or fails its digest."""


class DesyncError(ContainerError):
    """Decode completed incorrectly or the decoded digest does not match."""


class ResourceLimitError(ContainerError):
    """A caller-supplied safety limit was exceeded."""


class ManifestResourceLimitError(ManifestError, ResourceLimitError):
    """A manifest-declared size exceeds the reader policy."""
