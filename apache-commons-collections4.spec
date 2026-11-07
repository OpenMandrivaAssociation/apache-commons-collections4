Name:		apache-commons-collections4
Version:	4.6.0
Release:	1
Summary:	Interfaces and utilities that extend the Java Collections Framework
Group:		Development/Java
License:	ASL 2.0
URL:		https://commons.apache.org/proper/commons-collections/
Source0:	https://github.com/apache/commons-collections/archive/refs/tags/rel/commons-collections-%{version}.tar.gz#/commons-collections4-%{version}.tar.gz

BuildArch:	noarch
# The site checkout profile is active when site-content is absent, and
# antrun is on the sysjar keep list.
%global sysjar_drops --drop org.apache.maven.plugins:maven-antrun-plugin
BuildRequires:	python
BuildRequires:	mvn(org.apache.commons:commons-parent:pom::)
BuildRequires:	mvn(org.apache:apache:pom::)
# Literal, so the first rpmbuild -bs records them before sysjar is installed.
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildSystem:	maven
BuildOption(install):	--file-name commons-collections4 --link %{name}

%description
Apache Commons Collections 4.6.0 extends the Java Collections
Framework. It is a different artifact from Commons Collections 3.
This release adds SortedMultiSet and MultiSetUtils, and fixes
PassiveExpiringMap under synchronizedMap and the MapUtils typed
getters. Java 8 is required. Tests are skipped. The automatic module
name is org.apache.commons.collections4.

%prep
%autosetup -n commons-collections-rel-commons-collections-%{version}
# Test dependencies and the unused optional codec jar are not packaged
# for this build. The jar plugin is versionless, so its
# Automatic-Module-Name would be dropped. The Java 24 profile adds a
# snapshot plugin repository.
python - <<'PY'
import xml.etree.ElementTree as ET
from pathlib import Path

ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")
ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")

def local(tag):
    return tag.rsplit("}", 1)[-1]

path = Path("pom.xml")
tree = ET.parse(path)
root = tree.getroot()
removed = []
for parent in list(root.iter()):
    if local(parent.tag) != "dependencies":
        continue
    for child in list(parent):
        if local(child.tag) != "dependency":
            continue
        scope = artifact = ""
        for item in child:
            name = local(item.tag)
            if name == "scope":
                scope = (item.text or "").strip()
            elif name == "artifactId":
                artifact = (item.text or "").strip()
        if scope == "test" or artifact == "commons-codec":
            parent.remove(child)
            removed.append(artifact)
profiles = None
for child in list(root):
    if local(child.tag) == "profiles":
        profiles = child
if profiles is None:
    raise SystemExit("profiles missing")
dropped_profile = False
for profile in list(profiles):
    ident = ""
    for item in profile:
        if local(item.tag) == "id":
            ident = (item.text or "").strip()
    if ident == "java-24-up":
        profiles.remove(profile)
        dropped_profile = True
jar = None
for parent in root.iter():
    for child in list(parent):
        if local(child.tag) != "plugin":
            continue
        artifact = ""
        for item in child:
            if local(item.tag) == "artifactId":
                artifact = (item.text or "").strip()
        if artifact == "maven-jar-plugin":
            jar = child
if jar is None:
    raise SystemExit("jar plugin missing")
for item in list(jar):
    if local(item.tag) == "executions":
        jar.remove(item)
    if local(item.tag) == "version":
        raise SystemExit("jar plugin already versioned")
version = ET.Element(jar.tag.rsplit("}", 1)[0] + "}version" if "}" in jar.tag else "version")
version.text = "3.3.0"
jar.insert(0, version)
tree.write(path, encoding="UTF-8", xml_declaration=True)
text = path.read_text(encoding="utf-8")
if "commons-codec" in text or "java-24-up" in text or "<scope>test</scope>" in text:
    raise SystemExit("dependency rewrite failed: " + " ".join(removed))
if not dropped_profile or "<version>3.3.0</version>" not in text:
    raise SystemExit("plugin rewrite failed")
if "test-jar" in text or "Automatic-Module-Name" not in text:
    raise SystemExit("jar plugin rewrite failed")
PY

%build -a
java --module-path target/commons-collections4-%{version}.jar --describe-module org.apache.commons.collections4 | grep -q '^org.apache.commons.collections4'

%files -f .mfiles
%doc LICENSE.txt NOTICE.txt RELEASE-NOTES.txt README.md
