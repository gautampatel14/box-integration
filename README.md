## Getting started with Box Integration for splunk


### UCC Setup
---
1. Installation:

requirements.txt
```
splunk-add-on-ucc-framework==5.38.0
```

2. ucc init
```
ucc-gen init --addon-name "box_integration_for_splunk" --addon-display-name "Box Integration for Splunk" --addon-input-name box_input
```

(or)
clone the git repo.

3. ucc build
```
ucc-gen build --ta-version=1.0.0
```

4. create a soft link (optional)
```
ln -s <your splunk/etc/apps location>/box_integration_for_splunk/output/box_integration_for_splunk <your splunk/etc/apps/ location>
```