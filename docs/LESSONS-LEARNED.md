# Lessons Learned aus dem Aufbau

Probleme, die beim Aufbau tatsächlich aufgetreten sind, und wie sie gelöst wurden.

## 1. Helm-Test-Pod von der eigenen NetworkPolicy blockiert
**Symptom:** `helm test` lief in einen Timeout (`curl: (28) Failed to connect`), obwohl Prometheus
die App aus dem Namespace `monitoring` problemlos scrapte.
**Analyse:** Ein Debug-Pod ohne App-Labels erreichte den Service *mit* aktiver NetworkPolicy. Der
Test-Pod trug jedoch die Selector-Labels der App (`app.kubernetes.io/name/instance`) und wurde damit
selbst von der Egress-Regel der App erfasst, die nur DNS und HTTPS erlaubt.
**Lösung:** Test-Pod bekommt eigene Labels. Nebeneffekt: Er kann nun auch nicht mehr versehentlich
als Endpoint des Services oder im PodDisruptionBudget landen.

## 2. kind-CLI zu alt für das Node-Image
**Symptom:** `kind load docker-image` → `unknown containerd config version: 4`.
**Ursache:** Das Node-Image `kindest/node:v1.36.4` nutzt eine neuere containerd-Konfiguration als die
Standard-kind-Version der GitHub Action.
**Lösung:** kind-Version in der Pipeline explizit auf v0.33.0 pinnen; Voraussetzung im README dokumentiert.

## 3. Zurückgezogene Action-Version nach Supply-Chain-Vorfall
**Symptom:** `Unable to resolve action aquasecurity/trivy-action@0.28.0`.
**Ursache:** Nach dem Kompromittierungsvorfall im Trivy-Ökosystem 2026 wurden alte Tags entfernt.
**Lösung:** Action auf v0.36.0 **per Commit-SHA** gepinnt – Tags sind veränderlich, SHAs nicht.

## 4. Schwachstellen im Basis-Image
**Symptom:** Trivy-Gate rot: zlib (Debian) sowie msgpack/urllib3/setuptools aus dem mitgelieferten pip.
**Lösung:** Debian-Sicherheitsupdates im Build einspielen und pip/setuptools aus dem
Laufzeit-Image entfernen, da sie dort nicht gebraucht werden.
