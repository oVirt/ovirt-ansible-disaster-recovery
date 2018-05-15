#!/usr/bin/python
from bcolors import bcolors
from ConfigParser import SafeConfigParser
import os.path
import shlex
import subprocess
import sys

from subprocess import call

INFO = bcolors.OKGREEN
INPUT = bcolors.OKGREEN
WARN = bcolors.WARNING
FAIL = bcolors.FAIL
END = bcolors.ENDC
PREFIX = "[Failback] "
PLAY_DEF = "../examples/dr_play.yml"


class FailBack():

    def run(self, conf_file, log_file):
        print("\n%s%sStart failback operation...%s"
              % (INFO,
                 PREFIX,
                 END))
        dr_tag = "fail_back"
        dr_clean_tag = "clean_engine"
        target_host, source_map, var_file, vault, ansible_play = \
            self._init_vars(conf_file)
        print("\n%s%starget_host: %s \n"
              "%ssource_map: %s \n"
              "%svar_file: %s \n"
              "%svault: %s \n"
              "%sansible_play: %s%s \n"
              % (INFO,
                  PREFIX,
                  target_host,
                  PREFIX,
                  source_map,
                  PREFIX,
                  var_file,
                  PREFIX,
                  vault,
                  PREFIX,
                  ansible_play,
                  END))

        cmd = []
        cmd.append("ansible-playbook")
        cmd.append(ansible_play)
        cmd.append("-t")
        cmd.append(dr_clean_tag)
        cmd.append("-e")
        cmd.append("@" + var_file)
        cmd.append("-e")
        cmd.append("@" + vault)
        cmd.append("-e")
        cmd.append(" dr_source_map=" + target_host)
        cmd.append("--vault-password-file")
        cmd.append("vault_secret.sh")
        cmd.append("-vvv")

        cmd_fb = []
        cmd_fb.append("ansible-playbook")
        cmd_fb.append(ansible_play)
        cmd_fb.append("-t")
        cmd_fb.append(dr_tag)
        cmd_fb.append("-e")
        cmd_fb.append("@" + var_file)
        cmd_fb.append("-e")
        cmd_fb.append("@" + vault)
        cmd_fb.append("-e")
        cmd_fb.append(" dr_target_host=" + target_host +
                      " dr_source_map=" + source_map)
        cmd_fb.append("--vault-password-file")
        cmd_fb.append("vault_secret.sh")
        cmd_fb.append("-vvv")

        # Setting vault password
        vault_pass = raw_input(
            INPUT + PREFIX + "Please enter the vault password: " + END)
        os.system("export vault_password=\"" + vault_pass + "\"")
        print("\n%s%sStarting cleanup process of setup '%s'"
              " for oVirt ansible disaster recovery%s"
              % (INFO,
                  PREFIX,
                  target_host,
                  END))
        with open(log_file, "w") as f:
            f.write("Executing cleanup command: %s" % ' '.join(map(str, cmd)))
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            for line in iter(proc.stdout.readline, ''):
                # TODO: since we dont want to have log and print the
                # progress in the stdout, we only filter the task names
                # We should find a better way to do so.
                if 'TASK [ovirt-ansible-disaster-recovery : ' in line:
                    sys.stdout.write("\n" + line + "\n")
                f.write(line)

            print("\n%s%sFinished cleanup of setup '%s'"
                  " for oVirt ansible disaster recovery%s"
                  % (INFO,
                      PREFIX,
                      source_map,
                      END))

            print("\n%s%sStarting fail-back process to setup '%s'"
                  " from setup '%s' for oVirt ansible disaster recovery"
                  % (INFO,
                      PREFIX,
                      target_host,
                      source_map))

            f.write("Executing command %s" % ' '.join(map(str, cmd_fb)))
            proc_fb = subprocess.Popen(cmd_fb,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            for line in iter(proc_fb.stdout.readline, ''):
                # TODO: since we dont want to have log and print the
                # progress in the stdout, we only filter the task names
                # We should find a better way to do so.
                if 'TASK [ovirt-ansible-disaster-recovery :' in line:
                    sys.stdout.write("\n" + line + "\n")
                if "[Failback Replication Sync]" in line:
                    sys.stdout.write("\n" + INPUT + line + END)
                f.write(line)

        call(["cat", "/tmp/report.log"])
        print("\n%s%sFinished failback operation"
              " for oVirt ansible disaster recovery%s"
              % (INFO,
                  PREFIX,
                  END))

    def _init_vars(self, conf_file):
        """ Declare constants """
        _SECTION = "failover_failback"
        _TARGET = "dr_target_host"
        _SOURCE = "dr_source_map"
        _VAULT = "vault"
        _VAR_FILE = "var_file"
        _ANSIBLE_PLAY = 'ansible_play'
        setups = ['primary', 'secondary']

        """ Declare varialbles """
        target_host, source_map, vault, var_file, ansible_play = \
            '', '', '', '', ''
        settings = SafeConfigParser()
        settings.read(conf_file)
        if _SECTION not in settings.sections():
            settings.add_section(_SECTION)
        if not settings.has_option(_SECTION, _TARGET):
            settings.set(_SECTION, _TARGET, '')
        if not settings.has_option(_SECTION, _SOURCE):
            settings.set(_SECTION, _SOURCE, '')
        if not settings.has_option(_SECTION, _VAULT):
            settings.set(_SECTION, _VAULT, '')
        if not settings.has_option(_SECTION, _VAR_FILE):
            settings.set(_SECTION, _VAR_FILE, '')
        if not settings.has_option(_SECTION, _ANSIBLE_PLAY):
            settings.set(_SECTION, _ANSIBLE_PLAY, '')
        # We fetch the source map as target host since in failback
        # we do the reverse operation.
        target_host = settings.get(_SECTION, _SOURCE,
                                   vars=DefaultOption(settings,
                                                      _SECTION,
                                                      source_map=None))
        # We fetch the target host as target the source mapping for failback
        # since we do the reverse operation.
        source_map = settings.get(_SECTION, _TARGET,
                                  vars=DefaultOption(settings,
                                                     _SECTION,
                                                     target_host=None))
        vault = settings.get(_SECTION, _VAULT,
                             vars=DefaultOption(settings,
                                                _SECTION,
                                                vault=None))
        var_file = settings.get(_SECTION, _VAR_FILE,
                                vars=DefaultOption(settings,
                                                   _SECTION,
                                                   var_file=None))
        ansible_play = settings.get(_SECTION, _ANSIBLE_PLAY,
                                    vars=DefaultOption(settings,
                                                       _SECTION,
                                                       ansible_play=None))
        while target_host not in setups:
            target_host = raw_input(
                INPUT + PREFIX + "The target setup was not defined. "
                "Please provide the setup which it is failback to "
                "(primary or secondary): " + END)
        while source_map not in setups:
            source_map = raw_input(
                INPUT + PREFIX + "The source mapping was not defined. "
                "Please provide the source mapping "
                "(primary or secondary): " + END)
        while not os.path.isfile(var_file):
            var_file = raw_input("%s%svar file mapping '%s' does not exist. "
                                 "Please provide a valid mapping var file: %s"
                                 % (INPUT,
                                    PREFIX,
                                    var_file,
                                    END))
        while not os.path.isfile(vault):
            vault = raw_input("%s%spassword file '%s' does not exist."
                              "Please provide a valid password file:%s "
                              % (INPUT,
                                 PREFIX,
                                 vault,
                                 END))
        while (not ansible_play) or (not os.path.isfile(ansible_play)):
            ansible_play = raw_input("%s%sansible play '%s' "
                                     "is not initialized. "
                                     "Please provide the ansible play file "
                                     "to generate the mapping var file "
                                     "with ('%s'):%s "
                                     % (INPUT,
                                        PREFIX,
                                        str(ansible_play),
                                        PLAY_DEF,
                                        END) or PLAY_DEF)
        return (target_host, source_map, var_file, vault, ansible_play)


class DefaultOption(dict):

    def __init__(self, config, section, **kv):
        self._config = config
        self._section = section
        dict.__init__(self, **kv)

    def items(self):
        _items = []
        for option in self:
            if not self._config.has_option(self._section, option):
                _items.append((option, self[option]))
            else:
                value_in_config = self._config.get(self._section, option)
                _items.append((option, value_in_config))
        return _items


if __name__ == "__main__":
    FailBack().run('dr.conf', '/var/log/ovirt-dr/ovirt-dr.log')
