from dbt.contracts.util import Replaceable, Mergeable
from dbt.logger import GLOBAL_LOGGER as logger  # noqa
from dbt import tracking
from dbt.ui import printer
# from dbt.utils import JSONEncoder

from hologram import JsonSchemaMixin
from hologram.helpers import HyphenatedJsonSchemaMixin, register_pattern, \
    ExtensibleJsonSchemaMixin

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Union, Any, NewType

PIN_PACKAGE_URL = 'https://docs.getdbt.com/docs/package-management#section-specifying-package-versions' # noqa
DEFAULT_SEND_ANONYMOUS_USAGE_STATS = True
DEFAULT_USE_COLORS = True


Name = NewType('Name', str)
register_pattern(Name, r'^[^\d\W]\w*\Z')

# this does not support the full semver (does not allow a trailing -fooXYZ) and
# is not restrictive enough for full semver, (allows '1.0'). But it's like
# 'semver lite'.
SemverString = NewType('SemverString', str)
register_pattern(
    SemverString,
    r'^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(\.(?:0|[1-9]\d*))?$',
)


@dataclass
class Quoting(JsonSchemaMixin, Mergeable):
    identifier: Optional[bool]
    schema: Optional[bool]
    database: Optional[bool]
    project: Optional[bool]


@dataclass
class Package(Replaceable, HyphenatedJsonSchemaMixin):
    pass


@dataclass
class LocalPackage(Package):
    local: str


@dataclass
class GitPackage(Package):
    git: str
    revision: Optional[str]
    warn_unpinned: Optional[bool] = None


@dataclass
class RegistryPackage(Package):
    package: str
    version: Union[str, List[str]]


PackageSpec = Union[LocalPackage, GitPackage, RegistryPackage]


@dataclass
class PackageConfig(JsonSchemaMixin, Replaceable):
    packages: List[PackageSpec]


@dataclass
class ProjectPackageMetadata:
    name: str
    packages: List[PackageSpec]

    @classmethod
    def from_project(cls, project):
        return cls(name=project.project_name,
                   packages=project.packages.packages)


@dataclass
class Downloads(ExtensibleJsonSchemaMixin, Replaceable):
    tarball: str


@dataclass
class RegistryPackageMetadata(
    ExtensibleJsonSchemaMixin,
    ProjectPackageMetadata,
):
    downloads: Downloads


@dataclass
class Project(HyphenatedJsonSchemaMixin, Replaceable):
    name: Name
    version: Union[SemverString, float]
    project_root: Optional[str]
    source_paths: Optional[List[str]]
    macro_paths: Optional[List[str]]
    data_paths: Optional[List[str]]
    test_paths: Optional[List[str]]
    analysis_paths: Optional[List[str]]
    docs_paths: Optional[List[str]]
    target_path: Optional[str]
    snapshot_paths: Optional[List[str]]
    clean_targets: Optional[List[str]]
    profile: Optional[str]
    log_path: Optional[str]
    modules_path: Optional[str]
    quoting: Optional[Quoting]
    on_run_start: Optional[List[str]] = field(default_factory=list)
    on_run_end: Optional[List[str]] = field(default_factory=list)
    require_dbt_version: Optional[Union[List[str], str]] = None
    models: Dict[str, Any] = field(default_factory=dict)
    seeds: Dict[str, Any] = field(default_factory=dict)
    packages: List[PackageSpec] = field(default_factory=list)


@dataclass
class UserConfig(ExtensibleJsonSchemaMixin, Replaceable):
    send_anonymous_usage_stats: bool = DEFAULT_SEND_ANONYMOUS_USAGE_STATS
    use_colors: bool = DEFAULT_USE_COLORS
    printer_width: Optional[int] = None

    def set_values(self, cookie_dir):
        if self.send_anonymous_usage_stats:
            tracking.initialize_tracking(cookie_dir)
        else:
            tracking.do_not_track()

        if self.use_colors:
            printer.use_colors()

        if self.printer_width:
            printer.printer_width(self.printer_width)


@dataclass
class ProfileConfig(HyphenatedJsonSchemaMixin, Replaceable):
    profile_name: str = field(metadata={'preserve_underscore': True})
    target_name: str = field(metadata={'preserve_underscore': True})
    config: UserConfig
    threads: int
    # TODO: make this a dynamic union of some kind?
    credentials: Optional[Dict[str, Any]]


@dataclass
class ConfiguredQuoting(JsonSchemaMixin, Replaceable):
    identifier: bool
    schema: bool
    database: Optional[bool]
    project: Optional[bool]


@dataclass
class Configuration(Project, ProfileConfig):
    cli_vars: Dict[str, Any] = field(
        default_factory=dict,
        metadata={'preserve_underscore': True},
    )
    quoting: Optional[ConfiguredQuoting] = None


@dataclass
class ProjectList(JsonSchemaMixin):
    projects: Dict[str, Project]
