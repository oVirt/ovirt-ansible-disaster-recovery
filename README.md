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
| dr_target_host          | secondary             | Specify the default target host to be used in the ansible play.<br/> This host indicates the target site which the recover process will bedone.      |
| dr_source_map           | primary               | Specify the default source map to be used in the play.</br/> The source map indicates the key which is used to get the target value for each attribute which we want to register with the VM/Template.       |
| dr_reset_mac_pool       | True                  | If true, then once a VM will be registered, it will automatically reset the mac pool, if configured in the VM.        |
| dr_cleanup_retries_maintenance       | 3                  | Specify the number of retries of moving a storage domain to maintenace VM as part of a fail back scenario.       |
| dr_cleanup_delay_maintenance       | 120                  | Specify the number of seconds between each retry as part of a fail back scenario.       |
| dr_clean_orphaned_vms:       | True                  | Specify whether to remove any VMs which have no disks from the setup as part of cleanup.       |
| dr_clean_orphaned_disks:       | True                  | Specify whether to remove lun disks from the setup as part of engine setup.       |


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

