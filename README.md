oVirt Disaster Recovery
=========

The `oVirt.disaster-recovery` role responsible to manage the disaster recovery scenarios in oVirt.

Requirements
------------

 * Ansible version 2.4 or higher
 * Python SDK version 4.2.1 or higher

Role Variables
--------------

| Name                    | Default value         |                                                     |
|-------------------------|-----------------------|-----------------------------------------------------|
| dr_ignore_error_clean   | False                 | Specify whether to ignore errors on clean engine setup.<br/>This is mainly being used to avoid failures when trying to move a storage domain to maintenance/detach it.      |
| dr_ignore_error_recover | True                  | Specify whether to ignore errors on recover.      |
| dr_partial_import       | True                  | Specify whether to use the partial import flag on VM/Template register.<br/>If True, VMs and Templates will be registered without any missing disks, if false VMs/Templates will fail to be registered in case some of their disks will be missing from any of the storage domains.      |
| dr_target_host          | primary               | Specify the default target host to be used in the ansible play.<br/> This hos indicates the target site which the recover process will bedone.      |
| dr_source_map           | secondary             | Specify the default source map to be used in the play.</br/> The source map indicates the key which is used to get the target value for each attribute which we want to register with the VM/Template.       |
| dr_reset_mac_pool       | True                  | If true, then once a VM will be registered, it will automatically reset the mac pool, if configured in the VM.        |

Dependencies
------------

No.

Example Playbook
----------------

```yaml
---
- name: Setup oVirt environment
  hosts: localhost
  connection: local
  vars_files:
     - ovirt_passwords.yml
     - disaster_recovery_vars.yml
  roles:
     - {role: oVirt.disaster-recovery}
```

Generate var file mapping [demo](https://youtu.be/s1-Hq_Mk1w8)<br/>
Fail over scenario [demo](https://youtu.be/mEOgH-Tk09c)

License
-------

Apache License 2.0

