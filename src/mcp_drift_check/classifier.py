import re
from pathlib import Path

EXACT_SEMVER = re.compile(r"^v?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
RANGE_MARKERS = ("^", "~", ">", "<", "=", "*", "x", "X", "||", " - ")

def split_package_spec(spec: str):
    spec = spec.strip()
    if not spec:
        return None, None
    if spec.startswith('@'):
        slash = spec.find('/')
        if slash < 0:
            return spec, None
        at = spec.rfind('@')
        if at > slash:
            return spec[:at], spec[at+1:] or None
        return spec, None
    if '@' in spec:
        name, version = spec.rsplit('@', 1)
        return name, version or None
    return spec, None

def classify_package(spec: str, auto_yes: bool = False):
    package, version = split_package_spec(spec)
    suffix = " The invocation also uses -y/--yes, reducing interactive confirmation." if auto_yes else ""
    if not package:
        return None, None, "REVIEW", "Package reference could not be parsed.", "Review the command manually."
    if version is None:
        return package, None, "HIGH", "Package version is not pinned; future resolution may select different package code." + suffix, f"Pin {package} to a reviewed exact version."
    if version.lower() == 'latest':
        return package, version, "HIGH", "Package explicitly uses @latest; future resolution may select different package code." + suffix, f"Replace @latest with a reviewed exact version for {package}."
    if EXACT_SEMVER.fullmatch(version):
        return package, version, "SAFE", "Package is pinned to an exact semantic version.", "Keep the reviewed exact version pinned and update intentionally."
    if any(m in version for m in RANGE_MARKERS) or not EXACT_SEMVER.fullmatch(version):
        return package, version, "MEDIUM", "Package uses a non-exact version selector; resolution may change within the allowed selector." + suffix, f"Pin {package} to a reviewed exact version."
    return package, version, "REVIEW", "Package version could not be classified confidently.", "Review the package selector manually."

def classify_non_package(command: str):
    expanded = str(Path(command).expanduser())
    if command.startswith(('/', './', '../', '~')) or '/' in command:
        return "REVIEW", "Local or path-based executable; package drift rules do not apply directly.", "Verify the executable path, ownership, and update process."
    return "REVIEW", "Command is not a supported package-runner invocation and was not executed.", "Review how this command is installed and updated."
